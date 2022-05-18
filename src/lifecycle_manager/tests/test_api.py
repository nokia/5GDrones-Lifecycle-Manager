# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

""" Unit tests to check all functions of the application works correctly"""
import datetime
import time

from fastapi.testclient import TestClient
from tzlocal import get_localzone

import lifecycle_manager.app as app
from lifecycle_manager.tests.dummy_modules import DummyRunScheduler
from lifecycle_manager.api_customization import API_KEY
global test_token
test_token = None
dummy_run_scheduler = DummyRunScheduler()
app.run_scheduler = dummy_run_scheduler
client = TestClient(app.app)


def test_read_status_page():
    """Test the status page works correctly"""
    response = client.get("/status", headers={"Authorization": API_KEY})
    assert response.status_code == 200
    assert response.json() == {"message": "This is Lifecycle Manager 1.0.2!",
                               "Scheduler_status": "Idle",
                               "Automatic_scheduling": False,
                               "scheduled_trials": "[]",
                               "Executor_Engine_instances": "[]",
                               "Heartbeat_instances": "[]"}


def test_schedule_trial_with_trial_id_and_start_time():
    """Test app.schedule_trial_with_trial_id_and_start_time()
    Assert that correct status code and response are returned.
    """
    local_tz = get_localzone()
    start_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=60)) \
        .astimezone(local_tz).replace(microsecond=0).isoformat()

    body = {'trial_id': 'test', 'start_time': start_time}
    response = client.post("/debug/trial/schedule", headers={"Authorization": API_KEY}, json=body)
    assert response.status_code == 200
    assert response.json() == {"message": "Trial scheduling added with trial ID: test"}


def test_delete_scheduled_trial():
    """Test app.delete_scheduled_trial()
    Assert that correct status code and response are returned.
    """
    response = client.delete("/debug/trial/test/schedule", headers={"Authorization": API_KEY})
    assert response.status_code == 200
    assert response.json() == {"message": "Trial scheduling removed with trial ID: test"}


def test_schedule_all_trials_from_trial_registry():
    """Test app.schedule_all_trials_from_trial_registry.
    Assert that correct status code and response are returned.
    """
    response = client.post("/debug/trial/schedule-all", headers={"Authorization": API_KEY})
    assert response.status_code == 200
    assert response.json() == {'message': 'Trials added to scheduling: [test]'}


def test_schedule_a_trial_from_trial_registry_with_trial_id():
    """Test app.schedule_all_trials_from_trial_registry.
    Assert that correct status code and response are returned.
    """
    response = client.post("/debug/trial/test/schedule", headers={"Authorization": API_KEY})
    assert response.status_code == 200
    assert response.json() == {'message': 'Trial scheduled with trial ID: test'}


def test_schedule_trial_with_invalid_request_body():
    """Test app.post_job()
    Note: Testing adding job with faulty request body.
    Assert that correct status code and response are returned.
    """
    # Testing with a faulty request body field
    local_tz = get_localzone()
    start_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=60)) \
        .astimezone(local_tz).replace(microsecond=0).isoformat()
    body = {'test_id': 'test', 'start_time': start_time}
    response = client.post("/debug/trial/schedule", headers={"Authorization": API_KEY}, json=body)
    assert response.status_code == 422

    # Testing with an already passed start time
    start_time = "2020-02-09T15:12:20+02:00"
    body = {'trial_id': 'test', 'start_time': start_time}
    response = client.post("/debug/trial/schedule", headers={"Authorization": API_KEY}, json=body)
    assert response.status_code == 400


def test_delete_scheduled_trial_with_invalid_trial_id():
    """Test app.delete_scheduled_trial()
    Note: Testing removing a job that does not exist.
    Assert that correct status code and response are returned.
    """
    response = client.delete("/debug/trial/invalid/schedule", headers={"Authorization": API_KEY})
    assert response.status_code == 400
    assert response.json() == {"detail": "Trial scheduling with ID: invalid does not exist."}


def test_delete_engine_instance():
    """Test app.delete_engine_instance()
    Assert that correct status code and response are returned.
    """
    local_tz = get_localzone()
    start_time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=60)) \
        .astimezone(local_tz).replace(microsecond=0).isoformat()
    body = {'trial_id': 'test', 'start_time': start_time}
    client.post("/debug/schedule-trial", json=body)
    time.sleep(15)
    response = client.delete("/debug/engine/test", headers={"Authorization": API_KEY})
    assert response.status_code == 200
    assert response.json() == {"message": "Engine instance removed with trial ID: test"}


def test_delete_engine_instance_with_invalid_trial_id():
    """Test app.delete_engine_instance()
    Note: Testing removing an Engine instance that does not exist.
    Assert that correct status code and response are returned.
    """
    response = client.delete("/debug/engine/invalid", headers={"Authorization": API_KEY})
    assert response.status_code == 400
    assert response.json() == {"detail": "Engine instance with trial ID: invalid does not exist."}


def test_no_auth():
    """Test app authentication
    Assert that correct status code and response are returned.
    """
    response = client.get("/status")
    assert response.status_code == 401


def test_get_token():
    """Test token generation
    Note: Testing removing an Engine instance that does not exist.
    Assert that correct status code and response are returned.
    """
    global test_token
    response = client.post("/token/1", headers={"Authorization": API_KEY})
    assert response.json()["Authorization"]
    test_token = response.json()["Authorization"]
    assert response.status_code == 200


def test_token_auth():
    """Test token authentication and decode
    Note: Testing removing an Engine instance that does not exist.
    Assert that correct status code and response are returned.
    """
    response = client.get("/token/1", headers={"Authorization": test_token})
    assert response.json() == {"message": "Success"}
    assert response.status_code == 200


def test_token_delete():
    """Test token delete and that token cant be used anymore.
    Note: Testing removing an Engine instance that does not exist.
    Assert that correct status code and response are returned.
    """
    response = client.delete("/token/1", headers={"Authorization": test_token})
    assert response.status_code == 200
    fail_response = response = client.get("/token/1", headers={"Authorization": test_token})
    assert fail_response.status_code == 401


def test_active_engine_not_found():
    """Test endpoint with an unscheduled ID.
    Assert that correct status code and response are returned.
    """
    response = client.post("/trial/invalid/active", headers={"Authorization": API_KEY})
    assert response.status_code == 400
    assert response.json() == {"detail": "Engine with requested ID does not exist"}


def test_finish_engine_not_found():
    """Test endpoint with an unscheduled ID.
    Assert that correct status code and response are returned.
    """
    response = client.post("/trial/invalid/active", headers={"Authorization": API_KEY})
    assert response.status_code == 400
    assert response.json() == {"detail": "Engine with requested ID does not exist"}
