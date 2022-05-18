# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Module for implementing heartbeat and checking statuses of KPI sources"""
import logging
import time

from threading import Thread, Event

from lifecycle_manager.config import services

settings = services.Settings()


class Heartbeat(Thread):
    """Heartbeat class"""
    def __init__(self, _id):
        super().__init__()
        self.id = _id
        self._stop = False
        self._stop_event = Event()

    def signal_stop(self):
        """Set _stop and stop event to True."""
        self._stop = True
        self._stop_event.set()

    def run(self):
        """Main logic for a heartbeat instance"""
        logging.info("Running Heartbeat instance.")
        while not self._stop:
            time.sleep(10)

    def _main_logic(self):
        """Wait until an event is set."""
        logging.info("Running Heartbeat instance.")
        while not self._stop_event:
            time.sleep(1)
