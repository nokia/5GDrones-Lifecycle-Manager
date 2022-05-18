# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Module for running Scheduler."""
import logging

from apscheduler.jobstores.base import ConflictingIdError

from lifecycle_manager.scheduler.scheduler_handler import SchedulerHandler
from lifecycle_manager.heartbeat.heartbeat_handler import HeartbeatHandler


class RunScheduler:
    """Class for functionalities related to running Scheduler."""
    def __init__(self):
        self.scheduler_handler = SchedulerHandler()
        self.heartbeat_handler = HeartbeatHandler()

    @staticmethod
    def set_logging():
        """Initialize logging."""
        formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s',
                                      datefmt="%Y-%m-%dT%H:%M:%S%z")
        logger = logging.getLogger()

        if logger.hasHandlers():
            logger.handlers.clear()

        logger.setLevel(logging.WARNING)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.WARNING)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    def setup_scheduler_handler(self):
        """Create Scheduler Handler instance."""
        logging.info("Creating Scheduler Handler instance.")
        self.scheduler_handler.start()

    def stop_scheduler(self):
        """Stop Scheduler Handler thread. Stops the whole LCM instance."""
        # TBD

    def get_status(self):
        """Return the status variable of the Scheduler Handler instance."""
        return self.scheduler_handler.status

    def get_automatic_scheduling(self):
        """Return boolen from handler."""
        return self.scheduler_handler.automatic_scheduling

    def toggle_automatic_scheduling(self):
        """Return boolen from handler."""
        return self.scheduler_handler.toggle_automatic_scheduling()

    def get_scheduled_jobs(self):
        """Return a list of scheduled jobs in Internal Scheduler."""
        return self.scheduler_handler.internal_scheduler.get_scheduled_jobs_pretty()

    def get_executor_engine_instance_statuses(self):
        """Return a list of running Executor Engine instance ids and statuses."""
        return self.scheduler_handler.engine_instance_statuses

    def get_executor_engine_instances(self):
        """Return a list of running Executor Engine instances."""
        return self.scheduler_handler.engine_instances

    def fetch_all_trials(self):
        """Interface for querying all trials from Trial registry."""
        success, message = self.scheduler_handler.fetch_all_trials()
        return success, message

    def fetch_trial(self, trial_id):
        """Interface for querying a trial based on trial ID from Trial registry."""
        success, message = self.scheduler_handler.fetch_trial(trial_id=trial_id)
        return success, message

    def add_new_job(self, start_time_utc, trial_id):
        """Interface for adding a new job to Scheduler."""
        try:
            self.scheduler_handler.internal_scheduler.add_scheduled_job(start_date=start_time_utc,
                                                                        trial_id=trial_id)
            return True
        except ConflictingIdError:
            return False

    def remove_job(self, trial_id):
        """Interface for removing a job from Scheduler."""
        if self.scheduler_handler.internal_scheduler.remove_job(trial_id):
            return True
        return False

    def restore_engine_instance(self, trial_id):
        """Interface for restoring an Engine instance."""
        try:
            self.scheduler_handler.restore_engine_instance(trial_id=trial_id)
            return True
        except RuntimeError:
            return False

    def remove_engine_instance(self, trial_id):
        """Interface for removing an Engine instance."""
        try:
            self.scheduler_handler.stop_engine_instance(trial_id=trial_id)
            return True
        except RuntimeError:
            return False

    def run_scheduler(self):
        """Interface for Scheduler Handler instance setup and start."""
        self.setup_scheduler_handler()

    def get_heartbeat_handler_status(self):
        """Return the status variable of the Heartbeat Handler instance."""
        return self.heartbeat_handler.status

    def setup_heartbeat_handler(self):
        """Create Heartbeat Handler instance."""
        logging.info("Creating Heartbeat Handler instance.")
        self.heartbeat_handler.start()

    def run_heartbeat_handler(self):
        """Interface for Heartbeat Handler instance setup and start."""
        self.setup_heartbeat_handler()

    def get_heartbeat_instances(self):
        """Return a list of running Heartbeat instances."""
        return self.heartbeat_handler.heartbeat_instances

    def remove_heartbeat_instance(self, trial_id):
        """Interface for removing a Heartbeat instance."""
        try:
            self.heartbeat_handler.stop_heartbeat_instance(trial_id=trial_id)
            return True
        except RuntimeError:
            return False
