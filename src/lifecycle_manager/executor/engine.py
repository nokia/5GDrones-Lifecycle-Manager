# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0


"""Handler thread for executor a executor instance."""
import logging
import time
from threading import Thread, Event

from lifecycle_manager.executor.executor import Executor
from lifecycle_manager.executor.executor import UnhandledException
from lifecycle_manager.utils.any_event import AnyEvent


class Engine(Thread):
    """Thread to handle one executor instance. Provides functions to communicate to """
    def __init__(self, _id, services):
        super().__init__()
        self.id = _id
        self.services = services
        self.executor = Executor(self, _id, services)
        self.process_check_thread = Thread(target=self.is_process_alive, args=[Event()])
        self.events = self._create_events()
        self.backup = None
        self._shutdown = False
        self._failed = False
        self._finished = False

    @property
    def failed(self):
        """Getter for parameter self._failed."""
        return self._failed

    @property
    def finished(self):
        """Getter for parameter self._finished."""
        return self._finished

    @property
    def _stop_event(self):
        return self.events["stop"]

    @property
    def _execute_event(self):
        return self.events["execute"]

    @property
    def _any_event(self):
        return self.events["any"]

    def set_failed(self):
        """Set self._failed state to True"""
        self._failed = True

    def set_finished(self):
        """Set self._finished state to True"""
        self._finished = True

    def set_stop_event(self):
        """Interface for other threads to set stop event."""
        self._stop_event.set()

    def set_execute_event(self):
        """Interface for other threads to set execute event."""
        self._execute_event.set()

    @staticmethod
    def _create_events():
        """Create instances of needed events."""
        stop_event = Event()
        execute_event = Event()
        fail_event = Event()
        any_event = AnyEvent(stop_event, execute_event, fail_event)
        return {"stop": stop_event, "execute": execute_event, "fail": fail_event, "any": any_event}

    def get_executor_responses(self):
        """Return executor responses."""
        return self.executor.get_responses

    def get_executor_status(self):
        """Get the current state of the executor class."""
        return self.executor.get_status

    def get_executor_state(self):
        """Get the current state of the executor class."""
        return self.executor.get_current_state

    def set_executor_state(self, state):
        """Set state for the executor class. Return True if successful."""
        if self.executor.set_state(state) == 0:
            return True
        return False

    def set_executor_state_force(self, state):
        """Set state for the executor class. Return True if successful."""
        if self.executor.set_state_force(state) == 0:
            return True
        return False

    def run(self):
        """Run this thread."""
        logging.getLogger('__executor__').info("Handler running...")
        self._wait_and_handle_events()

    def restore(self):
        """Create a new executor object and restore the state from previous backup."""
        logging.getLogger('__executor__').debug("Restoring executor status")
        self.executor = Executor(self, '', self.services, self.backup)
        self._failed = False
        self.set_execute_event()

    def _wait_and_handle_events(self):
        """Wait until an event is set."""
        try:
            while self._any_event.wait():
                if self._stop_event.is_set():
                    self._handle_stop_event()
                    break

                if self._execute_event.is_set():
                    self._execute_event.clear()
                    self._handle_execute_event()
        except Exception as _err:
            logging.getLogger('__executor__').error(str(_err))
            raise UnhandledException() from _err

    def _handle_fail_event(self):
        """Stop executor and check thread and restore."""
        logging.getLogger('__executor__').error("Executor failed!")
        if self.executor.is_alive():
            self.executor.set_stop_event()
            self.executor.join()
        if self.process_check_thread.is_alive():
            self.process_check_thread.join()
        self._failed = True

    def _handle_execute_event(self):
        """Start executor and process check thread."""
        self.executor.start()
        self.process_check_thread = Thread(target=self.is_process_alive, args=[Event()])
        self.process_check_thread.start()

    def _handle_stop_event(self):
        """Stop executor and check thread."""
        logging.getLogger('__executor__').info("Stopping executor if still alive.")
        if self.executor.is_alive():
            self.executor.set_stop_event()
            self.executor.join()
        if self.process_check_thread.is_alive():
            self.process_check_thread.join()

    def is_process_alive(self, stop_event):
        """Check that executor processes are alive."""
        logging.getLogger('__executor__').info("Process check thread started")
        while not stop_event.is_set():
            time.sleep(1)
            if not self.executor.is_alive():
                logging.getLogger('__executor__').info("CheckThread: Executor process is NOT alive.")
                stop_event.set()
