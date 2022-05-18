# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

""" Tests for module internal_scheduler."""
import datetime
import pytest

from apscheduler.jobstores.base import ConflictingIdError
from tzlocal import get_localzone

from lifecycle_manager.scheduler.internal_scheduler import InternalScheduler
from lifecycle_manager.tests.dummy_modules import DummySchedulerHandler

# Initialize needed dummy instances
dummy_scheduler_handler = DummySchedulerHandler()

# Initialize Internal Scheduler instance
internal_scheduler = InternalScheduler(dummy_scheduler_handler)
dummy_scheduler_handler.internal_scheduler = internal_scheduler


def test_run():
    """ Test internal_scheduler.start().
    Test that Internal Scheduler thread starts successfully.
    """
    internal_scheduler.start()
    assert internal_scheduler.scheduler_handler == dummy_scheduler_handler


def test_add_scheduled_job():
    """Test internal_scheduler.add_scheduled_job().
    Assert that a correct scheduled job is returned.
    """
    local_tz = get_localzone()
    test_start_date = (datetime.datetime.utcnow() + datetime.timedelta(seconds=120))\
        .astimezone(local_tz).replace(microsecond=0).isoformat()
    internal_scheduler.add_scheduled_job(start_date=test_start_date, trial_id='2')
    jobs = internal_scheduler.get_scheduled_jobs()
    assert jobs


def test_fail_to_add_scheduled_job():
    """Test internal_scheduler.add_scheduled_job().
    Assert that a correct exception is thrown.
    """
    with pytest.raises(ConflictingIdError) as exception_info:
        local_tz = get_localzone()
        start_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=120)) \
            .astimezone(local_tz).replace(microsecond=0).isoformat()
        internal_scheduler.add_scheduled_job(start_date=start_time, trial_id='2')
    assert exception_info.type is ConflictingIdError
    assert exception_info.value.args[0] == 'Job identifier (2) conflicts with an existing job'


def test_remove_job():
    """Test internal_scheduler.remove()
    Assert that no jobs are returned.
    """
    internal_scheduler.remove_job(removable_job_id='2')
    jobs = internal_scheduler.get_scheduled_jobs()
    assert not jobs


def test_remove_invalid_job():
    """Test internal_scheduler.remove()
    Assert that removing the job returns false.
    """
    success = internal_scheduler.remove_job(removable_job_id='does_not_exist')
    assert not success


def test_stop():
    """Test internal_scheduler.signal_stop()."""
    internal_scheduler.signal_stop()
