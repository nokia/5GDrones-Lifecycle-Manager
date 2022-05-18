# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Test for module heartbeat_handler"""

from lifecycle_manager.heartbeat.heartbeat_handler import HeartbeatHandler
from lifecycle_manager.tests.dummy_modules import DummyHeartbeat

# Initialize Heartbeat Handler instance
heartbeat_handler = HeartbeatHandler()
# Initialize needed dummy instances
heartbeat_handler.heartbeat = DummyHeartbeat(heartbeat_handler)


def test_heartbeat_handler_instance():
    """Test that Heartbeat Handler instance has been created successfully."""
    assert heartbeat_handler.status == 'Idle'


def test_set_status():
    """Test heartbeat_handler.set_status().
    Assert that a correct state is returned after setting the state.
    """
    heartbeat_handler.set_status()
    status = heartbeat_handler.status
    assert status == 'Idle'


def test_create_and_stop_heartbeat_instance():
    """Test heartbeat_handler.create_heartbeat_instance() and heartbeat_handler.stop_heartbeat_instance.
    Assert that a heartbeat instances is not empty when heartbeat has been created and then remove the created instance.
    Test that asserting a heartbeat instances is empty
    """
    heartbeat_handler.create_heartbeat_instance(trial_id='test')
    assert heartbeat_handler.heartbeat_instances
    assert heartbeat_handler.status == 'Heartbeat check(s) initiated'

    heartbeat_handler.stop_heartbeat_instance(trial_id='test')
    assert not heartbeat_handler.heartbeat_instances
    assert heartbeat_handler.status == 'Idle'
