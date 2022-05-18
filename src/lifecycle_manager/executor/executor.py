# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Executor thread (state machine)."""
import logging
import importlib
import os
from threading import Thread, Event

from lifecycle_manager.utils.any_event import AnyEvent


class UnhandledException(Exception):
    """Raised when thread runs into a unhandled issue."""


class UnfinishedExecution(Exception):
    """Raised when thread exits wihtout finished flag set."""


class OutOfRetries(Exception):
    """Raised when thread runs into a unhandled issue."""


class Executor(Thread):
    """State machine thread."""

    def __init__(self, engine, _id, services, restore_dict=None):
        super().__init__()
        self.engine = engine
        self._states = None
        self._create_states()
        self.id = _id
        self.services = services
        self._trial_info = {"trialID": _id}
        self._run_params = {'current_state': 'GetCallbackToken', 'wanted_state': None,
                            'retries': 0, 'state_lock': False, 'finished': False, 'kpi_status': None,
                            'status': 'Stopped', 'token': None, 'slice_created': False}
        self._responses = {}
        self._shutdown = False
        self.events = self._create_events()
        if restore_dict is not None:
            self._restore(restore_dict)

    @property
    def _stop_event(self):
        return self.events['stop']

    @property
    def _run_event(self):
        return self.events['run']

    @property
    def _fail_event(self):
        return self.events['fail']

    @property
    def _state_event(self):
        return self.events['state']

    @property
    def _any_event(self):
        return self.events['any']

    @property
    def get_trial_information(self):
        """Get parameter."""
        return self._trial_info

    @property
    def get_kpi_status(self):
        """Get parameter"""
        return self._run_params['kpi_status']

    @property
    def get_slice_created(self):
        """Get parameter"""
        return self._run_params['slice_created']

    @property
    def get_status(self):
        """Get parameter."""
        return self._run_params['status']

    @property
    def get_responses(self):
        """Get responses."""
        return self._responses

    @property
    def get_current_state(self):
        """Get parameter."""
        return self._run_params['current_state']

    @property
    def get_id(self):
        """Get parameter"""
        return str(self.id)

    @property
    def get_token(self):
        """Get token"""
        return self._run_params['token']

    def set_slice_created(self):
        """Set slice_created flag"""
        self._run_params['slice_created'] = True

    def set_kpi_status(self, status):
        """Set kpi_status"""
        self._run_params['kpi_status'] = status

    def set_token(self, token):
        """Set token"""
        self._run_params['token'] = token

    def set_status(self, _status):
        """Set parameter."""
        self._run_params['status'] = _status

    def _set_current_state(self, state):
        """Set parameter."""
        self._run_params['current_state'] = state

    def _get_wanted_state(self):
        """Get parameter."""
        return self._run_params['wanted_state']

    def _set_wanted_state(self, state):
        """Set parameter."""
        self._run_params['wanted_state'] = state

    def _get_retries(self):
        """Get parameter."""
        return self._run_params['retries']

    def _set_retries(self, retries):
        """Set parameter."""
        self._run_params['retries'] = retries

    def _set_finished(self):
        """Set parameter."""
        self._run_params['finished'] = True

    def _get_finished(self):
        """Get parameter."""
        return self._run_params['finished']

    def _get_spinlock(self):
        """get current lock state."""
        return self._run_params['state_lock']

    def _spin_state_lock(self):
        """Lock and unlock."""
        if self._run_params['state_lock']:
            self._run_params['state_lock'] = False
        else:
            self._run_params['state_lock'] = True

    def set_stop_event(self):
        """Interface for other threads to set stop event."""
        self._stop_event.set()

    def set_run_event(self):
        """Interface for other threads to set collect event."""
        self._run_event.set()

    def set_fail_event(self):
        """Interface for other threads to set collect event."""
        self._fail_event.set()

    def set_state_event(self):
        """Interface for other threads to set collect event."""
        self._state_event.set()

    @staticmethod
    def _create_events():
        """Create instances of needed events."""
        stop_event = Event()
        run_event = Event()
        fail_event = Event()
        state_event = Event()
        any_event = AnyEvent(stop_event, run_event, state_event, fail_event)
        return {"stop": stop_event, "run": run_event, "fail": fail_event, "state": state_event, "any": any_event}

    def set_state(self, _state):
        """Interface for other threads to set next state for the state machine."""
        self._run_params['wanted'] = _state
        if self.is_alive() and self.get_status == 'Waiting':
            logging.getLogger('__executor__').debug('Setting next state to: %s', _state)
            self.set_state_event()
            return 0
        logging.getLogger('__executor__').debug('Executor is not ready for state change.')
        return 1

    def set_state_force(self, _state):
        """Interface for other threads to set next state for the state machine."""
        self._run_params['wanted'] = _state
        if self.is_alive():
            logging.getLogger('__executor__').debug('Setting next state to: %s', _state)
            self.set_state_event()
            return 0
        logging.getLogger('__executor__').debug('Executor is not alive.')
        return 1

    def _create_states(self, statelist=None):
        """Create states and return a dict of instantiated objects."""
        _dict = {}
        if statelist is None:
            statelist = ['GetCallbackToken', 'RemoveCallbackToken', 'GetTrialInfo', 'Waiting',
                         'SliceDeployment', 'UpdateDeploymentSlice', 'CloudVnfOnboarding',
                         'UpdateCloudVnfBoardingStatus', 'CloudVnfDeployment',
                         'UpdateCloudVnfDeploymentStatus', 'EdgeVnfOnboarding', 'UpdateEdgeVnfBoardingStatus',
                         'EdgeVnfDeployment', 'UpdateEdgeVnfDeploymentStatus', 'Start5GresourceTesting',
                         'EnforceUavPlan', 'UpdateUavPlanStatus', 'CreateMeasurementJob',
                         'UpdateStatusIdle', 'SendKpiIdle', 'UpdateStatusActive', 'SendKpiActive',
                         'UpdateStatusStopping', 'SendKpiFinish', 'DeleteMeasurementJob',
                         'CloseService', 'UpdateStatusFinish', 'Finish', 'Fail']
        for state in statelist:
            _state = getattr(importlib.import_module("lifecycle_manager.executor.states"), state)
            _dict[state] = _state()
        self._states = _dict

    def add_response(self, endpoint, status_code):
        """Add response to collection."""
        response = {"status_code": status_code}
        self._responses[endpoint] = response

    def update_trial_info(self, _dict):
        """Update values to trial_info."""
        for key in _dict:
            if key not in self._trial_info:
                self._trial_info[key] = _dict[key]

    def update_dict_in_info(self, info_key, _dict):
        """Update values to trial_info."""
        if info_key in self._trial_info:
            temp = self._trial_info[info_key]
            for key in _dict:
                temp[key] = _dict[key]
            self._trial_info[info_key] = temp

    def update_list_in_info(self, info_key, _list):
        """Update the whole list element."""
        if info_key in self._trial_info:
            self._trial_info[info_key] = _list

    def add_to_list_in_info(self, info_key, _list):
        """Add to a list element."""
        if info_key in self._trial_info:
            temp = self._trial_info[info_key]
            for item in _list:
                temp.append(item)
            self._trial_info[info_key] = temp

    def run(self):
        """Start executor routine."""
        logging.getLogger('__executor__').warning('%s Hello', self.name)
        self.set_run_event()
        try:
            self._main_logic()
        except UnfinishedExecution:
            logging.getLogger('__executor__').warning('%s Stopped before finish flag set.', self.name)

    def _backup(self):
        """Get current status of needed variables and save them to engine thread."""
        logging.getLogger('__executor__').warning("Backing up current state of executor")
        backup = {}
        for item in vars(self):
            if item in ['_trial_info', '_run_params', '_responses']:
                backup[str(item)] = vars(self)[item]
        self.engine.backup = backup

    def _restore(self, restore_dict):
        """Restore backed up variables to current instance."""
        logging.getLogger('__executor__').info("Restoring from backup")
        for item in restore_dict:
            setattr(self, item, restore_dict[item])
        logging.getLogger('__executor__').debug("Restoring complete.")

    def _main_logic(self):
        """Wait until an event is set."""
        while self._any_event.wait():
            if self._stop_event.is_set():
                self._handle_stop_event()
                break

            if self._fail_event.is_set():
                self._fail_event.clear()
                self._handle_fail_event()

            if self._state_event.is_set():
                self._state_event.clear()
                self._handle_state_event()

            if self._run_event.is_set():
                self._run_event.clear()
                self._handle_run_event()

    def _handle_state_event(self):
        """Set next state."""
        try:
            logging.getLogger('__executor__').debug('Set next is: %s', self._run_params['wanted'])
            if self._run_params['wanted'] in str(self._states):
                self._run_params['current_state'] = self._run_params['wanted']
                self._run_params['wanted'] = None
                self.set_status('Running')
                self._spin_state_lock()
                self.set_run_event()
            else:
                logging.getLogger('__executor__').error("Requested state doesn't exist.")
        except Exception:
            logging.getLogger('__executor__').error("Processing state change failed.")

    def _handle_fail_event(self):
        """Handle failure state."""
        retries = self._get_retries()
        if retries > 0:
            self._set_retries(retries - 1)
            self.set_run_event()
        else:
            self._backup()
            try:
                result, _next = self._states['Fail'].run(self)
            except Exception:
                logging.getLogger('__executor__').warning("%s", "Couldn't update repository status to failed." +
                                                          "Probably connection issue or testing.")
            try:
                os.mkdir("logs")
            except FileExistsError:
                logging.getLogger('__executor__').info("log folder seems to already exist.")
            except Exception:
                logging.getLogger('__executor__').error("")
            log = open('logs/executor_' + self.id + '_fail.log', 'w')
            log.write("PARAMETERS: " + str(self._run_params) + "\n" + "RESPONSES: " + str(self._responses))
            log.close()
        self.engine.set_failed()
        self._stop_event.set()

    def _handle_stop_event(self):
        """Stop this instance."""
        logging.getLogger('__executor__').info("Stopping executor.")
        self.set_status('Stopped')
        if self._get_finished():
            self.engine.set_finished()
            self.engine.set_stop_event()
        else:
            raise UnfinishedExecution

    def _handle_run_event(self):
        """Run one state."""
        try:
            current_state = self.get_current_state
            if self._get_spinlock():
                self._spin_state_lock()
            self.set_status('Running')
            logging.getLogger('__executor__').debug('Running: %s in: %s', str(self.get_current_state), self.name)
            if current_state == 'Waiting':
                self.set_status('Waiting')
                logging.getLogger('__executor__').debug("Waiting for signal")
            else:
                result, _next = self._states[current_state].run(self)
                if result != 0:
                    self.set_fail_event()
                else:
                    if current_state == "Finish":
                        self._set_finished()
                        self.set_stop_event()
                    else:
                        self._set_retries(0)
                        if not self._get_spinlock():
                            self._set_current_state(_next)
                            self.set_run_event()
        except Exception as _err:
            logging.getLogger('__executor__').debug("Error: %s", _err)
            self.set_fail_event()
