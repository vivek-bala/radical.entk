import os
import csv
import copy
import glob
import time
import threading

import radical.utils as ru

from radical.entk.exceptions import *
import traceback
import socket

# ------------------------------------------------------------------------------
#


def read_profiles(profiles):
    """
    We read all profiles as CSV files and parse them.  For each profile,
    we back-calculate global time (epoch) from the synch timestamps.
    """
    ret = dict()
    fields = ru.Profiler.fields

    for prof in profiles:
        rows = list()
        with open(prof, 'r') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=fields)
            for row in reader:

                # skip header
                if row['time'].startswith('#'):
                    continue

                row['time'] = float(row['time'])

                # store row in profile
                rows.append(row)

        ret[prof] = rows

    return ret


# ------------------------------------------------------------------------------
#
def combine_profiles(profs):
    """
    We merge all profiles and sorted by time.
    This routine expectes all profiles to have a synchronization time stamp.
    Two kinds of sync timestamps are supported: absolute and relative.
    Time syncing is done based on 'sync abs' timestamps, which we expect one to
    be available per host (the first profile entry will contain host
    information).  All timestamps from the same host will be corrected by the
    respectively determined ntp offset.  We define an 'accuracy' measure which
    is the maximum difference of clock correction offsets across all hosts.
    The method returnes the combined profile and accuracy, as tuple.
    """

    # we abuse the profile combination to also derive a pilot-host map, which
    # will tell us on what exact host each pilot has been running.  To do so, we
    # check for the PMGR_ACTIVE advance event in agent_0.prof, and use the NTP
    # sync info to associate a hostname.
    # FIXME: This should be replaced by proper hostname logging in
    #        in `pilot.resource_details`.

    pd_rel = dict()  # profiles which have relative time refs
    hostmap = dict()  # map pilot IDs to host names

    t_host = dict()  # time offset per host
    p_glob = list()  # global profile
    t_min = None   # absolute starting point of prof session
    c_qed = 0      # counter for profile closing tag
    accuracy = 0      # max uncorrected clock deviation

    for pname, prof in profs.iteritems():

        if not len(prof):
          # print 'empty profile %s' % pname
            continue

        if not prof[0]['msg']:
            # FIXME: https://github.com/radical-cybertools/radical.analytics/issues/20
          # print 'unsynced profile %s' % pname
            continue

        t_prof = prof[0]['time']

        host, ip, t_sys, t_ntp, t_mode = prof[0]['msg'].split(':')
        host_id = '%s:%s' % (host, ip)

        if t_min:
            t_min = min(t_min, t_prof)
        else:
            t_min = t_prof

        if t_mode == 'sys':
          # print 'sys synced profile (%s)' % t_mode
            continue

        # determine the correction for the given host
        t_sys = float(t_sys)
        t_ntp = float(t_ntp)
        t_off = t_sys - t_ntp

        if host_id in t_host:

            accuracy = max(accuracy, t_off - t_host[host_id])

            if abs(t_off - t_host[host_id]) > NTP_DIFF_WARN_LIMIT:
                print 'conflict sync   %-35s (%-35s) %6.1f : %6.1f :  %12.5f' \
                    % (os.path.basename(pname), host_id, t_off, t_host[host_id], (t_off - t_host[host_id]))

            continue  # we always use the first match

      # print 'store time sync %-35s (%-35s) %6.1f' \
      #         % (os.path.basename(pname), host_id, t_off)

    unsynced = set()
    for pname, prof in profs.iteritems():

        if not len(prof):
            continue

        if not prof[0]['msg']:
            continue

        host, ip, _, _, _ = prof[0]['msg'].split(':')
        host_id = '%s:%s' % (host, ip)
      # print ' --> pname: %s [%s] : %s' % (pname, host_id, bool(host_id in t_host))
        if host_id in t_host:
            t_off = t_host[host_id]
        else:
            unsynced.add(host_id)
            t_off = 0.0

        t_0 = prof[0]['time']
        t_0 -= t_min

      # print 'correct %12.2f : %12.2f for %-30s : %-15s' % (t_min, t_off, host, pname)

        # correct profile timestamps
        for row in prof:

            t_orig = row['time']

            row['time'] -= t_min
            row['time'] -= t_off

            # count closing entries
            if row['event'] == 'QED':
                c_qed += 1

            if 'agent_0.prof' in pname    and \
                    row['event'] == 'advance' and \
                    row['state'] == rps.PMGR_ACTIVE:
                hostmap[row['uid']] = host_id

          # if row['event'] == 'advance' and row['uid'] == os.environ.get('FILTER'):
          #     print "~~~ ", row

        # add profile to global one
        p_glob += prof

      # # Check for proper closure of profiling files
      # if c_qed == 0:
      #     print 'WARNING: profile "%s" not correctly closed.' % prof
      # if c_qed > 1:
      #     print 'WARNING: profile "%s" closed %d times.' % (prof, c_qed)

    # sort by time and return
    p_glob = sorted(p_glob[:], key=lambda k: k['time'])

  # for event in p_glob:
  #     if event['event'] == 'advance' and event['uid'] == os.environ.get('FILTER'):
  #         print '#=- ', event

  # if unsynced:
  #     # FIXME: https://github.com/radical-cybertools/radical.analytics/issues/20
  #     # print 'unsynced hosts: %s' % list(unsynced)
  #     pass

    return [p_glob, accuracy, hostmap]


