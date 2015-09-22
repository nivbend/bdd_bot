"""Deal scenarios from bank files.

Dealing reads a new scenario every time from a bank file and appends it to the feature
file, as long as all previous scenarios were properly implemented.

Features are written incrementaly from a bank file ("*.bank") to a corrosponding features
file ("*.feature"). So for example, the bank file 'banks/awesome.bank' will be translated to the
feature file 'features/awesome.feature'.
"""
from os.path import dirname, isdir, join
from os import mkdir, listdir
from subprocess import Popen, PIPE
from collections import OrderedDict
import logging
import pickle
from .bank import Bank, ParsingError
from .config import BotConfiguration, DEFAULT_CONFIG_FILENAME
from .errors import BotError

STATE_PATH = ".bdd-dealer"

class Dealer(object):
    """Manage banks of features to dispense whenever a scenario is implemented."""
    def __init__(self, config = DEFAULT_CONFIG_FILENAME):
        self.__config = BotConfiguration(config)
        self.__is_loaded = False
        self.__is_done = False
        self.__banks = OrderedDict()
        self.__log = logging.getLogger(__name__)

        try:
            with open(STATE_PATH, "rb") as state:
                self.__log.debug("Loading state")
                self.__banks = pickle.load(state)
        except IOError:
            pass
        else:
            self.__is_loaded = True

    @property
    def is_done(self):
        """Return True if no more scenarios are left to deal."""
        if not self.__is_loaded:
            return False

        return all(bank.is_done() for bank in self.__banks.itervalues())

    def save(self):
        """Save the bot's state to file."""
        self.__log.debug("Saving state")
        with open(STATE_PATH, "wb") as state:
            pickle.dump(self.__banks, state)

    def load(self):
        """Load a feature from the bank."""
        if self.__is_loaded:
            return

        self.__log.debug("Loading banks")

        for path in self.__config.bank:
            if isdir(path):
                self._load_directory(path)
            else:
                self._load_file(path)

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

        # Unless it's the first scenario to be dealt, test all scenarios so far.
        if not all(bank.is_fresh() for bank in self.__banks.itervalues()):
            if not self._are_tests_passing():
                raise BotError("Can't deal while there are unimplemented scenarios")

        # Find the first bank that still has scenarios to deal.
        (path, current_bank) = next(
            ((path, bank) for (path, bank) in self.__banks.iteritems() if not bank.is_done()),
            (None, None))

        if not current_bank:
            # No more features to deal from.
            return

        if current_bank.is_fresh():
            self._deal_first(path, current_bank)
        else:
            self._deal_another(path, current_bank)

    def _load_directory(self, path):
        """Load all bank files under a given directory."""
        self.__log.info("Checking bank directory '%s'", path)
        for filename in listdir(path):
            if not filename.endswith(".bank"):
                self.__log.debug("Skipping non-bank file '%s'", filename)
                continue

            filename = join(path, filename)
            self._load_file(filename)

    def _load_file(self, path):
        """Load a bank file."""
        self.__log.info("Loading features bank '%s'", path)
        output_path = path.replace("bank", "feature")
        if not output_path.endswith(".feature"):
            output_path += ".feature"

        try:
            with open(path, "r") as bank_input:
                self.__banks[output_path] = Bank(bank_input.read())
        except IOError:
            raise BotError("Couldn't open features bank '{:s}'".format(path))
        except ParsingError as parsing_error:
            # Supply the bank path and re-raise.
            parsing_error.filename = path

            self.__log.exception(
                "Parsing error in %s:%d:%s",
                path, parsing_error.line, parsing_error.filename)
            raise

    def _are_tests_passing(self):
        """Verify that all scenarios were implemented using `behave`.

        This is done by calling each testing command (by default, only "behave") in order.
        If any of them fail, the result is False.
        """
        for command in self.__config.test_commands:
            process = Popen(command, stdout = PIPE, stderr = PIPE)
            (stdout, stderr) = process.communicate()

            # pylint: disable=superfluous-parens
            if (0 != process.returncode):
                self.__log.warning(
                    "\n".join(["Test '%s' failed", "stdout = %s", "stderr = %s", ]),
                    " ".join(command), stdout, stderr)
                return False

        self.__log.info("All tests are passing")
        return True

    def _deal_first(self, path, bank):
        """Deal the very first scenario in the bank.

        This will create the feature file and fill it with the feature's text,
        background, etc. It implicitly calls load().
        """
        self.__log.info("Dealing first scenario in '%s'", path)

        try:
            mkdir(dirname(path))
            self.__log.debug("Created features directory '%s'", dirname(path))
        except OSError:
            # Directory exists.
            pass

        try:
            with open(path, "w") as features:
                self.__log.info("Writing header from '%s': '%s'", path, bank.header.rstrip("\n"))
                features.write(bank.header)

                self.__log.info("Writing feature from '%s': '%s'", path, bank.feature.rstrip("\n"))
                features.write(bank.feature)

                self.__write_next_scenario(features, path, bank)
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(path))

    def _deal_another(self, path, bank):
        """Deal a new scenario (not the first one)."""
        self.__log.info("Dealing scenario in '%s'", path)

        try:
            with open(path, "ab") as features:
                self.__write_next_scenario(features, path, bank)
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(path))

    def __write_next_scenario(self, stream, path, bank):
        """Write the next scenario from the bank to the stream."""
        scenario = bank.get_next_scenario()

        self.__log.info(
            "Writing scenario from '%s': '%s'",
            path, scenario.splitlines()[0].lstrip())

        stream.write(scenario)
