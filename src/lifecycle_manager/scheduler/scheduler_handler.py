# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Thread for handling InternalScheduler instance and Executor Engine instances."""
from datetime import datetime, timedelta
import logging
import time
from threading import Thread, Event

from apscheduler.jobstores.base import ConflictingIdError
from lifecycle_manager.config import services
from lifecycle_manager.executor.engine import Engine
from lifecycle_manager.scheduler.internal_scheduler import InternalScheduler
from lifecycle_manager.scheduler.trial_registry_client import TrialRegistryClient


class RunSchedulerException(Exception):
    """Raised when encountered an exception in SchedulerHandler.run"""


class SchedulerHandler(Thread):
    """Scheduler Handler class."""

    def __init__(self):
        super().__init__()
        self.internal_scheduler = InternalScheduler(self)
        self.trial_repo_client = TrialRegistryClient()
        self._automatic_scheduling = False
        self._engine_instances = []
        self._engine_instance_statuses = []
        self._shutdown = False
        self._status = 'Idle'

    @property
    def status(self):
        """Getter for variable status."""
        return self._status

    @property
    def automatic_scheduling(self):
        """Getter for automatic scheduling boolean."""
        return self._automatic_scheduling

    @property
    def engine_instances(self):
        """Getter for engine instance list."""
        return self._engine_instances

    @property
    def engine_instance_statuses(self):
        """Getter for engine instance statuses."""
        return self._engine_instance_statuses

    def toggle_automatic_scheduling(self):
        """Toggle boolean."""
        if self.automatic_scheduling:
            self._automatic_scheduling = False
            return
        self._automatic_scheduling = True

    def shutdown(self):
        """Set shutdown to True for stopping the thread."""
        self._shutdown = True

    def set_status(self):
        """Set the status variable of the Scheduler Handler."""
        if self.internal_scheduler.scheduler.get_jobs():
            self._status = 'Scheduled job(s) initiated'
        else:
            self._status = 'Idle'

    def check_trial_id_statuses(self, trial_ids_start_times):
        """Check whether trials with the given ids can be shceduled."""
        schedulable_trials = []
        already_scheduled = []
        already_executing = []
        for trial in trial_ids_start_times:
            flag = False
            trial_id = str(trial['trial_id'])
            start_time = trial['start_time']
            start_time_dt = self.internal_scheduler.create_dt_start_time(start_time)
            for engine_instance in self._engine_instances:
                if engine_instance.id == trial_id:
                    already_executing.append(trial_id)
                    flag = True
                    break
            scheduled_jobs = self.internal_scheduler.get_scheduled_jobs()
            for job in scheduled_jobs:
                if not flag:
                    if job["id"] == trial_id and start_time_dt == job["trigger"]:
                        already_scheduled.append(trial_id)
                        flag = True
                        break
                    self.internal_scheduler.remove_job(trial_id)
                    break
                break
            if not flag:
                trial = {'trial_id': trial_id, 'start_time': start_time}
                schedulable_trials.append(trial)
        return schedulable_trials, already_scheduled, already_executing

    def fetch_all_trials(self):
        """Get all available trials from Trial registry."""
        success, message, trial_ids_start_times = self.trial_repo_client.get_all_trial_ids_and_start_times()
        if success:
            if trial_ids_start_times:
                schedulable_trials, already_scheduled, already_executing = self.check_trial_id_statuses(
                    trial_ids_start_times)
                scheduled_trials = []
                for trial in schedulable_trials:
                    start_time = trial['start_time']
                    trial_id = trial['trial_id']
                    if self.execute_scheduled_job(start_time, trial_id):
                        scheduled_trials.append(trial_id)
                message = "Trials added to scheduling: {}".format(scheduled_trials)
                if already_scheduled or already_executing:
                    message = "Trials added to scheduling: {}. Trials already scheduled: {}. Trials already " \
                              "executing: {}.".format(scheduled_trials, already_scheduled, already_executing)
                return True, message
        return False, message

    def fetch_trial(self, trial_id):
        """Get trial start time for a specific trial from Trial registry."""
        success, message, start_time = self.trial_repo_client.get_trial_start_time(trial_id=trial_id)
        if success:
            if start_time:
                for engine_instance in self._engine_instances:
                    if engine_instance.id == trial_id:
                        return False, "Engine instance with trial ID: {} already exists.".format(trial_id)
                if self.execute_scheduled_job(start_time, trial_id):
                    return True, "Trial scheduled with trial ID: {}".format(trial_id)
            return False, message
        return False, message

    def execute_scheduled_job(self, start_date, trial_id):
        """Call Internal Scheduler instance to execute a scheduled job."""
        try:
            self.internal_scheduler.add_scheduled_job(start_date=start_date, trial_id=trial_id)
            return True
        except ConflictingIdError:
            return False

    def create_executor_engine_instance(self, trial_id):
        """Call Executor engine to create an Engine instance."""
        logging.info("Calling Execution engine to create an Executor instance with Trial ID: %s", trial_id)
        engine_instance = Engine(trial_id, services.Settings())
        self._engine_instances.append(engine_instance)
        self._engine_instance_statuses.append({"ID": trial_id, "status": "Active"})
        engine_instance.start()
        engine_instance.set_execute_event()
        self.set_status()

    def restore_engine_instance(self, trial_id):
        """Restore an Executor Engine instance thread."""
        logging.info("Restoring Executor Engine thread...")
        for instance in self._engine_instances:
            if instance.id == trial_id:
                instance.restore()
                return True
        return False

    def run(self):
        """Run Scheduler Handler main functionalities."""
        logging.info("Running Scheduler Handler instance.")

        stop_event = Event()
        last_poll = datetime.utcnow()
        while True:
            self.set_status()
            current_poll = datetime.utcnow()
            if (current_poll - last_poll) > timedelta(minutes=1) and self.automatic_scheduling:
                logging.info("Fetching trials from repository")
                self.fetch_all_trials()
                last_poll = current_poll
            time.sleep(1)
            for instance in self._engine_instances:
                if instance.failed:
                    for engine in self._engine_instance_statuses:
                        if engine["ID"] == instance.id:
                            engine["status"] = "Failed"
                if instance.finished:
                    for engine in self._engine_instance_statuses:
                        if engine["ID"] == instance.id:
                            engine["status"] = "Finished"

            if self._shutdown:
                logging.warning("Shutting down Scheduler instance.")
                stop_event.set()
                self.internal_scheduler.signal_stop()
                self.internal_scheduler.join()
                break

    def is_process_alive(self, stop_event, process_instance):
        """Check that a process instances is alive."""
        logging.info("Process check thread started.")
        while not stop_event.is_set():
            time.sleep(1)
            if not process_instance.is_alive():
                logging.warning("Process instance is not alive.")
                if not self._shutdown:
                    process_instance.join()
                else:
                    self.shutdown()
                    stop_event.wait(5)

    def stop_internal_scheduler(self):
        """Stop Internal Scheduler thread."""
        logging.info("Stopping Internal Scheduler thread...")
        if self.internal_scheduler.signal_stop():
            self.internal_scheduler.join()
        logging.info("Internal Scheduler thread stopped.")

    def stop_engine_instance(self, trial_id):
        """Stop an Engine instance."""
        logging.info("Stopping an Engine instance with ID: %s)", str(trial_id))
        for instance in self._engine_instances:
            if trial_id == instance.id:
                instance.set_stop_event()
                instance.join()
                self._engine_instances.remove(instance)
        for instance in self._engine_instance_statuses:
            if trial_id == instance["ID"]:
                self._engine_instance_statuses.remove(instance)

    def stop_all_engine_instances(self):
        """Stop all Executor Engine instances."""
        logging.info("Stopping all Executor Engine threads...")
        for instance in self._engine_instances:
            instance.set_stop_event()
        for instance in self._engine_instances:
            instance.join()
        self._engine_instances = []
        self._engine_instance_statuses = []
        logging.info("All Executor Engine threads stopped.")
        return True
