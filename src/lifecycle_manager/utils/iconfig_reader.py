# © 2021 Nokia
#
# Licensed under the Apache license 2.0
# SPDX-License-Identifier: Apache-2.0

"""Abstract class for handling of reading and storing config information."""
from abc import ABC, abstractmethod


class IConfig(ABC):
    """Abstract class for reading configuration from file."""
    def __init__(self, config_file, config_name):
        """
        Initialize Configparser from configparser-library:
        self._config_parser = configparser.ConfigParser()

        Initialize reading from the config file.
        A section header name within a config.ini-file is passed to the constructor.
        self._config_parser.read(config_name)

        Initialize needed variables for the config file contents.
        """
        self._config_file = config_file
        self._config_name = config_name
        # Read the config file.
        # self.read_config()

    @property
    def config_name(self):
        """Getter for configuration name."""
        return self._config_name

    # Implement properties (getters) for each variable.
    # E.g.:
    # @property
    # @abstractmethod
    # def variable_name(self):
        # return self._variable_name

    @abstractmethod
    def read_config(self):
        """Read the configuration from the file.
        Implement needed variables, e.g.:
        try:
            logging.info('Reading configuration from file.')
            self._variable_name = self._config_parser[self._config_name]['variable_name']
        except Exception as e:
            logging.error("Cannot parse configuration from file: " + str(e))
            return None
        """
