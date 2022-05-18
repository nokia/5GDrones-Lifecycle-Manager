# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Tests for module scheduler_handler."""

from lifecycle_manager.scheduler.scheduler_handler import SchedulerHandler
from lifecycle_manager.tests.dummy_modules import DummyInternalScheduler

# Initialize Scheduler Handler instance
scheduler_handler = SchedulerHandler()
# Initialize needed dummy instances
scheduler_handler.internal_scheduler = DummyInternalScheduler(scheduler_handler)


def test_scheduler_handler_instance():
    """Test that Scheduler Handler instance has been created successfully."""
    assert scheduler_handler.status == 'Idle'


def test_set_status():
    """Test scheduler_handler.set_status().
    Assert that a correct state is returned after setting the state.
    """
    scheduler_handler.set_status()
    status = scheduler_handler.status
    assert status == 'Idle'


def test_create_engine_instance():
    """Test scheduler_handler.create_executor_engine.
    Assert that an Executor Engine instances is not empty.
    """
    scheduler_handler.create_executor_engine_instance(trial_id='test')
    assert scheduler_handler.engine_instances


def test_restore_engine_instance():
    """Test scheduler_handler.restore_engine_instance for an existing instance.
    Assert correct response.
    """
    success = scheduler_handler.restore_engine_instance(trial_id='test')
    assert success


def test_restore_invalid_engine_instance():
    """Test scheduler_handler.restore_engine_instance for a non-existent instance.
    Assert correct response.
    """
    success = scheduler_handler.restore_engine_instance(trial_id='non_existent')
    assert not success


def test_stop_all_engine_instances():
    """Test scheduler_handler.stop_all_engine_instances().
    Assert that all Executor Engine instances are stopped successfully.
    """
    assert scheduler_handler.stop_all_engine_instances()
    assert not scheduler_handler.engine_instances
