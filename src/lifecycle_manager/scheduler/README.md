# LCM: Scheduler

## Overview

Scheduler is one of the two main components in Lifecycle Manager. The main purpose for Scheduler is to start and perform
scheduled jobs that are utilized to trigger activities in Execution Engine. Scheduler is also used to route requests
that come to the LCM API. The actual LCM activities are performed within Executor Engine.

In 5G!Drones, Scheduler handles scheduling of trials using jobs. Actual activities that are performed by LCM are 
managed and executed in Execution Engine.

## What's new? - Current functionality overview (v1.0.0)

### Updated API endpoints

The Swagger documentation has been updated, and a new endpoint has been added to support restoring an Engine instance in case of a failure in trial setup or execution.

See sections **Functionality/Controlling Scheduler** and **How to use**.

### Functionality

In the current version of Scheduler (LCM v0.1.1), the functionality of Scheduler includes:
- Scheduling a trial in one of the two ways:
    1. Retrieving trial IDs and start times for all trials available in Trial registry
    2. Retrieving trial start time for a trial with given trial ID from Trial registry
    3. Providing trial ID and start time directly to Scheduler via LCM API
- Removal of scheduled trials
    - Scheduler handles scheduling of trials via jobs. A job is identified by the trial id of the trial which 
      Scheduler is scheduling. If needed, these jobs can be removed via the LCM API.
- Restoring Executor Engine instances
    - If a failure situation is faced during LCM activities in an Executor Engine instance, the instance can be restored
      from the latest saved point of execution. The execution of activities continues from that point on.
- Removal of Executor Engine instances
    - Actual LCM activities are performed in Engine instances. An Engine instance is identifiable by the trial id of 
      the trial which Engine instance is handling. If needed, Engine instances can be removed via the LCM API.

## Dependencies to other 5G!Drones components

In the current version of LCM (v0.1.1), Scheduler communicates with Trial registry by retrieving trial start 
times for either all of the available trials, or for a specific trial based on the given trial ID. 

The current implementation has been tested against a dummy API that mimics the endpoints and schemas provided by the 
current implementation Trial registry (5G!Drones registry API).

As presented in the current 5G!Drones registry API implementation, the endpoints utilized by Scheduler are:
- /trial/
    - Scheduler parses variables *id* and *start_time* from the response for each available trial
    - Endpoint returns a list of json-objects, in which an object represents one trial. 
- /trial/{trial_id}/
    - Trial ID is passed to the endpoint by Scheduler. Variable *start_time* is parsed from the response
    - Endpoint returns an json-object that represents one trial.
  
The schema of the trial objects is as follows:
```
{
  ...
  "id": string
  ...
  "start_time": string (UTC format: yyyy-mm-ddThh:mm:ss+zz:00)
  ...
}
```
where ```...``` denotes that the object includes other variables other than ``id`` and ``start_time``, but Scheduler 
will only parse and utilize these two variables.

Therefore, if Trial registry is not available, LCM can be tested against a dummy API that has the following 
characteristics:
- endoint ``/trial/``
  - return a list of trial objects
  - E.g:
```
[
{
  "id": "test_trial_id_1",
  "start_time": string (UTC format: yyyy-mm-ddThh:mm:ss+zz:00)
},
{
  "id": "test_trial_id_2",
  "start_time": string (UTC format: yyyy-mm-ddThh:mm:ss+zz:00)
}
]
```

- endpoint ``/trial/{trial_id}/``
  - returns a trial object, the id of which matches the given trial id
  - E.g.
```
{
  "id": "test_trial_id_1",
  "start_time": string (UTC format: yyyy-mm-ddThh:mm:ss+zz:00)
}
```

Specify the Trial registry endpoint in the file ``lifecycle_manager/config/services.py``

## Architecture

In this version of LCM (0.1.1), Scheduler consists of the following, separate components:
- SchedulerHandler
- InternalScheduler
- TrialRegistryClient

