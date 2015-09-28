"""Test logging and output."""

from os import chdir
from nose.tools import assert_raises
from testfixtures import TempDirectory
from mock import patch, call, ANY
import pickle
from bddbot.dealer import Dealer, STATE_PATH
from bddbot.config import DEFAULT_TEST_COMMAND
from bddbot.errors import BotError, ParsingError

BANK_PATH_1 = "banks/first.bank"
BANK_PATH_2 = "banks/second.bank"
FEATURE_PATH_1 = BANK_PATH_1.replace("bank", "feature")
FEATURE_PATH_2 = BANK_PATH_2.replace("bank", "feature")

(HEADER_1, FEATURE_1, SCENARIO_1_1) = (
    "# Header",
    "Feature: Feature 1",
    "    Scenario: Scenario 1.1")

(FEATURE_2, SCENARIO_2_1, SCENARIO_2_2_1, SCENARIO_2_2_2) = (
    "Feature: Feature 2",
    "    Scenario: Scenario 2.1",
    "    Scenario: Scenario 2.2",
    "        Some text under the scenario")

def _create_dealer(banks = None):
    """Create a new dealer and return it and the mocked-out logger instance."""
    if banks is None:
        banks = [BANK_PATH_1, BANK_PATH_2, ]

    with patch("bddbot.dealer.logging.getLogger") as mock_log:
        dealer = Dealer(banks)

    mock_log.assert_called_once_with(ANY)

    # Return the dealer and the logger objects.
    return (dealer, mock_log.return_value)

class TestDealerLogging(object):
    """Test and verify log messages during a dealer's execution."""
    def setup(self):
        # pylint: disable=missing-docstring, attribute-defined-outside-init
        self.sandbox = TempDirectory()
        chdir(self.sandbox.path)

    def teardown(self):
        # pylint: disable=missing-docstring
        self.sandbox.cleanup()

    def test_state(self):
        """Check state-related messages."""
        self.sandbox.write(STATE_PATH, pickle.dumps({}))

        # Verify loading log message.
        (dealer, mocked_log) = _create_dealer()

        mocked_log.debug.assert_called_once_with("Loading state")

        # Verify storing log message.
        dealer.save()

        mocked_log.debug.assert_called_with("Saving state")

        # No other messages should be printed.
        mocked_log.info.assert_not_called()
        mocked_log.warning.assert_not_called()
        mocked_log.error.assert_not_called()
        mocked_log.critical.assert_not_called()

    def test_no_banks(self):
        # pylint: disable=no-self-use
        """Output a warning if no banks were specified."""
        (dealer, mocked_log) = _create_dealer([])
        dealer.load()

        mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.warning("No banks"),
            ])

    def test_load(self):
        """Check bank loading messages."""
        self._write_banks()

        (dealer, mocked_log) = _create_dealer()
        dealer.load()

        mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.info("Loading features bank '%s'", BANK_PATH_1),
            call.info("Loading features bank '%s'", BANK_PATH_2),
            ])
        mocked_log.warning.assert_not_called()

    def test_parsing_error(self):
        """Test parsing error logging during load()."""
        bad_bank_path = "banks/bad.bank"
        self.sandbox.write(
            bad_bank_path,
            "\n".join([
                FEATURE_1,
                SCENARIO_1_1,
                "        \"\"\"",
                "        THIS IS AN UNFINISHED MULTILINE TEXT",
            ]))

        (dealer, mocked_log) = _create_dealer([bad_bank_path, ])

        with assert_raises(ParsingError):
            dealer.load()

        mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.info("Loading features bank '%s'", bad_bank_path),
            call.exception("Parsing error in %s:%d:%s", bad_bank_path, 3, ANY),
            ])

    @patch("bddbot.dealer.Popen")
    def test_deal(self, mocked_popen):
        """Test dealing the scenarios from feature banks."""
        self._write_banks()

        # Load dealer, ignoring logs.
        (dealer, mocked_log) = _create_dealer()
        dealer.load()
        mocked_log.reset_mock()

        # Deal the first scenario.
        dealer.deal()

        mocked_log.assert_has_calls([
            call.info("Dealing first scenario in '%s'", FEATURE_PATH_1),
            call.debug("Created features directory '%s'", "features"),
            call.info("Writing header from '%s': '%s'", FEATURE_PATH_1, HEADER_1),
            call.info("Writing feature from '%s': '%s'", FEATURE_PATH_1, FEATURE_1),
            call.info("Writing scenario from '%s': '%s'", FEATURE_PATH_1, SCENARIO_1_1.lstrip()),
            ])

        mocked_log.reset_mock()

        # Deal from a new feature.
        mocked_popen.return_value.returncode = 0
        mocked_popen.return_value.communicate.return_value = ("", "")
        dealer.deal()

        mocked_log.assert_has_calls([
            call.info("All tests are passing"),
            call.info("Dealing first scenario in '%s'", FEATURE_PATH_2),
            call.info("Writing header from '%s': '%s'", FEATURE_PATH_2, ""),
            call.info("Writing feature from '%s': '%s'", FEATURE_PATH_2, FEATURE_2),
            call.info("Writing scenario from '%s': '%s'", FEATURE_PATH_2, SCENARIO_2_1.lstrip()),
            ])

        mocked_log.reset_mock()

        # Attempt to deal a new scenario before tests are passing.
        mocked_popen.return_value.returncode = -1
        mocked_popen.return_value.communicate.return_value = ("STDOUT", "STDERR")

        with assert_raises(BotError):
            dealer.deal()

        mocked_log.warning.assert_called_once_with(
            "\n".join(["Test '%s' failed", "stdout = %s", "stderr = %s", ]),
            DEFAULT_TEST_COMMAND,
            "STDOUT",
            "STDERR")

        mocked_log.reset_mock()

        # If scenario was implemented, deal from the second scenario from the same feature.
        mocked_popen.return_value.returncode = 0
        mocked_popen.return_value.communicate.return_value = ("", "")
        dealer.deal()

        mocked_log.assert_has_calls([
            call.info("All tests are passing"),
            call.info("Dealing scenario in '%s'", FEATURE_PATH_2),
            call.info("Writing scenario from '%s': '%s'", FEATURE_PATH_2, SCENARIO_2_2_1.lstrip()),
            ])

        mocked_log.reset_mock()

    def _write_banks(self):
        # pylint: disable=missing-docstring
        self.sandbox.write(BANK_PATH_1, "\n".join([HEADER_1, FEATURE_1, SCENARIO_1_1, ]))
        self.sandbox.write(
            BANK_PATH_2,
            "\n".join([FEATURE_2, SCENARIO_2_1, SCENARIO_2_2_1, SCENARIO_2_2_2, ]))
