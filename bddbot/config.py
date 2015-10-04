"""Encapsulate configuration properties."""

from ConfigParser import SafeConfigParser as ConfigParser
from .errors import BotError

CONFIG_FILENAME = "bddbot.cfg"
TEST_COMMAND = ["behave", ]

class ConfigError(BotError):
    # pylint: disable=missing-docstring
    pass

class BotConfiguration(object):
    """Load configuration from file or return default values."""
    def __init__(self, filename = None):
        config = ConfigParser()

        if not filename:
            filename = CONFIG_FILENAME

        try:
            with open(filename, "r") as handle:
                config.readfp(handle, filename)
        except IOError:
            pass

        self.__banks = _get_banks(config)
        self.__tests = _get_tests(config)

    @property
    def banks(self):
        """Features bank paths."""
        return self.__banks

    @property
    def tests(self):
        """The commands to run BDD tests with.

        Test commands are generated as a list of command and arguments, the kind the subprocess
        module can later take (for example, `["behave", "--no-multiline", "--format=progress", ]`).
        """
        return self.__tests

def _get_banks(config):
    """get the feature banks' paths from configuration."""
    if not config.has_option("paths", "bank"):
        return []

    paths = config.get("paths", "bank").splitlines()
    if not paths:
        raise ConfigError("No features banks specified")

    # Return non-empty paths.
    return [path for path in paths if path]

def _get_tests(config):
    """get the test commands from configuration."""
    if not config.has_option("test", "run"):
        return [TEST_COMMAND, ]

    # Return non-empty commands.
    commands = config.get("test", "run").splitlines()
    return [command.split() for command in commands if command]
