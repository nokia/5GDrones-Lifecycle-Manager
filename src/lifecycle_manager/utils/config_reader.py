# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Module for reading configuration for Scheduler."""
import configparser
import logging

from lifecycle_manager.utils.iconfig_reader import IConfig


class Config(IConfig):
    """Implementation of IConfig for configuration."""
    def __init__(self, config_file, config_name):
        super().__init__(config_file, config_name)
        self._config_parser = None
        self.initialize_configparser(config_file)
        self.read_config()

    def initialize_configparser(self, config_file):
        """Initialize the ConfigParser-object."""
        try:
            self._config_parser = configparser.ConfigParser(allow_no_value=True)
            self._config_parser.read_file(open(config_file, 'r'))
        except FileNotFoundError as config_file_not_found_error:
            logging.exception("Unable to read configuration: %s", str(config_file_not_found_error))
            raise FileNotFoundError from config_file_not_found_error

    def read_config(self):
        """Read the configuration from the file."""
        try:
            logging.info('Reading configuration from file.')
        except KeyError as key_exception:
            logging.exception("Cannot parse configuration from file: %s", str(key_exception))
            raise KeyError from key_exception

