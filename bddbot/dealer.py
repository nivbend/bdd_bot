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
from .bank import split_bank
from .config import BotConfiguration, DEFAULT_CONFIG_FILENAME
from .errors import BotError

class Dealer(object):
    """Manage banks of features to dispense whenever a scenario is implemented."""
    def __init__(self, config = DEFAULT_CONFIG_FILENAME):
        self.__config = BotConfiguration(config)
        self.__is_loaded = False
        self.__is_done = False
        self.__output_path = ""
        self.__header = ""
        self.__feature = ""
        self.__scenarios = []

    @property
    def is_done(self):
        """Return True if no more scenarios are left to deal."""
        return self.__is_done

    def load(self):
        """Load a feature from the bank."""
        if self.__is_loaded:
            return

        try:
            with open(self.__config.bank, "rb") as bank_input:
                (self.__header, self.__feature, scenarios) = split_bank(bank_input.read())
        except IOError:
            raise BotError("No features bank in {:s}".format(getcwd()))

        output_path = self.__config.bank.replace("bank", "feature")
        if not output_path.endswith(".feature"):
            output_path += ".feature"

        self.__output_path = output_path
        self.__scenarios = [(False, scenario) for scenario in scenarios]
        self.__is_loaded = True

    def deal(self):
        """Deal a scenario from the bank.

        If this is the first scenario, call _deal_first(). If not, as long as there
        are more scenarios in the bank call _deal_another(). When there are no more scenarios,
        the dealer is 'done'.

        Attempting to deal while the test commands (by default, "behave") fail will raise a
        BotError.
        """
        deal_flags = (was_dealt for (was_dealt, _) in self.__scenarios)

        if not any(deal_flags):
            self._deal_first()
        elif not all(deal_flags):
            if self._are_tests_passing():
                self._deal_another()
            else:
                raise BotError("Can't deal while there are unimplemented scenarios")
        else:
            self.__is_done = True

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

    def _deal_first(self):
        """Deal the very first scenario in the bank.

        This will create the feature file and fill it with the feature's text,
        background, etc. It implicitly calls load().
        """
        self.load()

        if not self.__feature:
            self.__is_done = True
            return

        try:
            mkdir(dirname(self.__output_path))
        except OSError:
            # Directory exists.
            pass

        try:
            with open(self.__output_path, "wb") as features:
                features.write(self.__header)
                features.write(self.__feature)
                if self.__scenarios:
                    (_, scenario) = self.__scenarios[0]
                    features.write(scenario)
                    self.__scenarios[0] = (True, scenario)
                else:
                    self.__is_done = True
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(self.__output_path))

    def _deal_another(self):
        """Deal a new scenario (not the first one)."""
        try:
            with open(self.__output_path, "ab") as features:
                for i in xrange(len(self.__scenarios)):
                    (was_dealt, scenario) = self.__scenarios[i]
                    if not was_dealt:
                        features.write(scenario)
                        self.__scenarios[i] = (True, scenario)
                        break
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(self.__output_path))
