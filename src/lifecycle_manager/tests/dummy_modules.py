"""Dummy versions of modules for testing."""
from threading import Thread, Event


class DummyEngine(Thread):
    """Dummy class for Executor Engine."""
    def __init__(self, trial_id):
        super().__init__()
        self.id = trial_id

    @staticmethod
    def restore():
        """Dummy for restore."""
        return True


class DummyRunScheduler:
    """Dummy class for Run Scheduler."""
    def __init__(self):
        self.scheduler_handler = DummySchedulerHandler()
        self.heartbeat_handler = DummyHeartbeatHandler()

    def setup_scheduler_handler(self):
        """Create Scheduler Handler instance."""

    def stop_scheduler(self):
        """Stops the whole LCM instance."""

    def get_automatic_scheduling(self):
        """Return boolen from handler."""
        return self.scheduler_handler.automatic_scheduling

    def toggle_automatic_scheduling(self):
        """Return boolen from handler."""
        return self.scheduler_handler.toggle_automatic_scheduling()

    def get_scheduled_jobs(self):
        """Return scheduled jobs."""
        return self.scheduler_handler.internal_scheduler.get_scheduled_jobs()

    def get_status(self):
        """Return the status variable.."""
        return self.scheduler_handler.status

    def get_executor_engine_instance_statuses(self):
        """Return a list of running Executor Engine instances."""
        instances = []
        for instance in self.scheduler_handler.engine_instances:
            instances.append({"Trial ID": instance.id, "failed": instance.failed})
        return instances

    def get_executor_engine_instances(self):
        """Return a list of running Executor Engine instances."""
        return self.scheduler_handler.engine_instances

    def get_heartbeat_instances(self):
        """Return a list of running Heartbeat instances."""
        return self.heartbeat_handler.heartbeat_instances

    def add_new_job(self, start_time, trial_id):
        """Interface for adding a new job to Scheduler."""
        self.scheduler_handler.engine_instances.append(DummyEngine(trial_id))
        return True

    @staticmethod
    def remove_job(trial_id):
        """Interface for removing a job from Scheduler."""
        if trial_id == "invalid":
            return False
        return True

    @staticmethod
    def remove_engine_instance(trial_id):
        """Interface for removing an Engine instance."""
        return True

    def run_scheduler(self):
        """Interface for Scheduler Handler instance setup and start."""
        self.setup_scheduler_handler()

    @staticmethod
    def fetch_all_trials():
        """Fetch all trials."""
        return True, "Trials added to scheduling: [test]"

    @staticmethod
    def fetch_trial(trial_id):
        """Fetch trial."""
        return True, "Trial scheduled with trial ID: {}".format(trial_id)


class DummySchedulerHandler(Thread):
    """Dummy class for SchedulerHandler."""
    def __init__(self):
        super().__init__()
        self.internal_scheduler = DummyInternalScheduler(self)
        self._engine_instances = []
        self.config = self._read_config(config_name='startup')
        self._dummy_status = 'Idle'
        self._automatic_scheduling = False

    @property
    def status(self):
        """Getter for variable dummy_status."""
        return self._dummy_status

    @property
    def engine_instances(self):
        """Getter for dummy engine instance list."""
        return self._engine_instances

    @staticmethod
    def _read_config(config_name):
        """Read configuration."""
        return {'config_name': config_name}

    @property
    def automatic_scheduling(self):
        """Getter for automatic scheduling boolean."""
        return self._automatic_scheduling

    def toggle_automatic_scheduling(self):
        """Toggle boolean."""
        if self.automatic_scheduling:
            self._automatic_scheduling = False
            return
        self._automatic_scheduling = True

    def set_status(self):
        """Set the status variable of the Scheduler Handler."""
        if self.internal_scheduler.get_scheduled_jobs():
            self._dummy_status = 'Scheduled job(s) initiated'
        else:
            self._dummy_status = 'Idle'

    def _execute_timer_job(self, dummy_start_time, dummy_trial_id):
        """Execute a timer job."""
        self.internal_scheduler.add_timer_job(dummy_start_time, dummy_trial_id)

    def _execute_scheduled_job(self, dummy_start_date, dummy_trial_id):
        """Execute a scheduled job."""
        try:
            self.internal_scheduler.add_scheduled_job(dummy_start_date, dummy_trial_id)
            return True
        except Exception:
            return False

    def create_executor_engine_instance(self, trial_id):
        """Create an Engine instance."""

    def restore_engine_instance(self, trial_id):
        """Restore an Executor Engine thread."""
        for engine in self._engine_instances:
            if engine.id == trial_id:
                engine.restore()
                return True
        return False

    def run(self):
        """Run Scheduler Handler main functionalities."""

    def main_logic_for_testing(self):
        """Temporary main logic function for Scheduler development. Will be replaced!"""

    def is_process_alive(self, stop_event, process_instance):
        """Check that a process instances is alive."""

    def stop_internal_scheduler(self):
        """Stop Internal Scheduler thread."""

    def stop_executor_instance(self, trial_information):
        """Stop an Executor Handler instance."""

    def stop_all_executor_instances(self):
        """Stop all Executor Engine instances."""


class DummyInternalScheduler(Thread):
    """Dummy class for InternalScheduler."""

    def __init__(self, scheduler_handler):
        super().__init__()
        self.scheduler_handler = scheduler_handler
        self.scheduler = DummyBackgroundScheduler()
        self._dummy_stop = False
        self._dummy_stop_event = Event()

    def get_scheduled_jobs(self):
        """Return an array of scheduled jobs from self.scheduler."""
        return self.scheduler.get_jobs()

    def get_scheduled_jobs_pretty(self):
        """Return an array of scheduled jobs from self.scheduler."""
        return self.scheduler.get_jobs()

    def signal_stop(self):
        """Set _stop and stop event to True."""
        self._dummy_stop = True
        self._dummy_stop_event.set()

    def add_timer_job(self, start_time, trial_id):
        """Create and add a timer job to the BackgroundScheduler instance.
        Calls the target function after a set interval has passed.
        """
        self.scheduler.add_job({'start_time': start_time, 'trial_id': trial_id})

    def add_scheduled_job(self, start_date, trial_id):
        """Create and add a scheduled job to the BackgroundScheduler instance.
        Calls the target function when a set time has been reached.
        """
        self.scheduler.add_job({'start_date': start_date, 'trial_id': trial_id})

    def run(self):
        """Start Internal Scheduler thread."""
        return True

    @staticmethod
    def _main_logic():
        """Wait until an event is set."""
        return True


class DummyBackgroundScheduler:
    """Dummy class for APScheduler.BackgroundScheduler"""
    def __init__(self):
        self.jobs = []
        self.start_time = 15

    def get_jobs(self):
        """Return jobs."""
        return self.jobs

    def add_job(self, test_job):
        """Add job."""
        self.jobs.append(test_job)


class DummyHeartbeatHandler(Thread):
    """Dummy class for HeartbeatHandler."""
    def __init__(self):
        super().__init__()
        self.heartbeat = DummyHeartbeat(self)
        self._heartbeat_instances = []
        self._dummy_status = 'Idle'

    @property
    def status(self):
        """Getter for variable status."""
        return self._dummy_status

    @property
    def heartbeat_instances(self):
        """Getter for heartbeat instance list."""
        return self._heartbeat_instances


class DummyHeartbeat(Thread):
    """Dummy class for Heartbeat."""
    def __init__(self, _id):
        super().__init__()
        self.id = _id
        self._dummy_stop = False
        self._dummy_stop_event = Event()
