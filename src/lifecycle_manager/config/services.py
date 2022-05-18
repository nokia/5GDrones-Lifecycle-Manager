# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

# Configure URL:s and authentication credentials here
from pydantic import BaseSettings
from lifecycle_manager.api_customization import API_KEY
class Settings(BaseSettings):
    """Set your preferences here."""

    # Executor TLS
    """ WARNING! Setting disable_cert_verification to True will open your TLS traffic to Man in the middle attacks.
    This negates the whole purpose of TLS traffic. Set it to True only for DEBUGGING purposes."""

    disable_cert_verification = False  # Keep this set to False. Read warning above.
    ca_bundle_path = "/etc/ssl/certs/ca-certificates.crt"  # Path set up for docker usage. No need to change, unless you are not using Docker.

    # Executor
    disable_vnf = True  # Default True to skip vnf requests

    # Facilites mapping
    facilities = {
        "EUR": "eurecom",
        "OULU": "5gtn",
        "AALTO": "XN",
        "NCSRD": "test"
    }

    # Services
    lcm = {
        "url": "http://localhost:5000",
        "username": "",
        "password": "",
        "apikey": API_KEY,
        "token": False
    }
    trial_enforcement = {
        "url": "http://localhost:5001",
        "username": "",
        "password": "",
        "apikey": "",
        "token": False
    }
    trial_repository = {
        "url": "http://localhost:5001",
        "username": "",
        "password": "",
        "apikey": "",
        "token": False
    }
    kpi_monitoring = {
        "url": "http://localhost:5001",
        "username": "",
        "password": "",
        "apikey": "",
        "token": True,
        "auth_url": "http://localhost:5001/monitoring/token",
        "token_payload": {"grant_type": "client_credentials", "client_id": "test", "client_secret": "test"}
    }
    abstraction_layer = {
        "url": "http://localhost:5001",
        "port": 5000,
        "username": "test",
        "password": "test",
        "interval": 0,
        "apikey": "",
        "token": False
    }