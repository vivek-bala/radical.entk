import radical.utils as ru
import os, json


def dump_session(workflow, AppManager, WFProcessor, ResourceManager, TaskManager):

    json_data = {}

    # Add RP session being used
    json_data['session'] = AppManager.uid

    # Create the tree!
    json_data['tree'] = dict()

    # Add ResourceManager to tree
    json_data['tree']['ResourceManager'] = {
        'cfg': {
            'session': ResourceManager.session.uid,
            'pmgr': ResourceManager.pmgr.uid,
            'pilot': ResourceManager.pilot.uid,
            'resource': ResourceManager.resource,
            'walltime': ResourceManager.walltime,
            'cores': ResourceManager.cores,
            'project': ResourceManager.project,
            'access_schema': ResourceManager.access_schema,
            'queue': ResourceManager.queue
        },

        'etype': 'ResourceManager',
        'uid': ResourceManager.uid,
        'children': [],
        'has': [],

        'description': {
            'session': ResourceManager.session.uid,
            'pmgr': ResourceManager.pmgr.uid,
            'pilot': ResourceManager.pilot.uid,
            'resource': ResourceManager.resource,
            'walltime': ResourceManager.walltime,
            'cores': ResourceManager.cores,
            'project': ResourceManager.project,
            'access_schema': ResourceManager.access_schema,
            'queue': ResourceManager.queue
        }
    }

    # Add AppManager to tree
    json_data['tree']['AppManager'] = {
        'cfg': {
            'hostname': AppManager.hostname,
            'port': AppManager.port,
            'push_threads': AppManager.num_push_threads,
            'pull_threads': AppManager.num_pull_threads,
            'sync_threads': AppManager.num_sync_threads,
            'pending_qs': AppManager.num_pending_qs,
            'completed_qs': AppManager.num_completed_qs,
            'reattempts': AppManager.reattempts,
            'autoterminate': AppManager.autoterminate
        },

        'etype': 'AppManager',
        'uid': AppManager.uid,
        'children': [],
        'has': ['Pipeline',
                'WFProcessor',
                'ResourceManager',
                'TaskManager'
                ],

        'description': {
            'hostname': AppManager.hostname,
            'port': AppManager.port,
            'push_threads': AppManager.num_push_threads,
            'pull_threads': AppManager.num_pull_threads,
            'sync_threads': AppManager.num_sync_threads,
            'pending_qs': AppManager.num_pending_qs,
            'completed_qs': AppManager.num_completed_qs,
            'reattempts': AppManager.reattempts,
            'autoterminate': AppManager.autoterminate
        }
    }

    for pipe in workflow:
        json_data['tree']['AppManager']['children'].append(pipe.uid)

    json_data['tree']['AppManager']['children'].append(WFProcessor.uid)
    json_data['tree']['AppManager']['children'].append(ResourceManager.uid)
    json_data['tree']['AppManager']['children'].append(TaskManager.uid)

    # Add WFProcessor to tree
    json_data['tree']['WFProcessor'] = {
        'cfg': {},

        'etype': 'WFProcessor',
        'uid': WFProcessor.uid,
        'children': [],
        'has': [],
        'description': {}
    }

    # Add TaskManager to tree
    json_data['tree']['TaskManager'] = {
        'cfg': {},
        'etype': 'TaskManager',
        'uid': TaskManager.uid,
        'children': [],
        'has': [],
        'description': {}
    }

    # Add Pipelines to tree
    for pipe in workflow:
        json_data['tree'][pipe.uid] = {
            'cfg': {
                'stage_count': len(pipe.stages),
                'state_history': pipe.state_history
            },
            'etype': 'Pipeline',
            'uid': pipe.uid,
            'children': [],
            'has': ['Stage'],
            'description': {
                'stage_count': len(pipe.stages),
                'state_history': pipe.state_history
            }
        }

        for stage in pipe.stages:
            json_data['tree'][pipe.uid]['children'].append(stage.uid)

            json_data['tree'][stage.uid] = {
                'cfg': {
                    'task_count': len(stage.tasks),
                    'state_history': stage.state_history,
                    'parent_pipeline': stage._parent_pipeline
                },
                'etype': 'Stage',
                'uid': stage.uid,
                'children': [],
                'has': ['Task'],
                'description': {
                    'task_count': len(stage.tasks),
                    'state_history': stage.state_history,
                    'parent_pipeline': stage._parent_pipeline
                }
            }

            for task in stage.tasks:
                json_data['tree'][stage.uid]['children'].append(task.uid)

                json_data['tree'][task.uid] = {
                    'cfg': {
                        'pre_exec': task.pre_exec,
                        'executable': task.executable,
                        'arguments': task.arguments,
                        'post_exec': task.post_exec,
                        'cores': task.cores,
                        'mpi': task.mpi,
                        'upload_input_data': task.upload_input_data,
                        'copy_input_data': task.copy_input_data,
                        'link_input_data': task.link_input_data,
                        'copy_output_data': task.copy_output_data,
                        'download_output_data': task.download_output_data,
                        'exit_code': task.exit_code,
                        'path': task.path,
                        'parent_stage': task._parent_stage,
                        'parent_pipeline': task._parent_pipeline,
                        'state_history': task.state_history
                    },
                    'etype': 'Task',
                    'uid': task.uid,
                    'children': [],
                    'has': [],
                    'description': {
                        'pre_exec': task.pre_exec,
                        'executable': task.executable,
                        'arguments': task.arguments,
                        'post_exec': task.post_exec,
                        'cores': task.cores,
                        'mpi': task.mpi,
                        'upload_input_data': task.upload_input_data,
                        'copy_input_data': task.copy_input_data,
                        'link_input_data': task.link_input_data,
                        'copy_output_data': task.copy_output_data,
                        'download_output_data': task.download_output_data,
                        'exit_code': task.exit_code,
                        'path': task.path,
                        'parent_stage': task._parent_stage,
                        'parent_pipeline': task._parent_pipeline,
                        'state_history': task.state_history
                    }
                }


    ru.write_json(json_data,'%s/%s.json' % (os.getcwd(), AppManager.uid))
