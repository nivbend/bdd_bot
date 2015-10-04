"""Test logging and output."""

from os import chdir
from nose.tools import assert_raises
from testfixtures import TempDirectory
from mock import patch, call, ANY
import pickle
from bddbot.dealer import Dealer, STATE_PATH
from bddbot.config import TEST_COMMAND
from bddbot.errors import BotError, ParsingError
from bddbot.test.constants import BANK_PATH_1, BANK_PATH_2, FEATURE_PATH_1, FEATURE_PATH_2
from bddbot.test.constants import DEFAULT_TEST_COMMANDS

(HEADER_1, FEATURE_1, SCENARIO_1_1) = (
    "# Header",
    "Feature: Feature 1",
    "    Scenario: Scenario 1.1")

(FEATURE_2, SCENARIO_2_1, SCENARIO_2_2_1, SCENARIO_2_2_2) = (
    "Feature: Feature 2",
    "    Scenario: Scenario 2.1",
    "    Scenario: Scenario 2.2",
    "        Some text under the scenario")

class TestDealerLogging(object):
    def __init__(self):
        self.sandbox = None
        self.dealer = None
        self.mocked_log = None

    def setup(self):
        self.sandbox = TempDirectory()
        chdir(self.sandbox.path)

    def teardown(self):
        self.sandbox.cleanup()

        self.dealer = None
        self.mocked_log = None

    def test_state(self):
        self.sandbox.write(STATE_PATH, pickle.dumps({}))

        self._create_dealer()

        # Verify loading log message.
        self.mocked_log.debug.assert_called_once_with("Loading state")

        # Verify storing log message.
        self.dealer.save()

        self.mocked_log.debug.assert_called_with("Saving state")

        # No other messages should be printed.
        self.mocked_log.info.assert_not_called()
        self.mocked_log.warning.assert_not_called()
        self.mocked_log.error.assert_not_called()
        self.mocked_log.critical.assert_not_called()

    def test_no_banks(self):
        # Output a warning if no banks were specified.
        self._create_dealer([])
        self.dealer.load()

        self.mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.warning("No banks"),
            ])

    def test_load(self):
        self._write_banks()

        self._create_dealer()
        self.dealer.load()

        self.mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.info("Loading features bank '%s'", BANK_PATH_1),
            call.info("Loading features bank '%s'", BANK_PATH_2),
            ])
        self.mocked_log.warning.assert_not_called()

    def test_parsing_error(self):
        bad_bank_path = "banks/bad.bank"
        self.sandbox.write(
            bad_bank_path,
            "\n".join([
                FEATURE_1,
                SCENARIO_1_1,
                "        \"\"\"",
                "        THIS IS AN UNFINISHED MULTILINE TEXT",
            ]))

        self._create_dealer([bad_bank_path, ])

        with assert_raises(ParsingError):
            self.dealer.load()

        self.mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.info("Loading features bank '%s'", bad_bank_path),
            call.exception("Parsing error in %s:%d:%s", bad_bank_path, 3, ANY),
            ])

    @patch("bddbot.dealer.Popen")
    def test_deal(self, mocked_popen):
        self._write_banks()

        # Load dealer, ignoring logs.
        self._create_dealer()
        self.dealer.load()
        self.mocked_log.reset_mock()

        # Deal the first scenario.
        self.dealer.deal()

        self.mocked_log.assert_has_calls([
            call.info("Dealing first scenario in '%s'", FEATURE_PATH_1),
            call.debug("Created features directory '%s'", "features"),
            call.info("Writing header from '%s': '%s'", FEATURE_PATH_1, HEADER_1),
            call.info("Writing feature from '%s': '%s'", FEATURE_PATH_1, FEATURE_1),
            call.info("Writing scenario from '%s': '%s'", FEATURE_PATH_1, SCENARIO_1_1.lstrip()),
            ])

        self.mocked_log.reset_mock()

        # Deal from a new feature.
        mocked_popen.return_value.returncode = 0
        mocked_popen.return_value.communicate.return_value = ("", "")
        self.dealer.deal()

        self.mocked_log.assert_has_calls([
            call.info("All tests are passing"),
            call.info("Dealing first scenario in '%s'", FEATURE_PATH_2),
            call.info("Writing header from '%s': '%s'", FEATURE_PATH_2, ""),
            call.info("Writing feature from '%s': '%s'", FEATURE_PATH_2, FEATURE_2),
            call.info("Writing scenario from '%s': '%s'", FEATURE_PATH_2, SCENARIO_2_1.lstrip()),
            ])

        self.mocked_log.reset_mock()

        # Attempt to deal a new scenario before tests are passing.
        mocked_popen.return_value.returncode = -1
        mocked_popen.return_value.communicate.return_value = ("STDOUT", "STDERR")

        with assert_raises(BotError):
            self.dealer.deal()

        self.mocked_log.warning.assert_called_once_with(
            "\n".join(["Test '%s' failed", "stdout = %s", "stderr = %s", ]),
            " ".join(TEST_COMMAND),
            "STDOUT",
            "STDERR")

        self.mocked_log.reset_mock()

        # If scenario was implemented, deal from the second scenario from the same feature.
        mocked_popen.return_value.returncode = 0
        mocked_popen.return_value.communicate.return_value = ("", "")
        self.dealer.deal()

        self.mocked_log.assert_has_calls([
            call.info("All tests are passing"),
            call.info("Dealing scenario in '%s'", FEATURE_PATH_2),
            call.info("Writing scenario from '%s': '%s'", FEATURE_PATH_2, SCENARIO_2_2_1.lstrip()),
            ])

        self.mocked_log.reset_mock()

    def _create_dealer(self, banks = None):
        """Create a new dealer and logger mock."""
        if banks is None:
            banks = [BANK_PATH_1, BANK_PATH_2, ]

        with patch("bddbot.dealer.logging.getLogger") as mock_logger:
            self.dealer = Dealer(banks, DEFAULT_TEST_COMMANDS)

        mock_logger.assert_called_once_with(ANY)
        self.mocked_log = mock_logger.return_value

    def _write_banks(self):
        # pylint: disable=missing-docstring
        self.sandbox.write(BANK_PATH_1, "\n".join([HEADER_1, FEATURE_1, SCENARIO_1_1, ]))
        self.sandbox.write(
            BANK_PATH_2,
            "\n".join([FEATURE_2, SCENARIO_2_1, SCENARIO_2_2_1, SCENARIO_2_2_2, ]))
