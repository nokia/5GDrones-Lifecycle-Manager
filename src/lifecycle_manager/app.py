# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""This file starts the application."""
import datetime
import os

from threading import Thread

import jwt
import uvicorn
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyCookie, APIKeyHeader, APIKey
from pydantic import BaseModel

from lifecycle_manager.api_customization import FASTAPI_TITLE, FASTAPI_DESCRIPTION, ORIGINS
from lifecycle_manager.api_customization import FASTAPI_VERSION, FASTAPI_DOCS_URL, FASTAPI_ROOT_PATH
from lifecycle_manager.api_customization import API_KEY, SECRET
from lifecycle_manager.run_scheduler import RunScheduler

root_dir = os.path.dirname(os.path.abspath(__file__))
TOKENS = []
API_KEY_NAME = "Authorization"
_apikey_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
_apikey_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

app = FastAPI(title=FASTAPI_TITLE,
              description=FASTAPI_DESCRIPTION,
              version=FASTAPI_VERSION,
              docs_url=FASTAPI_DOCS_URL,
              root_path=FASTAPI_ROOT_PATH)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

run_scheduler = RunScheduler()


class TrialItem(BaseModel):
    """Class model for schedule_trial_with_trial_id_and_start_time request body."""
    trial_id: str
    start_time: str


def create_token_with_id(secret: str, trial_id: str):
    """Create jwt token for engine callbacks."""
    key = jwt.encode({"trial_id": trial_id}, secret, "HS256").decode('utf-8')
    return key


def decode_token(secret: str, token, trial_id):
    """Decode token"""
    token_trial_id = jwt.decode(token, secret, algorithms=['HS256'])["trial_id"]
    if str(token_trial_id) == str(trial_id):
        return
    raise HTTPException(
        status_code=401, detail="Unauthorized")


def engine_valid(trial_id: str):
    """Test that engine is still relevant"""
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if not engine.finished and not engine.failed:
                return
            break
    raise HTTPException(
        status_code=403, detail="Unauthorized")


async def get_key(apikey_header: str = Security(_apikey_header), apikey_cookie: str = Security(_apikey_cookie)):
    """Get key from headers or cookies."""
    if apikey_header == API_KEY:
        return apikey_header
    if apikey_cookie == API_KEY:
        return apikey_cookie
    raise HTTPException(
        status_code=401, detail="Unauthorized")


async def get_key_callback(apikey_header: str = Security(_apikey_header),
                           apikey_cookie: str = Security(_apikey_cookie)):
    """Get token from headers or cookies."""
    for key in TOKENS:
        if str(apikey_header) == str(key):
            return apikey_header
        if apikey_cookie == str(key):
            return apikey_cookie
    raise HTTPException(
        status_code=401, detail="Unauthorized")


@app.get('/status', tags=["Status"])
def get_message_from_status_page(api_key: APIKey = Depends(get_key)):
    """This function receives get command from a user to go to status page."""
    return {"message": "This is Lifecycle Manager {}!".format(FASTAPI_VERSION),
            "Scheduler_status": run_scheduler.get_status(),
            "Automatic_scheduling": run_scheduler.get_automatic_scheduling(),
            "scheduled_trials": str(run_scheduler.get_scheduled_jobs()),
            "Executor_Engine_instances": str(run_scheduler.get_executor_engine_instance_statuses()),
            "Heartbeat_instances": str(run_scheduler.get_heartbeat_instances())}


@app.post('/trial/scheduling', tags=["Status"])
def toggle_automatic_scheduling(api_key: APIKey = Depends(get_key)):
    """Toggle automatic scheduling on/off"""
    run_scheduler.toggle_automatic_scheduling()
    return{"message": "Automatic scheduling: " + str(run_scheduler.get_automatic_scheduling())}


