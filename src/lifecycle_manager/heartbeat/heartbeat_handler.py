# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Thread for handling Heartbeat instance"""
import logging
import time
from threading import Thread, Event
from lifecycle_manager.heartbeat.heartbeat import Heartbeat


class HeartbeatHandler(Thread):
    """ Heartbeat Handler class."""
    def __init__(self):
        super().__init__()
        self.heartbeat = Heartbeat(self)
        self._heartbeat_instances = []
        self._shutdown = False
        self._status = 'Idle'

    @property
    def status(self):
        """Getter for variable status."""
        return self._status

    @property
    def heartbeat_instances(self):
        """Getter for heartbeat instance list."""
        return self._heartbeat_instances

    def shutdown(self):
        """Set shutdown to True for stopping the thread."""
        self._shutdown = True

    def set_status(self):
        """Set the status variable of the Heartbeat Handler."""
        if self.heartbeat_instances:
            self._status = 'Heartbeat check(s) initiated'
        else:
            self._status = 'Idle'

    def create_heartbeat_instance(self, trial_id):
        """Call Heartbeat class to create Heartbeat instance."""
        logging.info("Creating Heartbeat instance with Trial ID: %s", trial_id)
        heartbeat_instance = Heartbeat(trial_id)
        self._heartbeat_instances.append(heartbeat_instance)
        heartbeat_instance.start()
        self.set_status()

    def run(self):
        """Run Heartbeat Handler main functionalities."""
        logging.info("Running Heartbeat Handler instance.")

        stop_event = Event()

        while True:
            time.sleep(1)

            if self._shutdown:
                logging.warning("Shutting down Heartbeat instance.")
                stop_event.set()
                self.heartbeat.signal_stop()
                self.heartbeat.join()
                break

        self.set_status()

    def stop_heartbeat_instance(self, trial_id):
        """Stop a Heartbeat instance."""
        logging.info("Stopping a Heartbeat with ID: %s)", str(trial_id))
        for instance in self._heartbeat_instances:
            if trial_id == instance.id:
                instance.signal_stop()
                self._heartbeat_instances.remove(instance)
                self.set_status()
