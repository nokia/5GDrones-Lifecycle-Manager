# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""States for statemachine."""

import ast
import logging
import time
from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth


def form_and_send(executor, _type, service, _endpoint, _data=None, url_payload=None, headers=None):
    """Create and send requests. Return response object."""
    response = None
    auth = None
    if not headers:
        if not service["apikey"] == "":
            headers = {"Authorization": service["apikey"]}
        elif not service["username"] == "" and not service["token"]:
            auth = HTTPBasicAuth(service["username"], service["password"])
        elif service["token"]:
            try:
                headers = {'Content-type': 'application/x-www-form-urlencoded'}
                response = requests.post(service["auth_url"], headers=headers, data=service["token_payload"])
                auth_token = response.json()["access_token"]
                headers = {'Authorization': 'bearer ' + auth_token}
            except Exception as request_error:
                logging.getLogger('__executor__').error("Getting authentication token failed: %s") % str(request_error)
                return None

    if service["url"].startswith("https"):
        if not executor.services.disable_cert_verification:
            cert = executor.services.ca_bundle_path
        else:
            cert = False
    else:
        cert = False

    logging.getLogger('__executor__').info(service["url"] + _endpoint)
    if _type == 'Get':
        response = requests.get(service["url"] + _endpoint, auth=auth,
                                verify=cert, timeout=30, headers=headers)
    if _type == 'Post':
        response = requests.post(service["url"] + _endpoint, auth=auth, verify=cert,
                                 json=_data, params=url_payload, timeout=30, headers=headers)
    if _type == 'Put':
        response = requests.put(service["url"] + _endpoint, auth=auth, verify=cert,
                                json=_data, params=url_payload, timeout=30, headers=headers)
    if _type == 'Delete':
        response = requests.delete(service["url"] + _endpoint, auth=auth, json=_data,
                                   verify=cert, params=url_payload, timeout=30, headers=headers)

    logging.getLogger('__executor__').debug(response.status_code)
    if response is not None:
        return response
    logging.getLogger('__executor__').error("No response object to return.")
    return None


def make_body(trial_info: dict, _keys: list):
    """Create and return dict for request body."""
    temp = {}
    for key in _keys:
        temp[key] = trial_info[key]
    return temp


class State:
    """State class parent."""
    def run(self, executor):
        """State code."""
        assert 0, "not implemented"


class GetCallbackToken(State):
    """Get token for callback authentication."""
    def run(self, executor):
        response = form_and_send(executor, 'Post', executor.services.lcm, '/token/' + executor.get_id)
        try:
            data = response.json()
            executor.set_token(data["Authorization"])
            return 0, 'GetTrialInfo'
        except KeyError:
            logging.error("Failed getting token for callbacks.")
        return 1, ''


class RemoveCallbackToken(State):
    """Clean up token from LCM."""
    def run(self, executor):
        response = form_and_send(executor, 'Delete', executor.services.lcm, '/token/' + executor.get_id,
                                 None, None, {"Authorization": executor.get_token})
        if not response.status_code == 200:
            logging.error("Failed removing token for callbacks. Stale token remains.")
        return 0, 'Finish'


