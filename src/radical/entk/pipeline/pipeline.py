import radical.utils as ru
from radical.entk.exceptions import *
from radical.entk.stage.stage import Stage
import threading
from radical.entk import states


class Pipeline(object):

    def __init__(self, name, resource=None):

        self._uid       = ru.generate_id('radical.entk.pipeline')
        self._stages    = list()
        self._name      = name
        self._resource  = resource

        self._state     = states.NEW

        # To keep track of current state
        self._stage_count = len(self._stages)
        self._current_stage = 1

        # Lock around current stage
        self._stage_lock = threading.Lock()

        # To keep track of termination of pipeline
        self._completed_flag = threading.Event()


    def validate_stages(self, stages):

        if not isinstance(stages, list):
            stages = [stages]

        for val in stages:
            if not isinstance(val, Stage):
                raise TypeError(expected_type=Stage, actual_type=type(val))

        return stages
    # -----------------------------------------------
    # Getter functions
    # -----------------------------------------------

    @property
    def name(self):
        return self._name
    
    @property
    def stages(self):
        return self._stages

    @property
    def state(self):
        return self._state
    
    @property
    def resource(self):
        return self._resource

    @property
    def stage_lock(self):
        return self._stage_lock
    
    @property
    def completed(self):
        return self._completed_flag.is_set()

    @property
    def current_stage(self):
        return self._current_stage
    
    @property
    def uid(self):
        return self._uid
    
    # -----------------------------------------------


    # -----------------------------------------------
    # Setter functions
    # -----------------------------------------------

    @stages.setter
    def stages(self, stages):

        self._stages = self.validate_stages(stages)
        self.pass_uid()
        self._stage_count = len(self._stages)
    

    @resource.setter
    def resource(self, value):
        self._resource = value

    # -----------------------------------------------

    def add_stages(self, stages):

        stages = self.validate_stages(stages)
        stages = self.pass_uid(stages)
        self._stages.extend(stages)
        self._stage_count = len(self._stages)


    def remove_stages(self, stage_names):

        if not isinstance(stage_names, list):
            stage_names = [stage_names]

        copy_of_existing_stages = self._stages
        copy_stage_names = stage_names

        for stage in self._stages:

            for stage_name in stage_names:
                
                if stage.name ==  stage_name:

                    copy_of_existing_stages.remove(stage)
                    copy_stage_names.remove(stage)

            stage_names = copy_stage_names

        self._stages = copy_of_existing_stages
        self._stage_count = len(self._stages)

    def pass_uid(self, stages=None):

        if stages is None:
            for stage in self._stages:
                stage.parent_pipeline = self._uid
                stage.pass_uid()
        else:
            for stage in stages:
                stage.parent_pipeline = self._uid
                stage.pass_uid()

            return stages


    def increment_stage(self):

        if self._current_stage < self._stage_count:
            self._current_stage+=1
        else:
            self._completed_flag.set()