Messages to the LCM API are routed to Scheduler via RunScheduler (implementation in ``run_scheduler.py``).

## Functionality

### Startup

Starting the LCM instance will start the API (``app.py``) and a RunScheduler instance. In turn, RunScheduler will
initialize a SchedulerHandler instance. 

After startup, the LCM is waiting for API calls.

### Controlling Scheduler

In this version of LCM (0.1.1), the following API endpoints are provided for basic LCM control:
1. Dependent on Trial registry
- /debug/trial/schedule-all [POST]
    - endpoint for instructing Scheduler to retrieve start times for all available trials from Trial registry
    - a request to this endpoint will also trigger scheduling of the retrieved trials
- /debug/trial/{trial_id}/schedule [POST]
    - endpoint for instructing Scheduler to retrieve a specific trial start time from Trial registry based on a trial ID
    - a request to this endpoint will also trigger scheduling the retrieved trial.
  
2. Not dependent on Trial registry
- /debug/schedule-trial [POST]
    - endpoint for adding a scheduled job to schedule a trial
    - trial ID and start time interval must be provided in the request
- /debug/trial/{trial_id}/schedule [DELETE]
    - endpoint for removing a scheduled job/scheduling of a trial
    - trial ID must be provided in the request
- /debud/engine/{trial_id}/restore
    - endpoint for restoring an Engine instance to continue the execution from the latest saved point
    - trial ID must be provided in the request 
- /debug/engine/{trial_id} [DELETE]
    - endpoint for removing an existing Executor Engine instance
    - trial ID must be provided in the request

**NOTE:** For now, these endpoints and related functionalities have been created for debugging purposes and are 
subject to change.

## How to use

### Startup

To start Scheduler activities, follow the LCM setup instructions in the project main README.

Addresses of other components interacting with LCM can be provided via the file 
``lifecycle_manager/config/services.py``. 


### Checking the LCM status

Once the LCM instance has been started, the status of the LCM instance can be checked at any given time from the
endpoint ``/status`` with a ``GET`` request. 

After initial startup when no jobs have been scheduled, the API should return the following:
```
{
  "message": "This is Lifecycle Manager 0.1.1!",
  "Scheduler_status": "Idle",
  "scheduled_trials": "[]",
  "Executor_Engine_instances": "[]",
  "Heartbeat_instances": "[]"
}
```

### Start LCM activities for a trial

To start the LCM activities for a specific trial, Trial ID and trial start time need to be provided to Scheduler. 
This can be done in one of the three ways via the LCM API:
1. Instruct LCM to retrieve start time for a specific trial by providing the trial ID
2. Instruct LCM to retrieve all trial ids and start times from Trial registry
3. Instruct LCM to start scheduling of a trial by providing both the trial ID and start time

### 1. Retrieve start time for a specific trial from Trial registry and schedule the trial

To start LCM activities for a specific trial, LCM can retrieve the start time for the trial with the provided trial ID.

To perform this, provide trial ID to the endpoint ``/debug/trial/{trial_id}/schedule`` with a ``POST`` 
request where:
- trial id (string)

If not using the provided Swagger/OpenAPI interface, the endpoint can be accessed via e.g.:
```
curl -X POST "http://localhost:5000/debug/trial/{trial_id}/schedule" -H  "accept: application/json" -d ""
```