@app.post('/trial/{trial_id}/callback/slice', tags=["Trial Callback"])
def post_callback_slice(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Callback from trialenforcement, to advance the execution."""
    decode_token(SECRET, api_key, trial_id)
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if not engine.executor.get_slice_created:
                engine.executor.add_response('SliceCallback', 200)
                engine.executor.set_slice_created()
                if engine.set_executor_state('UpdateDeploymentSlice'):
                    return {"message": "State change registered"}
            else:
                engine.executor.add_response('SliceDeleteCallback', 200)
                if engine.set_executor_state('UpdateStatusFinish'):
                    return {"message": "State change registered"}
            raise HTTPException(status_code=400, detail="Executor not ready for state change.")
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/trial/{trial_id}/callback/cloudvnfboarding',
          tags=["Trial Callback"])
def post_callback_cloudvnfboarding(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Callback from trialenforcement, to advance the execution."""
    decode_token(SECRET, api_key, trial_id)
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if engine.set_executor_state('UpdateCloudVnfBoardingStatus'):
                return {"message": "State change registered"}
            raise HTTPException(status_code=400, detail="Executor not ready for state change.")
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/trial/{trial_id}/callback/cloudvnfdeployment', tags=["Trial Callback"])
def post_callback_cloudvnfdeployment(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Callback from trialenforcement, to advance the execution."""
    decode_token(SECRET, api_key, trial_id)
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if engine.set_executor_state('UpdateCloudVnfDeploymentStatus'):
                return {"message": "State change registered"}
            raise HTTPException(status_code=400, detail="Executor not ready for state change.")
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/trial/{trial_id}/callback/edgevnfonboarding', tags=["Trial Callback"])
def post_callback_edgevnfonboarding(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Callback from trialenforcement, to advance the execution."""
    decode_token(SECRET, api_key, trial_id)
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if engine.set_executor_state('UpdateEdgeVnfBoardingStatus'):
                return {"message": "State change registered"}
            raise HTTPException(status_code=400, detail="Executor not ready for state change.")
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/trial/{trial_id}/callback/edgevnfdeployment', tags=["Trial Callback"])
def post_callback_edgevnfdeployment(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Callback from trialenforcement, to advance the execution."""
    decode_token(SECRET, api_key, trial_id)
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if engine.set_executor_state('UpdateEdgeVnfDeploymentStatus'):
                return {"message": "State change registered"}
            raise HTTPException(status_code=400, detail="Executor not ready for state change.")
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/trial/{trial_id}/active', tags=["Trial"])
def post_trial_kpi_status(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Receive status message and forward it to executor."""
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if engine.executor.get_kpi_status == "Idle":
                if engine.set_executor_state("SendKpiActive"):
                    return {"message": "State change registered"}
                raise HTTPException(status_code=400, detail="Executor not ready for state change.")
            raise HTTPException(status_code=400, detail="Current label not Idle. Can't mark KPI's as Active.")

    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/trial/{trial_id}/finish', tags=["Trial"])
def post_data_finish(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Receive finish request and forward it to executor."""
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            if engine.set_executor_state_force('UpdateStatusStopping'):
                return {"message": "State change registered"}
            raise HTTPException(status_code=400, detail="Executor not ready for state change.")
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.get('/trial/{trial_id}/status', tags=["Trial"])
def get_engine_state(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Get executor status and state."""
    engines = run_scheduler.get_executor_engine_instances()
    for engine in engines:
        if engine.id == trial_id:
            status = engine.get_executor_status()
            state = engine.get_executor_state()
            return {"message": "Status: " + status + " State: " + state}
    raise HTTPException(status_code=400, detail="Engine with requested ID does not exist")


@app.post('/debug/trial/schedule-all', tags=['Debug/Trial scheduling'])
def schedule_all_trials_from_trial_registry(api_key: APIKey = Depends(get_key)):
    """Fetch all trial ids and start times from Trial registry. Schedule trials as jobs."""
    success, message = run_scheduler.fetch_all_trials()
    if success:
        return {"message": message}
    raise HTTPException(status_code=400, detail="Failed to retrieve trials: {}".format(message))


@app.post('/debug/trial/{trial_id}/schedule', tags=['Debug/Trial scheduling'])
def schedule_a_trial_from_trial_registry_with_trial_id(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Fetch trial start time based on trial id from Trial registry. Schedule trial as job."""
    success, message = run_scheduler.fetch_trial(trial_id=trial_id)
    if success:
        return {"message": message}
    raise HTTPException(status_code=400, detail="Failed to retrieve trial start time: {}".format(message))


@app.post('/debug/trial/schedule', tags=['Debug/Trial scheduling'])
def schedule_trial_with_trial_id_and_start_time(trial: TrialItem, api_key: APIKey = Depends(get_key)):
    """Add trial scheduling as a new job to Scheduler."""
    # Check valid start_date format
    try:
        datetime.datetime.strptime(trial.start_time, "%Y-%m-%dT%H:%M:%S%z")
    except Exception as date_format_exception:
        raise HTTPException(status_code=400, detail="Invalid start time: {}. Start time must be provided in UTC "
                                                    "format: yyyy-mm-ddThh:mm:ss+zz:00. "
                                                    "Example: 2021-02-09T15:12:20+02:00".format(trial.start_time)) \
            from date_format_exception

    # Check that an Engine instance with the given trial ID does not already exist
    current_engine_instances = run_scheduler.get_executor_engine_instances()
    for engine in current_engine_instances:
        if engine.id == trial.trial_id:
            raise HTTPException(status_code=400,
                                detail="Executor Engine with ID: {} already exists.".format(trial.trial_id))

    # Try and add as a scheduled job
    if run_scheduler.add_new_job(trial.start_time, trial.trial_id):
        return {"message": "Trial scheduling added with trial ID: {}".format(trial.trial_id)}
    raise HTTPException(status_code=400, detail="Trial scheduling with ID: {} already exists.".format(trial.trial_id))


@app.delete('/debug/trial/{trial_id}/schedule', tags=['Debug/Trial scheduling'])
def delete_scheduled_trial(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Remove an existing trial scheduling (job) from Scheduler."""
    if run_scheduler.remove_job(trial_id):
        return {"message": "Trial scheduling removed with trial ID: {}".format(trial_id)}
    raise HTTPException(status_code=400, detail="Trial scheduling with ID: {} does not exist.".format(trial_id))


@app.delete('/debug/engine/{trial_id}', tags=['Debug/Trial execution'])
def delete_engine_instance(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Remove an existing Engine instance."""
    current_engine_instances = run_scheduler.get_executor_engine_instances()
    for engine in current_engine_instances:
        if engine.id == trial_id:
            if run_scheduler.remove_engine_instance(trial_id=trial_id):
                return {"message": "Engine instance removed with trial ID: {}".format(trial_id)}
    raise HTTPException(status_code=400, detail="Engine instance with trial ID: {} does not exist.".format(trial_id))


@app.post('/debug/engine/{trial_id}/restore', tags=['Debug/Trial execution'])
def restore_engine_instance(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Restore an Engine instance."""
    current_engine_instances = run_scheduler.get_executor_engine_instances()
    for instance in current_engine_instances:
        if instance.id == trial_id:
            if run_scheduler.restore_engine_instance(trial_id):
                return {"message: Engine instance restored for trial ID: {}".format(trial_id)}
            raise HTTPException(status_code=500,
                                detail="Failed to restore the Engine instance with ID: {}".format(trial_id))
    raise HTTPException(status_code=404,
                        detail="Engine instance with trial ID: {} does not exist.".format(trial_id))


@app.post('/debug/add-heartbeat', tags=['Debug/Heartbeat'])
def post_heartbeat(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Post heartbeat."""
    run_scheduler.heartbeat_handler.create_heartbeat_instance(trial_id)
    return {"message": "Heartbeat added with trial ID: {}".format(trial_id)}


@app.delete('/debug/heartbeat/{trial_id}', tags=['Debug/Heartbeat'])
def delete_heartbeat_instance(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Remove an existing Heartbeat instance."""
    current_heartbeat_instances = run_scheduler.get_heartbeat_instances()
    for heartbeat in current_heartbeat_instances:
        if heartbeat.id == trial_id:
            if run_scheduler.remove_heartbeat_instance(trial_id=trial_id):
                return {"message": "Heartbeat instance removed with trial ID: {}".format(trial_id)}
    raise HTTPException(status_code=400, detail="Heartbeat instance with trial ID: {} does not exist.".format(trial_id))


@app.post('/token/{trial_id}', tags=['Token'])
def post_token(trial_id: str, api_key: APIKey = Depends(get_key)):
    """Create token for callbacks."""
    token = create_token_with_id(SECRET, trial_id)
    TOKENS.append(token)
    return {"Authorization": str(token)}


@app.delete('/token/{trial_id}', tags=['Token'])
def delete_token(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Delete token from LCM"""
    TOKENS.remove(api_key)
    return {"message": "Success"}


@app.get('/token/{trial_id}', tags=['Token'])
def test_token(trial_id: str, api_key: APIKey = Depends(get_key_callback)):
    """Test endpoint for token auth."""
    decode_token(SECRET, api_key, trial_id)
    return {"message": "Success"}


if __name__ == "__main__":
    run_scheduler.set_logging()
    run_scheduler_handler_thread = Thread(target=run_scheduler.run_scheduler())
    run_scheduler_handler_thread.start()
    run_heartbeat_handler_thread = Thread(target=run_scheduler.run_heartbeat_handler())
    run_heartbeat_handler_thread.start()
    uvicorn.run(app, host="0.0.0.0", port=5000)
