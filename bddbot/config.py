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

        config.read([filename, ])

        self.__banks = _get_banks(config)
        self.__tests = _get_tests(config)
        self.__host = _get_host(config)
        self.__port = _get_port(config)

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

    @property
    def host(self):
        """Server's hostname (None if undefined)."""
        return self.__host

    @property
    def port(self):
        """Server's port (None if undefined)."""
        return self.__port

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

def _get_host(config):
    """Get the server's hostname from configuration."""
    if not config.has_option("server", "host"):
        return None

    host = config.get("server", "host")
    return host

def _get_port(config):
    """Get the server's port from configuration."""
    if not config.has_option("server", "port"):
        return None

    port = config.getint("server", "port")
    return port
