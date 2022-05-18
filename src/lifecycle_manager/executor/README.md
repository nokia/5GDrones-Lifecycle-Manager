# ExecutionEngine
Please configure /src/lifecycle_manager/config/services.py with addresses to your trial components and credentials.

## Communication
This component communicates with other services of the trial engine. It runs through a predetermined list of requests to complete a trial. See trial sequence diagrams for detailed information.

## Callback authentication
For requests that trigger callbacks towards LCM. Executor provides an Authentication token in request body.
Use this token in callback request headers or cookies to authenticate the request.
example: {"Authorization: <token/key>} 

## Logs
If a failure occurs in the executor, logs are available in the container folder /code/logs .
Logs include all responses and executor parameters.

## Known limitations
VNF requests are not developed and by default disabled. 

If you encounter issues, contact LCM team.


# Engine
Thread. Provides needed functionality and interfaces to handle executor state machines.

Creates Executor and ProcessCheck Threads automatically.
  
### Process check thread
Thread. Monitors the status of executor. 

### Executor
Thread. State machine. Runs code according to different states and moves to the next. Waits for signals from the engine, where needed.
Execution is started immediately as this thread starts.

## Engine usage

Create a instance for each executor (Done in scheduler):
- `engine = Engine(id, services)` where `id` is a trial id string and `services` a python class that contains the adrresses for the components that the executor connects to.

Start the engine:
- `engine.start()` This starts event waiting thread.


Set execute event to start the state machine:
- `engine.set_execute_event()` This starts executor and process check threads. 


When the executor is waiting for signals from the engine the the next state can be provided with:
- `engine.set_executor_state(<your_state_here>)` This function returns `True` if state changes and `False` otherwise

Engine can be stopped with:
- `engine.set_stop_event()` This signals the engine to stop executor, processcheck and engine. After this you can `engine.join()` the thread.


### Debug/other features

All the response codes and json bodies can be obtained with:
-`engine.get_executor_responses()`

If the executor fails:
- The flag `engine._failed` is set to `True`
- Executor state and information has been backed up automatically.
- `engine.restore()` Restores backed up state to a new executor thread and starts it. `engine._failed` is set to `False`


