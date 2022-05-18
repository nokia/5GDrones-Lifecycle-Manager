# LCM: Heartbeat

Feature is not in use in the current version.
However, this feature can be modified and utilised to different functionality transferring information.

## Overview

Heartbeat is functionality in LCM, which can be used to transfer information periodically.

## Architecture

Heartbeat consists of the components:

- HeartbeatHandler
- Heartbeat


## Functionality

Heartbeat works under the thread, which make it possible to utilise multiple heartbeat instance to transfer data.
Heartbeat is started under run_scheduler module, and the module starts heartbeat_handler module,
which controls all instances of Heartbeat class.


## How to use

Currently, a heartbeat instance can be start using LCM API (It does not have main logic. Must be implemented if the use
case has been defined). Heartbeat has two endpoint for debugging: Start and delete a heartbeat instance.

To start heartbeat instance, send ``POST`` request to the endpoint ``/debug/add-heartbeat`` with  trial ID

To delete the created heartbeat instance, send ``DELETE`` request to the endpoint ``/debug/heartbeat/{trial_id}``.

The status of initialised heartbeat instances can be checked from the endpoint ```/status```.
It should be similar to the following example, when one heartbeat instance running in the application:

```
{
  "message": "This is Lifecycle Manager 0.1.1!",
  "Scheduler_status": "Idle",
  "scheduled_trials": "[]",
  "Executor_Engine_instances": "[]",
  "Heartbeat_instances": "[<Heartbeat(Thread-7, started daemon 2220)>]"
}
```