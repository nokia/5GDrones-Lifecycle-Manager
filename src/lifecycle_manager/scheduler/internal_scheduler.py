# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Module for implementing Internal Scheduler and related functionalities."""
import datetime
import logging
import time
from threading import Thread, Event

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError, JobLookupError


class InternalScheduler(Thread):
    """Internal Scheduler class."""

    def __init__(self, scheduler_handler):
        super().__init__()
        self.scheduler_handler = scheduler_handler
        self.scheduler = BackgroundScheduler()
        self._stop = False
        self._stop_event = Event()

    def get_scheduled_jobs(self):
        """Return an array of scheduled jobs from self.scheduler."""
        jobs = []
        for job in self.scheduler.get_jobs():
            trigger_str = str(job.trigger)[5:24].replace(" ", "T")
            datetime_trigger = datetime.datetime.strptime(trigger_str, "%Y-%m-%dT%H:%M:%S")
            jobs.append({"id": str(job.id), "trigger": datetime_trigger})
        return jobs

    def get_scheduled_jobs_pretty(self):
        """Return an array of scheduled jobs from self.scheduler."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({"id": str(job.id), "trigger": str(job.trigger)})
        return jobs

    def signal_stop(self):
        """Set _stop and stop event to True."""
        self._stop = True
        self._stop_event.set()

    def _backup(self):
        """Save needed information and pass to the target."""

    def _restore(self):
        """Load saved information to the Internal Scheduler instance."""

    def create_dt_start_time(self, start_date):
        """Crete dt object from string."""
        timezone = int("00")
        start_time_dt = datetime.datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S%z")
        start_time_str = str(start_time_dt.year) + "-" + str(start_time_dt.month) + "-" + \
            str(start_time_dt.day) + "T" + str(start_time_dt.hour + timezone) + \
            ":" + str(start_time_dt.minute) + ":" + str(start_time_dt.second)
        start_time_dt = datetime.datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S")
        return start_time_dt

    def add_scheduled_job(self, start_date, trial_id):
        """Create and add a scheduled job to the BackgroundScheduler instance.
        Calls the target function when a set time has been reached.
        """
        try:
            logging.info("Creating and adding a scheduled job with ID: %s", str(trial_id))
            self.scheduler.add_job(self.scheduler_handler.create_executor_engine_instance, 'date',
                                   run_date=self.create_dt_start_time(start_date), args=[trial_id], id=trial_id)
            if not self.scheduler.running:
                self.scheduler.start()
        except ConflictingIdError as conflicting_id_error:
            logging.error("Could not add a job: %s", str(conflicting_id_error))
            raise ConflictingIdError(job_id=trial_id) from conflicting_id_error
        logging.info("Job added and started.")

    def remove_job(self, removable_job_id):
        """Remove a job from the BackgroundScheduler instance based on the job ID."""
        try:
            self.scheduler.remove_job(removable_job_id)
            return True
        except JobLookupError:
            logging.exception("Job with ID: %s does not exist.", str(removable_job_id))
            return False

    def run(self):
        """Start Internal Scheduler thread."""
        logging.info("Running Internal Scheduler thread.")
        while not self._stop:
            self._main_logic()

    def _main_logic(self):
        """Wait until an event is set."""
        logging.info("Running Internal Scheduler.")
        while not self._stop_event:
            time.sleep(1)
