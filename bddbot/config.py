"""Encapsulate configuration properties."""

import yaml

DEFAULT_CONFIG_FILENAME = "bddbot.yml"
DEFAULT_BANK_PATH = "banks/all.bank"
DEFAULT_TEST_COMMAND = "behave"

class BotConfiguration(object):
    """Load configuration from file or return default values."""
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
    def bank(self):
        """Return the features bank's path."""
        value = self.__parameters.get("bank", DEFAULT_BANK_PATH)

        if not value:
            value = DEFAULT_BANK_PATH

        if isinstance(value, str):
            yield value
        else:
            for path in value:
                yield path

    @property
    def test_commands(self):
        """Generate the commands to run BDD tests with.

        Test commands are generated as a list of command and arguments, the kind the subprocess
        module can later take (for example, `["behave", "--no-multiline", "--format=progress", ]`).
        """
        commands = self.__parameters.get("test_command", DEFAULT_TEST_COMMAND)

        if not commands:
            yield DEFAULT_TEST_COMMAND.split()

        elif isinstance(commands, str):
            yield commands.split()

        else:
            for command in commands:
                yield command.split()
