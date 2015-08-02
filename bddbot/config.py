"""Encapsulate configuration properties."""

import yaml

DEFAULT_CONFIG_FILENAME = ".bddbotrc"
DEFAULT_TEST_COMMAND = "behave"

class BotConfiguration(object):
    """Load configuration from file or return default values."""
    # pylint: disable=too-few-public-methods
    def __init__(self, filename = None):
        if not filename:
            filename = DEFAULT_CONFIG_FILENAME

        try:
            with open(filename, "rb") as config:
                contents = config.read()
            self.__parameters = yaml.load(contents)
        except IOError:
            self.__parameters = None

        if not self.__parameters:
            self.__parameters = {}

    @property
    def test_commands(self):
        """Generate the commands to run BDD tests with."""
        commands = self.__parameters.get("test_command", DEFAULT_TEST_COMMAND)

        if not commands:
            yield DEFAULT_TEST_COMMAND.split()

        elif isinstance(commands, str):
            yield commands.split()

        else:
            for command in commands:
                yield command.split()