# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Tests for module run_scheduler."""

from lifecycle_manager.run_scheduler import RunScheduler
from lifecycle_manager.tests.dummy_modules import DummySchedulerHandler, DummyInternalScheduler

# Initialize RunScheduler instance to be tested
run_scheduler = RunScheduler()

# Initialize needed dummy instances
scheduler_handler_dummy = DummySchedulerHandler()
scheduler_handler_dummy.internal_scheduler = DummyInternalScheduler(scheduler_handler_dummy)
run_scheduler.scheduler_handler = scheduler_handler_dummy


def test_run_scheduler():
    """Test run_scheduler.setup_scheduler_handler().
    Assert that creation and running a Scheduler instance are executed successfully.
    """
    run_scheduler.run_scheduler()
    assert run_scheduler.scheduler_handler.status == 'Idle'
    assert not run_scheduler.scheduler_handler.engine_instances
    assert run_scheduler.heartbeat_handler.status == 'Idle'
    assert not run_scheduler.heartbeat_handler.heartbeat_instances


def test_get_status():
    """Test run_scheduler.get_status().
    Assert that a correct status is returned.
    """
    status = run_scheduler.get_status()
    assert status == 'Idle'


def test_get_scheduled_jobs():
    """Test run_scheduler.get_jobs().
    Assert that no jobs are scheduled.
    """
    returned_jobs = run_scheduler.get_scheduled_jobs()
    assert not returned_jobs


def test_get_executor_engine_instances():
    """Test run_scheduler.get_executor_engine_instances().
    Assert that no Executor Engine instances are returned.
    """
    instances = run_scheduler.get_executor_engine_instances()
    assert not instances


def test_get_heartbeat_instances():
    """Test run_scheduler.get_heartbeat_instances().
    Assert that no Heartbeat instances are returned.
    """
    instances = run_scheduler.get_heartbeat_instances()
    assert not instances
