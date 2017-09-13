import radical.analytics as ra
import pprint

# A formatting helper before starting...
def ppheader(message):
    separator = '\n' + 78 * '-' + '\n'
    print separator + message + separator

if __name__ == '__main__':

    session = ra.Session(stype='radical.entk',src='/home/vivek/Research/repos/radical.entk-0.6/examples/analytics/raw_data/')

    pnames = session.list()
    ppheader("name of the properties of the session")
    pprint.pprint(pnames)

    # Each entity has at least four properties--etype, uid, state, and
    # event--and we can indipendently list one or more of these properties. The
    # following list the types of every entity in the session:
    etypes = session.list('etype')
    ppheader("name of the types of entity of the session")
    pprint.pprint(etypes)

    # The unique identifier of the entities (note that the identifier is
    # guaranteed to be unique within the scope of the given session. This means
    # that given two session, the same identifier may be used in both of them):
    ppheader("unique identifiers (uid) of all entities of the session")
    uids = session.list('uid')
    pprint.pprint(uids)

    # The name of the states of the entities:
    ppheader("unique names of the states of all entities of the session")
    states = session.list('state')
    pprint.pprint(states)

    # and the name of the events of the entities:
    ppheader("unique names of the events of all entities of the session")
    events = session.list('event')
    pprint.pprint(events)

    # Finally, when useful, we can list subset of properties by using a list
    # notation:
    ppheader("names of the types and states of entity of the session")
    etypes_states = session.list(['etype', 'state'])
    pprint.pprint(etypes_states)