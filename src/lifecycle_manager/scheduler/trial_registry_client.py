# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Functionality for performing HTTP requests."""
from datetime import datetime

import logging
import requests

from requests.auth import HTTPBasicAuth

from lifecycle_manager.config.services import Settings


class TrialRegistryClient:
    """Class for HTTP client functionality."""

    def __init__(self):
        self.settings = Settings()
        self.service = self.settings.trial_repository

    @staticmethod
    def parse_all_trials_information(response):
        """Parse response from Trial APIs GET /trial/."""
        try:
            trial_ids_start_times = []
            for trial in response:
                try:
                    start_time_str = trial['start_time']
                    start_time_dt = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ")
                    if start_time_dt > datetime.utcnow():
                        trial = {'trial_id': str(trial['id']),
                                 'start_time': start_time_str}
                        trial_ids_start_times.append(trial)
                except Exception as excep:
                    logging.warning("Failed to parse ID from Trial registry: {}".format(excep))
            return trial_ids_start_times, ""
        except Exception as excep:
            return None, "Failed to parse reply from Trial registry: {}".format(excep)

    @staticmethod
    def parse_trial_start_time(response):
        """Parse response from Trial APIs GET /trial/{trial_id}."""
        try:
            start_time_str = response['start_time']
            start_time_dt = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%SZ")
            if start_time_dt < datetime.utcnow():
                return None, "Trial start time in the past. Skipping scheduling."
            return start_time_str, ""
        except Exception as excep:
            return None, "Failed to parse reply from Trial registry: {}".format(excep)

    def get_all_trial_ids_and_start_times(self):
        """Get trial IDs and start times of all available trials from Trial registry."""
        logging.info("Sending GET request to %s/trial/", self.service["url"])
        try:
            if self.service["apikey"] != "":
                auth = HTTPBasicAuth('apikey', self.service["apikey"])
            else:
                auth = HTTPBasicAuth(self.service["username"], self.service["password"])

            if self.service["url"].startswith("https"):
                if not self.settings.disable_cert_verification:
                    cert = self.settings.ca_bundle_path
                else:
                    cert = None
            else:
                cert = None

            response = requests.get(self.service["url"] + "/trial/", auth=auth,
                                    verify=cert, timeout=30)

            if response.status_code == 200:
                response_dict = response.json()
                trial_ids_start_times, message = self.parse_all_trials_information(response_dict)
                if trial_ids_start_times:
                    return True, message, trial_ids_start_times
                return False, "No future trials defined in repository. No need to schedule.", trial_ids_start_times
            message = "Trial registry responded with: {}.".format(response.content)
            logging.warning(message)
            return False, message, None

        except (requests.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema) as excep:
            message = "Failed to connect to Trial registry at: {}: {}".format(self.service["url"], excep)
            logging.warning(message)
            return False, message, None

    def get_trial_start_time(self, trial_id):
        """Get start time for a specific trial based on trial ID from Trial registry."""
        logging.info("Sending GET request to %s/trial/%s/", self.service["url"], trial_id)
        try:
            if self.service["apikey"] != "":
                auth = HTTPBasicAuth('apikey', self.service["apikey"])
            else:
                auth = HTTPBasicAuth(self.service["username"], self.service["password"])

            if self.service["url"].startswith("https"):
                if not self.settings.disable_cert_verification:
                    cert = self.settings.ca_bundle_path
                else:
                    cert = None
            else:
                cert = None

            response = requests.get(self.service["url"] + "/trial/" + trial_id + "/",
                                    verify=cert, auth=auth, timeout=30)

            if response.status_code == 200:
                response_dict = response.json()
                start_time, message = self.parse_trial_start_time(response_dict)
                if start_time:
                    return True, message, start_time
                return False, message, start_time
            message = "Trial registry responded with: {}.".format(response.content)
            logging.warning(message)
            return False, message, None

        except (requests.ConnectionError, requests.exceptions.InvalidURL, requests.exceptions.InvalidSchema) as excep:
            message = "Failed to connect to Trial registry at: {}: {}".format(self.service["url"], excep)
            logging.warning(message)
            return False, message, None