# ------------------------------------------------------------------------------
#
def clean_profile(profile, sid):
    """
    This method will prepare a profile for consumption in radical.analytics.  It
    performs the following actions:
      - makes sure all events have a `ename` entry
      - remove all state transitions to `CANCELLED` if a different final state 
        is encountered for the same uid
      - assignes the session uid to all events without uid
      - makes sure that state transitions have an `ename` set to `state`
    """

    entities = dict()  # things which have a uid

    for event in profile:

        uid = event['uid']
        state = event['state']
        time = event['time']
        name = event['event']

        del(event['event'])

        # we derive entity_type from the uid -- but funnel
        # some cases into the session
        if uid:
            event['entity_type'] = uid.split('.', 1)[0]

        elif uid == 'root':
            event['entity_type'] = 'session'
            event['uid'] = sid
            uid = sid

        else:
            event['entity_type'] = 'session'
            event['uid'] = sid
            uid = sid

        if uid not in entities:
            entities[uid] = dict()
            entities[uid]['states'] = dict()
            entities[uid]['events'] = list()

        if name == 'advance':

            # this is a state progression
            assert(state), 'cannot advance w/o state'
            assert(uid),   'cannot advance w/o uid'

            event['event_type'] = 'state'
            skip = False

            if state in rps.FINAL:

                # a final state will cancel any previoud CANCELED state
                if rps.CANCELED in entities[uid]['states']:
                    del (entities[uid]['states'][rps.CANCELED])

                # vice-versa, we will not add CANCELED if a final
                # state already exists:
                if state == rps.CANCELED:
                    if any([s in entities[uid]['states']
                            for s in rps.FINAL]):
                        skip = True
                        continue

            if state in entities[uid]['states']:
                # ignore duplicated recordings of state transitions
                skip = True
                continue
              # raise ValueError('double state (%s) for %s' % (state, uid))

            if not skip:
                entities[uid]['states'][state] = event

        else:
            # FIXME: define different event types (we have that somewhere)
            event['event_type'] = 'event'
            entities[uid]['events'].append(event)

    # we have evaluated, cleaned and sorted all events -- now we recreate
    # a clean profile out of them
    ret = list()
    for uid, entity in entities.iteritems():

        ret += entity['events']
        for state, event in entity['states'].iteritems():
            ret.append(event)

    # sort by time and return
    ret = sorted(ret[:], key=lambda k: k['time'])

    return ret


