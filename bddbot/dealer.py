"""Deal scenarios from bank files.

Dealing reads a new scenario every time from a bank file and appends it to the feature
file, as long as all previous scenarios were properly implemented.

Features are written incrementaly from a bank file ("*.bank") to a corrosponding features
file ("*.feature"). So for example, the bank file 'banks/awesome.bank' will be translated to the
feature file 'features/awesome.feature'.
"""
from os.path import dirname
from os import mkdir, getcwd
from subprocess import Popen, PIPE
from collections import OrderedDict
from .bank import Bank
from .config import BotConfiguration, DEFAULT_CONFIG_FILENAME
from .errors import BotError

class Dealer(object):
    """Manage banks of features to dispense whenever a scenario is implemented."""
    def __init__(self, config = DEFAULT_CONFIG_FILENAME):
        self.__config = BotConfiguration(config)
        self.__is_loaded = False
        self.__is_done = False
        self.__banks = OrderedDict()

    @property
    def is_done(self):
        """Return True if no more scenarios are left to deal."""
        return all(bank.is_done() for bank in self.__banks.itervalues())

    def load(self):
        """Load a feature from the bank."""
        if self.__is_loaded:
            return

        for path in self.__config.bank:
            output_path = path.replace("bank", "feature")
            if not output_path.endswith(".feature"):
                output_path += ".feature"

            try:
                with open(path, "rb") as bank_input:
                    self.__banks[output_path] = Bank(bank_input.read())
            except IOError:
                raise BotError("No features bank in {:s}".format(getcwd()))

        self.__is_loaded = True

    def deal(self):
        """Deal a scenario from the bank.

        If this is the first scenario, call _deal_first(). If not, as long as there
        are more scenarios in the bank call _deal_another(). When there are no more scenarios,
        the dealer is 'done'.

        Attempting to deal while the test commands (by default, "behave") fail will raise a
        BotError.
        """
        if not self.__is_loaded:
            self.load()

        # Find the first bank that still has scenarios to deal.
        (path, current_bank) = next(
            ((path, bank) for (path, bank) in self.__banks.iteritems() if not bank.is_done()),
            (None, None))

        if not current_bank:
            # No more features to deal from.
            return

        if current_bank.is_fresh():
            self._deal_first(path, current_bank)
        elif self._are_tests_passing():
            self._deal_another(path, current_bank)
        else:
            raise BotError("Can't deal while there are unimplemented scenarios")

    def _are_tests_passing(self):
        """Verify that all scenarios were implemented using `behave`.

        This is done by calling each testing command (by default, only "behave") in order.
        If any of them fail, the result is False.
        """
        for command in self.__config.test_commands:
            process = Popen(command, stdout = PIPE, stderr = PIPE)
            process.wait()

            # pylint: disable=superfluous-parens
            if (0 != process.returncode):
                return False

        return True

    @staticmethod
    def _deal_first(path, bank):
        """Deal the very first scenario in the bank.

        This will create the feature file and fill it with the feature's text,
        background, etc. It implicitly calls load().
        """
        try:
            mkdir(dirname(path))
        except OSError:
            # Directory exists.
            pass

        try:
            with open(path, "wb") as features:
                features.write(bank.header)
                features.write(bank.feature)
                features.write(bank.get_next_scenario())
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(path))

    @staticmethod
    def _deal_another(path, bank):
        """Deal a new scenario (not the first one)."""
        try:
            with open(path, "ab") as features:
                features.write(bank.get_next_scenario())
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(path))