where the address of LCM instance must be given (``http://localhost:5000`` in the example). Replace ``{trial_id}`` 
with the desired Trial ID.

If the trial ID has been provided successfully, Scheduler will send a request to configured Trial registry endpoint. 
If a trial with the provided trial ID is available, Scheduler will parse the variable ```start_time``` from the 
response and schedule LCM activities for the trial based on the start time. The scheduling is performed via a job. 
Once the start time is reached for the trial, Scheduler will call Executor Engine to create an Engine instance and 
begin the actual LCM activities for the trial.

A job can be added if Scheduler does not already have a job scheduled with the same trial ID. Additionally, a job cannot
be added if there already exists an Execution Engine instance with the same trial ID.

If the above is performed successfully, a response similar to the following should be returned:
```
{
  "message": "Trial scheduled with trial ID: test_trial_id"
}
```

If a job to schedule the trial has been added successfully, the status information from the endpoint ```/status``` 
should be similar to the following example:
```
{
  "message": "This is Lifecycle Manager 0.1.1!",
  "Scheduler_status": "Idle",
  "scheduled_jobs": "[<Job (id=test_trial_id name=SchedulerHandler.create_executor_engine_instance)>]",
  "Executor_Engine_instances": "[]"
}
```

### 2. Retrieve all trial ids and start times from Trial registry and schedule the trials

To start LCM activities for all of the trials available in Trial registry, LCM can be instructed to send a request 
to Trial registry.

To perform this, send ``POST`` request to the endpoint ``/debug/trial/schedule-all``.
No request parameters are needed.

If not using the provided Swagger/OpenAPI interface, the endpoint can be accessed via e.g.:

```
curl -X POST "http://localhost:5000/debug/trial/schedule-all" -H  "accept: application/json" -d ""
```

where the address of LCM instance must be given (``http://localhost:5000`` in the example).

If called successfully, Scheduler will send a request to Trial registry to retrieve all 
the available trials and start times. After a successful request, Scheduler will parse trial IDs and start times from 
the response provided by Trial registry. Scheduler will then schedule all of the trials. Scheduling is performed via 
jobs. Once a start time is reached for a trial, Scheduler will call Executor Engine to create an Engine instance and 
begin the actual LCM activities for the trial.

A job can be added if Scheduler does not already have a job scheduled with the same trial ID. Additionally, a job cannot
be added if there already exist an Execution Engine instance with the same trial ID.

If the above is performed successfully, the response should be similar to the following:
```
{
  "message": "Scheduled trials with ids: ['trial_1', 'trial_2']"
}
```

If a job has been added successfully, the status information from the endpoint ```/status``` should be similar to the
following example:
```
{
  "message": "This is Lifecycle Manager 0.1.1!",
  "Scheduler_status": "Scheduled job(s) initiated",
  "scheduled_trials": "[{'id': 'test_trial_id', 'trigger': 'date[2021-03-26 10:00:00 EET]'},
                        {'id': 'test_trial_id_2', 'trigger': 'date[2021-03-26 15:00:00 EET]'}]",
  "Executor_Engine_instances": "[]",
  "Heartbeat_instances": "[]"
}
```

### 3. Provide Trial ID and start time

LCM activities for a trial can be scheduled without retrieving the start time for Trial registry.

To schedule a trial by providing Trial ID and start 
time have to be provided via the API.

Provide the following request body (as .json) to endpoint ``/debug/schedule-trial`` with a ``POST`` request:
```
{
  "trial_id": [string],
  "start_time": [string]
}
```
An example request body:
```
{
  "trial_id": "test_id",
  "start_time": "2021-02-23T07:17:15+02:00"
}
```

**NOTE:** ```start_time``` must be in the following **UTC** format: ``yyyy-mm-ddThh:mm:ss+zz:00``.
For example: ``2021-02-23T07:17:15+02:00``.

If not using the provided Swagger/OpenAPI interface, the endpoint can be accessed via e.g.:
```
curl -X POST "http://localhost:5000/debug/schedule-trial" -H  "accept: application/json" -H  
"Content-Type: application/json" -d "{\"trial_id\":\"[string]\",\"start_time\":\"[string]\"}"
```

where the address of LCM instance must be given (``http://localhost:5000`` in the example).

In ``trial_id\":\"[string]``, replace ``[string]`` with the desired trial ID.

In ``start_time\":\"[string]``, replace ``[string]`` with the desired start date in format 
``yyyy-mm-ddThh:mm:ss+zz:00``, for example: ``2021-02-23T07:17:15+02:00``.

If the parameters have been provided successfully, Scheduler will start a scheduled job that will call creation of
Execution Engine instance once the set time interval has passed.

A job can be added if Scheduler does not already have a job scheduled with the same Trial ID. Additionally, a job cannot
be added if there already exist an Execution Engine instance with the same Trial ID.

If a job has been added successfully, the status information from the endpoint ```/status``` should be similar to the
following example:
```
{
  "message": "This is Lifecycle Manager 0.1.1!",
  "Scheduler_status": "Scheduled job(s) initiated",
  "scheduled_trials": "[{'id': 'test_trial_id', 'trigger': 'date[2021-03-26 10:14:52 EET]'}]",
  "Executor_Engine_instances": "[]",
  "Heartbeat_instances": "[]"
}
```

### 2. Remove a scheduled trial

A scheduled trial is handled as a job in Scheduler. A job can be removed once it has been scheduled and added to job 
store in InternalScheduler.

To remove a scheduled trial, provide Trial ID as a parameter to the endpoint ```/debug/trial/{trial_id}/schedule``` 
with a ``DELETE`` request:
- Trial ID (string)

If not using the provided Swagger/OpenAPI interface, the endpoint can be accessed via:
```
curl -X DELETE "http://localhost:5000/debug/trial/{trial_id}/schedule" -H  "accept: application/json"
```

where the address of the LCM instance must be given (``http://localhost:5000`` in the example).

Replace ``{trial_id}`` with the desired trial ID (string).

If the parameter has been provided successfully, the job will be removed from InternalScheduler and it will not trigger
any further activities. 

### 3. Activities triggered by a scheduled trial

Once the scheduled time of a job has been reached, the Scheduler will call Execution Engine to create an Engine instance
to perform LCM activities for the given trial based on the Trial ID. 

If a scheduled job has been completed and an Execution Engine instance has been created successfully, the status
information from the endpoint ```/status``` should be similar to the following example:
```
{
  "message": "This is Lifecycle Manager 0.1.1!",
  "Scheduler_status": "Idle",
  "scheduled_trials": "[]",
  "Executor_Engine_instances": "[{'ID': 'test_trial_id', 'status': 'active'}]",
  "Heartbeat_instances": "[]"
}
```

### 4. Restore an Engine instance

The restore function is intended for situations where an Engine instance faces a failure during execution of the 
implemented sequences of LCM activities. For example, an Engine instance may fail to communicate with a specific 
target. Once restored, the Engine instance resumes its execution from the latest saved point.

**NOTE:** This is a debugging feature. Once a restore instance request has been sent, LCM will restore the Engine 
instance regardless the Engine state.

To restore an Engine instance, send trial ID as a parameter to the endpoint ```/debug/engine/{trial_id}/restore``` 
where:
- Trial ID (string)

If not using the provided Swagger/OpenAPI interface, the endpoint can be accessed via:
```
curl -X POST "http://localhost:5000/debug/engine/{trial_id}/restore" -H  "accept: application/json"
```

Replace ``{trial_id}`` with the desired trial ID.

The Engine instance will be restored if there exist an Engine instance with the provided trial ID in LCM. If the 
parameter has been provided successfully, the Scheduler will instruct the Engine to restore the Engine instance from
the backup.

### 5. Remove an Engine instance

Once an Engine instance has been created via a scheduled job, it can be removed from LCM.

**NOTE:** This is a debugging feature. Once a remove instance request has been sent, LCM will stop and remove the
instance regardless the Engine state.

To remove an Engine instance, send trial ID as parameter to the endpoint ```/debug/engine/{trial_id}```:
- Trial ID (string)

If not using the provided Swagger/OpenAPI interface, the endpoint can be accessed via:
```
curl -X DELETE "http://localhost:5000/debug/engine/{trial_id}" -H  "accept: application/json"
```

Replace ``{trial_id}`` with the desired trial ID.

The Engine instance will be removed if there exist an Engine instance with the provided trial ID. If the parameter has
been provided successfully, the Scheduler will instruct the Engine to stop the Engine instance thread and join it.
