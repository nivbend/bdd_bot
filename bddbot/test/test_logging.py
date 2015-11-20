"""Test logging and output."""

from os import chdir
from time import sleep
from threading import Thread
import pickle
from contextlib import contextmanager
from nose.tools import assert_equal, assert_raises
from testfixtures import TempDirectory
from mock import patch, call, ANY
from bddbot.dealer import Dealer, STATE_PATH
from bddbot.config import TEST_COMMAND
from bddbot.errors import BotError, ParsingError
from bddbot.test.test_server import BaseServerTest
from bddbot.test.constants import BANK_PATH_1, BANK_PATH_2, FEATURE_PATH_1, FEATURE_PATH_2
from bddbot.test.constants import DEFAULT_TEST_COMMANDS, HOST, PORT, CLIENT

BANK_PATH_3 = "banks/third.bank"
FEATURE_PATH_3 = BANK_PATH_3.replace("bank", "feature")

(HEADER_1, FEATURE_1, SCENARIO_1_1) = (
    "# Header",
    "Feature: Feature 1",
    "    Scenario: Scenario 1.1")

(FEATURE_2, SCENARIO_2_1, SCENARIO_2_2_1, SCENARIO_2_2_2) = (
    "Feature: Feature 2",
    "    Scenario: Scenario 2.1",
    "    Scenario: Scenario 2.2",
    "        Some text under the scenario")

(FEATURE_3_1, FEATURE_3_2, SCENARIO_3_1) = (
    "Feature: Feature 3",
    "    # A comment on the feature",
    "    Scenario: Scenario 3.1",)

class LoggingTestMixin(object):
    """A mixin class to mock out getLogger calls."""
    # pylint: disable=too-few-public-methods
    @contextmanager
    def _mock_log(self):
        """Mock out logger creation."""
        with patch("bddbot.dealer.logging.getLogger") as mock_logger:
            yield

        mock_logger.assert_called_once_with(ANY)

        # pylint: disable=attribute-defined-outside-init
        self.mocked_log = mock_logger.return_value