class GetTrialInfo(State):
    """Initialization state."""
    def run(self, executor):
        """State code."""
        executor.set_status('Running')
        response = form_and_send(executor, 'Get', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', executor.get_trial_information)
        executor.add_response('GetTrialInfo', response.status_code)
        if response.status_code == 200:
            temp = {}
            temp['target'] = "dummy"
            temp['trialID'] = response.json()["id"]
            temp['facility'] = executor.services.facilities[response.json()["facility"]]
            temp['kpis'] = response.json()["kpis"]
            temp['name'] = response.json()["name"]
            temp['KpiComponents'] = []
            temp['MeasurementJob'] = {}
            temp['DeployedSlice'] = {}
            executor.update_trial_info(temp)
            return 0, 'SliceDeployment'
        return 1, None


class Waiting(State):
    """Waiting state."""
    def run(self, executor):
        """State code."""
        return 0, 'Waiting'


class SliceDeployment(State):
    """Deploy slice state."""
    def run(self, executor):
        """State code."""
        info = executor.get_trial_information
        info_response = form_and_send(executor, 'Get', executor.services.trial_repository, '/trial/' +
                                      executor.get_id + '/')
        if info_response.status_code == 200 and info_response.json()["status"] == "APPROVED":
            nst = {'nst': ast.literal_eval(info_response.json()["nst"])}
            data = {"trialID": info["trialID"], 'NST': nst,
                    "facility": info["facility"], "Authorization": executor.get_token}
            url_payload = {'callback_url': executor.services.lcm['url'] + '/trial/' +
                           executor.get_id + '/callback/slice'}
            response = form_and_send(executor, 'Post', executor.services.trial_enforcement,
                                     '/sliceDeployment', data, url_payload)
            executor.add_response('SliceDeployment', response.status_code)
            executor.update_dict_in_info('DeployedSlice', response.json())
            if response.status_code == 424:
                return 1, None
            if response.status_code == 422:
                return 1, None
            if response.status_code == 409:
                return 1, None
            if response.status_code == 201:
                return 0, 'Waiting'
        return 1, None


class UpdateDeploymentSlice(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        temp = {"status": "ACTIVATING_1"}
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', temp)
        executor.add_response('UpdateDeploymentSlice', response.status_code)
        if response.status_code == 204:
            if executor.services.disable_vnf:
                return 0, 'EnforceUavPlan'
            return 0, 'CloudVnfOnboarding'
        return 1, None


class CloudVnfOnboarding(State):
    """CloudVnfOnboarding."""
    def run(self, executor):
        """State code."""
        data = {"Authorization": executor.get_token}
        url_payload = {'callback_url': executor.services.lcm['url'] + '/trial/' +
                       executor.get_id + '/callback/cloudvnfboarding'}
        response = form_and_send(executor, 'Post', executor.services.trial_enforcement,
                                 '/vnf/cloud/boarding?trialID=' + executor.get_id, data, url_payload)
        executor.add_response('CloudVnfOnboarding', response.status_code)
        if response.status_code == 201:
            return 0, 'Waiting'
        return 1, None


class UpdateCloudVnfBoardingStatus(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        return 0, 'CloudVnfDeployment'


class CloudVnfDeployment(State):
    """CloudVnfDeployment."""
    def run(self, executor):
        """State code."""
        data = {"Authorization": executor.get_token}
        url_payload = {'callback_url': executor.services.lcm['url'] + ':' +
                       str(executor.services.lcm['port']) + '/trial/' +
                       executor.get_id + '/callback/cloudvnfdeployment'}
        response = form_and_send(executor, 'Post', executor.services.trial_enforcement,
                                 '/vnf/cloud/deployment?trialID=' + executor.get_id, data, url_payload)
        executor.add_response('CloudVnfDeployment', response.status_code)
        if response.status_code == 201:
            return 0, 'Waiting'
        return 1, None


class UpdateCloudVnfDeploymentStatus(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        return 0, 'EdgeVnfOnboarding'


class EdgeVnfOnboarding(State):
    """EdgeVnfOnboarding."""
    def run(self, executor):
        """State code."""
        data = {"Authorization": executor.get_token}
        url_payload = {'callback_url': executor.services.lcm['url'] + '/trial/' +
                       executor.get_id + '/callback/edgevnfonboarding'}
        response = form_and_send(executor, 'Post', executor.services.trial_enforcement,
                                 '/vnf/edge/boarding?trialID=' + executor.get_id, data, url_payload)
        executor.add_response('EdgeVnfOnboarding', response.status_code)
        if response.status_code == 201:
            return 0, 'Waiting'
        return 1, None


class UpdateEdgeVnfBoardingStatus(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        return 0, 'EdgeVnfDeployment'


class EdgeVnfDeployment(State):
    """EdgeVnfDeployment."""
    def run(self, executor):
        """State code."""
        data = {"Authorization": executor.get_token}
        url_payload = {'callback_url': executor.services.lcm['url'] + '/trial/' +
                       executor.get_id + '/callback/edgevnfdeployment'}
        response = form_and_send(executor, 'Post', executor.services.trial_enforcement,
                                 '/vnf/edge/deployment?trialID=' + executor.get_id, data, url_payload)
        executor.add_response('EdgeVnfDeployment', response.status_code)
        if response.status_code == 201:
            return 0, 'Waiting'
        return 1, None


class UpdateEdgeVnfDeploymentStatus(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        return 0, 'Start5GresourceTesting'


class Start5GresourceTesting(State):
    """Start5GresourceTesting."""
    def run(self, executor):
        """State code."""
        data = make_body(executor.get_trial_information, ["trialID", "name", "facility", "target"])
        response = form_and_send(executor, 'Post', executor.services.trial_enforcement,
                                 '/tap', data)
        executor.add_response('Start5GresourceTesting', response.status_code)
        if response.status_code == 200:
            return 0, 'EnforceUavPlan'
        return 1, None


class EnforceUavPlan(State):
    """EnforceUavPlan."""
    def run(self, executor):
        """State code."""
        info = executor.get_trial_information
        info_response = form_and_send(executor, 'Get', executor.services.trial_repository, '/trial/' +
                                      executor.get_id + '/')
        if info_response.status_code == 200:
            flight_plan = {'flights': info_response.json()["flights"]}
            data = {"trialID": info["trialID"], "flight_plan": flight_plan}
            response = form_and_send(executor, 'Post', executor.services.trial_enforcement, '/flightplan', data)
            executor.add_response('EnforceUavPlan', response.status_code)
            if response.status_code == 201:
                return 0, 'UpdateUavPlanStatus'
        return 1, None


class UpdateUavPlanStatus(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        temp = {"status": "ACTIVATING_2"}
        executor.update_trial_info(temp)
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', temp)
        executor.add_response('UpdateUavPlanStatus', response.status_code)
        if response.status_code == 204:
            return 0, 'CreateMeasurementJob'
        return 1, None


class CreateMeasurementJob(State):
    """KpisRequest."""
    def run(self, executor):
        """State code."""
        info = executor.get_trial_information
        layer = executor.services.abstraction_layer
        info_response = form_and_send(executor, 'Get', executor.services.trial_repository, '/trial/' +
                                      executor.get_id + '/')
        if info_response.status_code == 200:
            temp = {
                "trialID": info["trialID"],
                "facility": info["facility"],
                "measurement_job": {
                    "auth": {
                        "host": layer["url"],
                        "password": layer["password"],
                        "port": layer["port"],
                        "username": layer["username"],
                    },
                    "interval": layer["interval"],
                    "kpis": info["kpis"],
                    "ns": info["DeployedSlice"]["Slice"]["id"]
                }
            }
            response = form_and_send(executor, 'Post', executor.services.trial_enforcement, '/measurementjobs', temp)
            executor.add_response('CreateMeasurementJob', response.status_code)
            executor.update_dict_in_info('MeasurementJob', response.json())
            if response.status_code == 201:
                return 0, 'SendKpiIdle'
        return 1, None


class SendKpiIdle(State):
    """Send KPI label IDLE."""
    def run(self, executor):
        """State code."""
        info = executor.get_trial_information
        temp = {"TrialID": info["trialID"], "MarkingID": info["trialID"],
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S%z"), "Marking": "Idle"}
        response_trial_id = form_and_send(executor, 'Post', executor.services.kpi_monitoring, '/markKPIData', temp)
        temp["TrialID"] = info["DeployedSlice"]["Slice"]["id"]
        temp["MarkingID"] = info["DeployedSlice"]["Slice"]["id"]
        response_slice_id = form_and_send(executor, 'Post', executor.services.kpi_monitoring, '/markKPIData', temp)
        if response_trial_id.status_code == 200 and response_slice_id.status_code == 200:
            executor.set_kpi_status("Idle")
            return 0, 'UpdateStatusIdle'
        return 1, None


class UpdateStatusIdle(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        temp = {"status": "IDLE"}
        executor.update_trial_info(temp)
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', temp)
        executor.add_response('RequestKpiComponents', response.status_code)
        if response.status_code == 204:
            return 0, 'Waiting'
        return 1, None


class SendKpiActive(State):
    """Send KPI label ACTIVE."""
    def run(self, executor):
        """State code."""
        info = executor.get_trial_information
        temp = {"TrialID": info["trialID"], "MarkingID": info["trialID"],
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S%z"), "Marking": "Active"}
        response_trial_id = form_and_send(executor, 'Post', executor.services.kpi_monitoring, '/markKPIData', temp)
        temp["TrialID"] = info["DeployedSlice"]["Slice"]["id"]
        temp["MarkingID"] = info["DeployedSlice"]["Slice"]["id"]
        response_slice_id = form_and_send(executor, 'Post', executor.services.kpi_monitoring, '/markKPIData', temp)
        if response_trial_id.status_code == 200 and response_slice_id.status_code == 200:
            executor.set_kpi_status("Active")
            return 0, 'UpdateStatusActive'
        return 1, None


class UpdateStatusActive(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        data = {"status": "ACTIVE"}
        executor.update_trial_info(data)
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', data)
        executor.add_response('UpdateStatusActive', response.status_code)
        if response.status_code == 204:
            return 0, 'Waiting'
        return 1, None


class UpdateStatusStopping(State):
    """UpdateConfig."""
    def run(self, executor):
        """State code."""
        data = {"status": "STOPPING"}
        executor.update_trial_info(data)
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', data)
        executor.add_response('UpdateStatusStopping', response.status_code)
        if response.status_code == 204:
            return 0, 'SendKpiFinish'
        return 1, None


class SendKpiFinish(State):
    """Send KPI label FINISHED."""
    def run(self, executor):
        info = executor.get_trial_information
        temp = {"TrialID": info["trialID"], "MarkingID": info["trialID"],
                "Timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S%z"), "Marking": "Finished"}
        response_trial_id = form_and_send(executor, 'Post', executor.services.kpi_monitoring, '/markKPIData', temp)
        temp["TrialID"] = info["DeployedSlice"]["Slice"]["id"]
        temp["MarkingID"] = info["DeployedSlice"]["Slice"]["id"]
        response_slice_id = form_and_send(executor, 'Post', executor.services.kpi_monitoring, '/markKPIData', temp)
        if response_trial_id.status_code == 200 and response_slice_id.status_code == 200:
            executor.set_kpi_status('Finished')
            return 0, 'DeleteMeasurementJob'
        return 1, None


class DeleteMeasurementJob(State):
    """Delete MeasurementJob."""
    def run(self, executor):
        """State code."""
        info = executor.get_trial_information
        temp = {"trialID": info["trialID"],
                "facility": info["facility"]}
        response = form_and_send(executor, 'Delete', executor.services.trial_enforcement,
                                 '/measurementjobs/' + info["MeasurementJob"]["MeasurementID"], temp)
        executor.add_response('DeleteMeasurementJob', response.status_code)
        if response.status_code == 204:
            return 0, 'CloseService'
        return 1, None


class CloseService(State):
    """Close request."""
    def run(self, executor):
        """State code."""
        data = {"Authorization": executor.get_token}
        url_payload = {'callback_url': executor.services.lcm['url'] + '/trial/' +
                       executor.get_id + '/callback/slice'}
        response = form_and_send(executor, 'Delete', executor.services.trial_enforcement,
                                 '/sliceDeployment/' + executor.get_id, data, url_payload)
        executor.add_response('CloseService', response.status_code)
        if response.status_code == 200:
            return 0, 'Waiting'
        return 1, None


class UpdateStatusFinish(State):
    """Update status to finish."""
    def run(self, executor):
        """State code."""
        temp = {"status": "FINISHED"}
        executor.update_trial_info(temp)
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', temp)
        executor.add_response('UpdateStatusFinish', response.status_code)
        if response.status_code == 204:
            return 0, 'RemoveCallbackToken'
        return 1, None


class Finish(State):
    """Finish state."""
    def run(self, executor):
        """State code."""
        time.sleep(2)
        executor.set_status('Finished')
        logging.getLogger('__executor__').debug('Executor reached finish.')
        return 0, None


class Fail(State):
    """Update failure status."""
    def run(self, executor):
        """State code."""
        data = {"status": "FAILED"}
        response = form_and_send(executor, 'Put', executor.services.trial_repository, '/trial/' +
                                 executor.get_id + '/', data)
        executor.add_response('Fail', response.status_code)
        if response.status_code == 204:
            return 0, 'Waiting'
        return 1, None


class FakeRun(State):
    """Fake state for testing."""
    def run(self, executor):
        """State code."""
        time.sleep(1)
        return 0, 'Waiting'


class FakeRunFail(State):
    """Fake state for testing."""
    def run(self, executor):
        """State code."""
        return 1, None


class FakeInit(State):
    """Init."""
    def run(self, executor):
        """State code."""
        executor.set_status('Running')
        time.sleep(2)
        return 0, 'FakeRun'