def get_profile(src=None):

    if not src:
        src = "%s/%s" % (os.getcwd())

    if os.path.exists(src):

        # EnTK profiles are always on localhost
        profiles = glob.glob("%s/*.prof" % src)

    else:
        raise Error(text='%s does not exist' % src)

    if len(profiles) == 0:
        raise Error(text='No profiles found at %s' % src)

    try:

        profiles = read_profiles(profiles)
        prof, acc, hostmap = combine_profiles(profiles)

        hostmap = dict()

        prof = clean_profile(prof, sid='radical.entk')

        return prof, acc, hostmap

    except Exception as ex:

        # Push the exception raised by child functions
        print traceback.format_exc()
        raise Error(text=ex)


def create_entities(json_data):

    # Create entities
    json_data['entities'] = dict()

    # Create AppManager
    json_data['entities']['AppManager'] = {
        'event_model': None,
        'state_model': None,
        'state_values': None
    }

    # Create WFProcessor
    json_data['entities']['WFProcessor'] = {
        'event_model': None,
        'state_model': None,
        'state_values': None
    }

    # Create ResourceManager
    json_data['entities']['ResourceManager'] = {
        'event_model': None,
        'state_model': None,
        'state_values': None
    }

    # Create TaskManager
    json_data['entities']['TaskManager'] = {
        'event_model': None,
        'state_model': None,
        'state_values': None
    }

    # Create Pipeline
    json_data['entities']['Pipeline'] = {
        'event_model': None,
        'state_model': {
            'DESCRIBED': 1,
            'SCHEDULING': 2,
            'DONE': 11,
            'FAILED': 11,
            'CANCELED': 11
        },
        'state_values': {
            1: 'DESCRIBED',
            2: 'SCHEDULING',
            11: 'DONE',
            11: 'FAILED',
            11: 'CANCELED'
        }
    }

    # Create Stage
    json_data['entities']['Stage'] = {
        'event_model': None,
        'state_model': {
            'DESCRIBED': 1,
            'SCHEDULING': 2,
            'SCHEDULED': 3,
            'DONE': 11,
            'FAILED': 11,
            'CANCELED': 11
        },
        'state_values': {
            1: 'DESCRIBED',
            2: 'SCHEDULING',
            3: 'SCHEDULED',
            11: 'DONE',
            11: 'FAILED',
            11: 'CANCELED'
        }
    }

    # Create Task
    json_data['entities']['Task'] = {
        'event_model': None,
        'state_model': {
            'DESCRIBED': 1,
            'SCHEDULING': 2,
            'SCHEDULED': 3,
            'SUBMITTING': 4,
            'SUBMITTED': 5,
            'COMPLETED': 6,
            'DEQUEUEING': 7,
            'DEQUEUED': 8,
            'SYNCHRONIZING': 9,
            'SYNCHRONIZED': 10,
            'DONE': 11,
            'FAILED': 11,
            'CANCELED': 11
        },
        'state_values': {
            1: 'DESCRIBED',
            2: 'SCHEDULING',
            3: 'SCHEDULED',
            4: 'SUBMITTING',
            5: 'SUBMITTED',
            6: 'COMPLETED',
            7: 'DEQUEUEING',
            8: 'DEQUEUED',
            9: 'SYNCHRONIZING',
            10: 'SYNCHRONIZED',
            11: 'DONE',
            11: 'FAILED',
            11: 'CANCELED'
        }
    }

    return json_data


def get_description(src=None):

    if not src:
        src = "%s/%s" % (os.getcwd())

    if os.path.exists(src):
        json_file = list()
        # EnTK profiles are always on localhost
        json_file.extend(glob.glob("%s/App*.json" % src))
        json_file.extend(glob.glob("%s/../App*.json" % src))

    else:
        raise Error(text='%s does not exist' % src)

    if len(json_file) == 0:
        raise Error(text='No profiles found at %s' % src)
    elif len(json_file) > 1:
        raise Error(text='More than one json file found at %s' % src)

    json_file = json_file[0]

    try:

        json_data = ru.read_json(json_file)

        # Add entities
        json_data = create_entities(json_data)

        return json_data

    except Exception as ex:

        # Push the exception raised by child functions
        print traceback.format_exc()
        raise Error(text=ex)
