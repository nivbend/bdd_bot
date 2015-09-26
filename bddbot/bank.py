"""Store banks' contents (feature test, scenarios, etc.)."""

import socket
from abc import ABCMeta, abstractmethod, abstractproperty
from xmlrpclib import ServerProxy
from .parser import parse_bank
from .errors import BotError

class ConnectionError(BotError):
    """An error on a remote operation."""
    def __init__(self, operation):
        super(ConnectionError, self).__init__("Failed on remote '{:s}'".format(operation))
        self.operation = operation

class BaseBank(object):
    """Access parts and aspects of feature bank/s."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_fresh(self):
        """Return True if no scenario was dealt yet.

        This returns False if there aren't any scenarios.
        """

    @abstractmethod
    def is_done(self):
        """Return True if all scenarios in the bank were dealt.

        This also returns True if there aren't any scenarios.
        """

    @abstractproperty
    def output_path(self):
        """The feature's path to write to."""

    @abstractproperty
    def header(self):
        """Return anything up the beginning of the feature (comments, etc.)."""

    @abstractproperty
    def feature(self):
        """Return the feature text and anything up to the first scenario (including the feature's
        description and the Background section)."""

    @abstractmethod
    def get_next_scenario(self):
        """Get the next scenario which wasn't dealt yet.

        This has the effect of marking the scenario returned as dealt.
        """

class Bank(BaseBank):
    """Holds a bank file's parsed contents and allows access to its scenarios in order."""
    def __init__(self, bank_path):
        try:
            with open(bank_path, "r") as bank_contents:
                (header, feature, scenarios) = parse_bank(bank_contents.read())
        except IOError:
            raise BotError("Couldn't open features bank '{:s}'".format(bank_path))

        self.__output_path = bank_path.replace("bank", "feature")
        self.__header = header
        self.__feature = feature
        self.__scenarios = [(False, scenario) for scenario in scenarios]

        # Ensure output path's extension is 'feature'.
        if not self.__output_path.endswith(".feature"):
            self.__output_path += ".feature"

    def is_fresh(self):
        if not self.__scenarios:
            return False

        return not any(was_dealt for (was_dealt, _) in self.__scenarios)

    def is_done(self):
        return all(was_dealt for (was_dealt, _) in self.__scenarios)

    @property
    def output_path(self):
        return self.__output_path

    @property
    def header(self):
        return self.__header

    @property
    def feature(self):
        return self.__feature

    def get_next_scenario(self):
        for i in xrange(len(self.__scenarios)):
            (was_dealt, scenario) = self.__scenarios[i]

            if not was_dealt:
                self.__scenarios[i] = (True, scenario)
                return scenario

        # No more scenarios.
        return None

class RemoteBank(BaseBank):
    """Access banks over a remote connection."""
    def __init__(self, client, host, port):
        address = "http://{host}:{port:d}".format(host = host, port = port)
        self.__proxy = ServerProxy(address)
        self.client = client

    def is_fresh(self):
        try:
            return self.__proxy.is_fresh(self.client)
        except socket.error:
            raise ConnectionError("is_fresh")

    def is_done(self):
        try:
            return self.__proxy.is_done(self.client)
        except socket.error:
            raise ConnectionError("is_done")

    @property
    def output_path(self):
        try:
            return self.__proxy.get_output_path(self.client)
        except socket.error:
            raise ConnectionError("output_path")

    @property
    def header(self):
        try:
            return self.__proxy.get_header(self.client)
        except socket.error:
            raise ConnectionError("header")

    @property
    def feature(self):
        try:
            return self.__proxy.get_feature(self.client)
        except socket.error:
            raise ConnectionError("feature")

    def get_next_scenario(self):
        try:
            return self.__proxy.get_next_scenario(self.client)
        except socket.error:
            raise ConnectionError("get_next_scenario")