class TestDealerLogging(LoggingTestMixin):
    def __init__(self):
        self.sandbox = None
        self.dealer = None

    def setup(self):
        self.sandbox = TempDirectory()
        chdir(self.sandbox.path)

    def teardown(self):
        self.sandbox.cleanup()

        self.dealer = None

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

    def test_remote_bank(self):
        self._create_dealer(["@{:s}:{:d}".format(HOST, PORT), ])
        self.dealer.load()

        self.mocked_log.assert_has_calls([
            call.debug("Loading banks"),
            call.info("Connecting to remote server at %s:%d", HOST, PORT),
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

        with self._mock_log():
            self.dealer = Dealer(banks, DEFAULT_TEST_COMMANDS)

    def _write_banks(self):
        # pylint: disable=missing-docstring
        self.sandbox.write(BANK_PATH_1, "\n".join([HEADER_1, FEATURE_1, SCENARIO_1_1, ]))
        self.sandbox.write(
            BANK_PATH_2,
            "\n".join([FEATURE_2, SCENARIO_2_1, SCENARIO_2_2_1, SCENARIO_2_2_2, ]))

class TestServerLogging(BaseServerTest, LoggingTestMixin):
    FEATURES = {
        BANK_PATH_1: (FEATURE_PATH_1, HEADER_1, FEATURE_1),
        BANK_PATH_2: (FEATURE_PATH_2, "", FEATURE_2),
        BANK_PATH_3: (FEATURE_PATH_3, "", "\n".join([FEATURE_3_1, FEATURE_3_2, ])),
    }

    def __init__(self):
        super(TestServerLogging, self).__init__()
        self.mocked_log = None

    def teardown(self):
        super(TestServerLogging, self).teardown()
        self.mocked_log = None

    def test_serving(self):
        self._create_server([BANK_PATH_1, ])

        self.server.server_address = (HOST, PORT)
        thread = Thread(target = self.server.serve_forever)
        with patch("select.select", return_value = ([], [], [])):
            thread.start()

        # Give thread some time to run.
        sleep(0.1)

        self.mocked_log.info.assert_called_with("Server started on %s:%d", HOST, PORT)

        self.server.shutdown()
        thread.join()

        self.mocked_log.info.assert_called_with("Stopped serving")

    def test_assignment(self):
        # pylint: disable=too-many-statements
        (client_1, client_2) = (CLIENT + "_1", CLIENT + "_2")
        self._create_server([BANK_PATH_1, BANK_PATH_2, BANK_PATH_3, ])

        # Assign the first bank to the first client.
        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self._setup_bank(BANK_PATH_3, True, False, SCENARIO_3_1)
        assert_equal(SCENARIO_1_1, self.server.get_next_scenario(client_1))
        self.mocked_log.info.assert_any_call("Assigning '%s' to '%s'", FEATURE_1, client_1)
        self.mocked_log.info.assert_any_call("Sent '%s' to '%s'", SCENARIO_1_1.lstrip(), client_1)
        assert_equal(2, self.mocked_log.info.call_count)
        self.mocked_log.reset_mock()

        # Assign the next bank to the second client.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self._setup_bank(BANK_PATH_3, True, False, SCENARIO_3_1)
        assert_equal(SCENARIO_2_1, self.server.get_next_scenario(client_2))
        self.mocked_log.info.assert_any_call("Assigning '%s' to '%s'", FEATURE_2, client_2)
        self.mocked_log.info.assert_any_call("Sent '%s' to '%s'", SCENARIO_2_1.lstrip(), client_2)
        assert_equal(2, self.mocked_log.info.call_count)
        self.mocked_log.reset_mock()

        # Unassign a bank when it is done and assign the next.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self._setup_bank(BANK_PATH_3, True, False, SCENARIO_3_1)
        assert_equal(SCENARIO_3_1, self.server.get_next_scenario(client_1))
        self.mocked_log.info.assert_any_call("Unassigning '%s' from '%s'", FEATURE_1, client_1)
        self.mocked_log.info.assert_any_call("Assigning '%s' to '%s'", FEATURE_3_1, client_1)
        self.mocked_log.info.assert_any_call("Sent '%s' to '%s'", SCENARIO_3_1.lstrip(), client_1)
        assert_equal(3, self.mocked_log.info.call_count)
        self.mocked_log.reset_mock()

        # Deal next scenario from an assigned bank.
        scenario_2_2 = "\n".join([SCENARIO_2_2_1, SCENARIO_2_2_2, ])
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, False, False, scenario_2_2)
        self._setup_bank(BANK_PATH_3, False, True, None)
        assert_equal(scenario_2_2, self.server.get_next_scenario(client_2))
        self.mocked_log.info.assert_any_call("Sent '%s' to '%s'", scenario_2_2.lstrip(), client_2)
        assert_equal(1, self.mocked_log.info.call_count)
        self.mocked_log.reset_mock()

        # Unassign banks when they are finished.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, False, True, None)
        self._setup_bank(BANK_PATH_3, False, True, None)
        assert_equal(None, self.server.get_next_scenario(client_1))
        assert_equal(None, self.server.get_next_scenario(client_2))
        self.mocked_log.info.assert_any_call("Unassigning '%s' from '%s'", FEATURE_3_1, client_1)
        self.mocked_log.debug.assert_any_call("No more scenarios for '%s'", client_1)
        self.mocked_log.info.assert_any_call("Unassigning '%s' from '%s'", FEATURE_2, client_2)
        self.mocked_log.debug.assert_any_call("No more scenarios for '%s'", client_2)
        assert_equal(2, self.mocked_log.info.call_count)
        self.mocked_log.reset_mock()

        # Don't assign banks if there aren't any with no more logs (aside debug).
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, False, True, None)
        self._setup_bank(BANK_PATH_3, False, True, None)
        assert_equal(None, self.server.get_next_scenario(client_1))
        assert_equal(None, self.server.get_next_scenario(client_2))
        assert_equal(0, self.mocked_log.info.call_count)
        self.mocked_log.info.assert_not_called()

    def _create_server(self, banks):
        """Create a new server with mock logger and banks."""
        with self._mock_log():
            super(TestServerLogging, self)._create_server(banks)

        self.mocked_log.assert_not_called()
