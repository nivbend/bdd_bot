"""Test the Dealer class."""

from collections import defaultdict
from subprocess import Popen
from os.path import dirname
from nose.tools import assert_equal, assert_in, assert_raises
from mock import Mock, patch, call, create_autospec, ANY
from mock_open import MockOpen
from bddbot.dealer import Dealer, STATE_PATH
from bddbot.config import DEFAULT_TEST_COMMAND
from bddbot.errors import BotError

FEATURES_DIRECTORY = "features"
BANK_PATH_1 = "banks/first.bank"
BANK_PATH_2 = "banks/second.bank"
FEATURE_PATH_1 = BANK_PATH_1.replace("bank", "feature")
FEATURE_PATH_2 = BANK_PATH_2.replace("bank", "feature")

(FEATURE_1, SCENARIO_1_1, SCENARIO_1_2) = (
    "Feature: First feature",
    "    Scenario: First feature, first scenario",
    "    Scenario: First feature, second scenario")
(FEATURE_2, SCENARIO_2_1, SCENARIO_2_2) = (
    "Feature: Second feature",
    "    Scenario: Second feature, first scenario",
    "    Scenario: Second feature, second scenario")

class BaseDealerTest(object):
    """A container for utility classes common when testing the Dealer class."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.dealer = None
        self.mocked_open = MockOpen()
        self.mocked_bank = defaultdict(Mock)
        self.mocked_bank_class = Mock(side_effect = self.__create_bank)
        self.mocked_popen = create_autospec(Popen)

    def teardown(self):
        patch.stopall()

        # Reset dealer instance.
        self.dealer = None

    def _mock_dealer_functions(self):
        """Mock out standard library functions used by the dealer module."""
        self._reset_mocks()

        patcher = patch.multiple(
            "bddbot.dealer",
            open = self.mocked_open,
            Bank = self.mocked_bank_class,
            Popen = self.mocked_popen)

        patcher.start()

    def _create_dealer(self, banks, test_commands = None):
        """Create a new dealer instance without loading state."""
        if not test_commands:
            test_commands = [DEFAULT_TEST_COMMAND.split(), ]

        self.mocked_open[STATE_PATH].side_effect = IOError()
        self.dealer = Dealer(bank_paths = banks, tests = test_commands)

        self.mocked_open.assert_called_once_with(STATE_PATH, "rb")

        self._reset_mocks()

    def _load_dealer(self, banks = None, test_commands = None):
        """Simulate a call to load() and verify success."""
        if banks is None:
            banks = [BANK_PATH_1, ]
        if not test_commands:
            test_commands = [DEFAULT_TEST_COMMAND.split(), ]

        # Setup and call load().
        self._create_dealer(banks, test_commands)
        self.dealer.load()

        # Verify calls to mocks.
        self.mocked_open.assert_not_called()
        self.mocked_bank_class.assert_has_calls([call(path) for path in banks])
        self.mocked_popen.assert_not_called()

        self._reset_mocks()

    def _deal(self, expected_feature, expected_scenario, bank_path = None, feature_path = None):
        # pylint: disable=too-many-arguments
        """Simulate dealing a scenario and verify success.

        If `expected_feature` is specified, simulate the first time a scenario is dealt from
        the features bank. Otherwise, simulate a consecutive deal from a previous bank.

        Return the commands passed to `Popen()` to verify outside of this function.
        """
        if not bank_path:
            bank_path = BANK_PATH_1

        if not feature_path:
            feature_path = bank_path.replace("bank", "feature")

        self.mocked_popen.return_value.returncode = 0
        self.mocked_popen.return_value.communicate.return_value = ("", "")

        with patch("bddbot.dealer.mkdir") as mocked_mkdir:
            self.dealer.deal()

        # If feature is specified, simulate the first deal from the features bank.
        if expected_feature is not None:
            self.mocked_open.assert_called_once_with(feature_path, "w")

            if expected_scenario is not None:
                self._assert_writes(
                    ["", expected_feature + "\n", expected_scenario, ],
                    path = feature_path)
            else:
                self._assert_writes(
                    ["", expected_feature, ],
                    path = feature_path)

            mocked_mkdir.assert_called_once_with(dirname(feature_path))

        # If feature isn't specified, simulate a consecutive deal.
        # Note that calls to Popen should be verified outside of this function in this case.
        else:
            self.mocked_open.assert_called_once_with(feature_path, "ab")
            self.mocked_open[feature_path].write.assert_called_once_with(expected_scenario)
            self.mocked_popen.return_value.communicate.assert_called_with()
            mocked_mkdir.assert_not_called()

        self.mocked_bank[bank_path].is_fresh.assert_called_with()
        self.mocked_bank[bank_path].is_done.assert_called_with()
        self.mocked_bank[bank_path].get_next_scenario.assert_called_once_with()

        # We return the commands because we reset the mocks at the end of the function.
        # The stdout/stderr values aren't important, we only care about the commands.
        popen_calls = [command for ((command, ), _) in self.mocked_popen.call_args_list]

        # Reset mocks.
        self._reset_mocks()

        return popen_calls

    def _setup_bank(self, path, is_fresh, is_done, header, feature, scenario, feature_path = None):
        # pylint: disable=too-many-arguments
        """Setup a mocked Bank instance before calling `deal()`."""
        if not feature_path:
            feature_path = path.replace("bank", "feature")

        mock_bank = self.mocked_bank[path]

        mock_bank.is_fresh.return_value = is_fresh
        mock_bank.is_done.return_value = is_done
        mock_bank.output_path = feature_path

        if is_fresh:
            mock_bank.header = header
            mock_bank.feature = feature
        else:
            mock_bank.header = None
            mock_bank.feature = None

        if not is_done:
            mock_bank.get_next_scenario.return_value = scenario
        else:
            # get_next_scenario shouldn't be called.
            mock_bank.get_next_scenario.return_value = None

    def _assert_writes(self, chunks, path = FEATURE_PATH_1):
        """Verify all calls to write()."""
        assert_equal([call(chunk) for chunk in chunks], self.mocked_open[path].write.mock_calls)

    def _reset_mocks(self):
        """Reset all mocks."""
        self.mocked_open.reset_mock()
        self.mocked_popen.reset_mock()

        for mock_bank in self.mocked_bank.itervalues():
            mock_bank.reset_mock()

    def __create_bank(self, bank_path):
        """Return a mock Bank instance, or creates a new one and adds it to the map."""
        return self.mocked_bank.setdefault(bank_path, Mock())

class TestConfiguration(BaseDealerTest):
    """Test tweaking behavior with the configuration file.

    Most use-cases are already covered by the BotConfiguration's unit-tests, these tests
    are designed to make sure the dealer object uses its configuration properly.
    """
    BANK_FILE_PATHS = [
        ("empty-trash.bank",                "empty-trash.feature"),
        ("banks/empty-trash.bank",          "features/empty-trash.feature"),
        ("without-extension",               "without-extension.feature"),
        ("banks/without-extension",         "features/without-extension.feature"),
        ("/path/to/empty-trash.bank",       "/path/to/empty-trash.feature"),
        ("/path/to/banks/empty-trash.bank", "/path/to/features/empty-trash.feature"),
    ]

    def setup(self):
        self._mock_dealer_functions()

    def test_setting_bank_file_path(self):
        """Set the path to the bank as a single file."""
        for (bank_path, expected_feature_path) in self.BANK_FILE_PATHS:
            yield self._check_setting_bank_file_path, bank_path, expected_feature_path

    def test_setting_multiple_bank_file_paths(self):
        """Setting multiple bank file paths will read from all of them."""
        self._load_dealer(banks = [BANK_PATH_1, BANK_PATH_2, ])

    def test_setting_test_command(self):
        """Using custom test commands to verify scenarios."""
        test_command_1 = ["some_test", ]
        test_command_2 = ["another_test", "--awesome", ]

        self._load_dealer(test_commands = [test_command_1, test_command_2, ])

        self._setup_bank(BANK_PATH_1, True, False, "", FEATURE_1 + "\n", SCENARIO_1_1 + "\n")
        popen_calls = self._deal(FEATURE_1, SCENARIO_1_1 + "\n")
        assert_equal([], popen_calls)

        self._setup_bank(BANK_PATH_1, False, False, None, None, SCENARIO_1_2)
        self.mocked_popen.return_value.returncode = 0
        popen_calls = self._deal(None, SCENARIO_1_2)

        assert_equal([test_command_1, test_command_2, ], popen_calls)

    def _check_setting_bank_file_path(self, bank_path, expected_feature_path):
        # pylint: disable=missing-docstring
        self._load_dealer(banks = [bank_path, ])

        self._setup_bank(
            bank_path,
            True,
            False,
            "",
            FEATURE_1 + "\n",
            SCENARIO_1_1,
            feature_path = expected_feature_path)

        self._deal(FEATURE_1, SCENARIO_1_1, bank_path, feature_path = expected_feature_path)

class TestLoading(BaseDealerTest):
    """Test various situations when calling load()."""
    def setup(self):
        self._mock_dealer_functions()

    def teardown(self):
        super(TestLoading, self).teardown()

        self.mocked_popen.assert_not_called()

    def test_successful_call(self):
        """A successful call to load() should read from the bank file."""
        self._load_dealer(banks = [BANK_PATH_1, ])

    def test_call_load_twice(self):
        """Calling load() twice only reads the features bank once."""
        self._load_dealer(banks = [BANK_PATH_1, ])
        self.dealer.load()

class TestDealFirst(BaseDealerTest):
    """Test dealing the first scenario."""
    def setup(self):
        self._mock_dealer_functions()

    def teardown(self):
        super(TestDealFirst, self).teardown()

        self.mocked_popen.assert_not_called()

    @patch("bddbot.dealer.mkdir")
    def test_cant_open_features_file_for_writing(self, mocked_mkdir):
        """Capture exceptions in open()."""
        self._load_dealer()

        self.mocked_open[FEATURE_PATH_1].side_effect = IOError()
        self._setup_bank(BANK_PATH_1, True, False, None, None, None)
        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        assert_in("couldn't write", error_context.exception.message.lower())
        mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        self.mocked_open.assert_called_once_with(FEATURE_PATH_1, "w")
        self.mocked_open[FEATURE_PATH_1].write.assert_not_called()
        assert_equal(2, self.mocked_bank[BANK_PATH_1].is_fresh.call_count)
        self.mocked_bank[BANK_PATH_1].is_done.assert_called_once_with()
        self.mocked_bank[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_not_called()

    @patch("bddbot.dealer.mkdir")
    def test_cant_write_to_feature_file(self, mocked_mkdir):
        """Capture exceptions in write()."""
        self._load_dealer()

        self.mocked_open[FEATURE_PATH_1].write.side_effect = IOError()
        self._setup_bank(BANK_PATH_1, True, False, "", None, None)
        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(FEATURE_PATH_1, "w")
        self.mocked_open[FEATURE_PATH_1].write.assert_called_once_with("")
        mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal(2, self.mocked_bank[BANK_PATH_1].is_fresh.call_count)
        self.mocked_bank[BANK_PATH_1].is_done.assert_called_once_with()
        self.mocked_bank[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_successful_write(self):
        """A successful call to deal() should write the feature and the first scenario."""
        self._load_dealer()

        self._setup_bank(BANK_PATH_1, True, False, "", FEATURE_1 + "\n", SCENARIO_1_1)
        self._deal(FEATURE_1, SCENARIO_1_1)

    @patch("bddbot.dealer.mkdir")
    def test_features_directory_already_exists(self, mocked_mkdir):
        """Test deal() works even if the features directory already exist."""
        self._load_dealer()

        mocked_mkdir.side_effect = OSError()
        self._setup_bank(BANK_PATH_1, True, False, "", FEATURE_1 + "\n", SCENARIO_1_1)
        self._deal(FEATURE_1, SCENARIO_1_1)

class TestDealNext(BaseDealerTest):
    """Test logic and actions when calling deal() continously."""
    def setup(self):
        self._mock_dealer_functions()
        self._load_dealer()

        self._setup_bank(BANK_PATH_1, True, False, "", FEATURE_1 + "\n", SCENARIO_1_1 + "\n")
        popen_calls = self._deal(FEATURE_1, SCENARIO_1_1 + "\n")
        assert_equal([], popen_calls)

    @patch("bddbot.dealer.mkdir")
    def test_no_more_scenarios(self, mocked_mkdir):
        """If no more scenarios to deal, mark as done.

        This includes empty banks and banks with no scenarios.
        """
        self._setup_bank(BANK_PATH_1, False, True, None, None, None)
        self.mocked_popen.return_value.returncode = 0

        self.dealer.deal()

        mocked_mkdir.assert_not_called()
        self.mocked_open.assert_not_called()
        self.mocked_bank[BANK_PATH_1].is_fresh.assert_called_once_with()
        self.mocked_bank[BANK_PATH_1].is_done.assert_called_once_with()
        self.mocked_bank[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)

    @patch("bddbot.dealer.mkdir")
    def test_should_not_deal_another(self, mocked_mkdir):
        """If a scenario fails, don't deal another scenario."""
        self._setup_bank(BANK_PATH_1, False, False, None, None, None)
        self.mocked_popen.return_value.returncode = -1

        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        assert_in("can't deal", error_context.exception.message.lower())
        mocked_mkdir.assert_not_called()
        self.mocked_open.assert_not_called()
        self.mocked_bank[BANK_PATH_1].is_fresh.assert_called_once_with()
        self.mocked_bank[BANK_PATH_1].is_done.assert_not_called()
        self.mocked_bank[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.communicate.assert_called_once_with()

    def test_should_deal_another(self):
        """When all scenarios pass, deal a new scenario."""
        self._setup_bank(BANK_PATH_1, False, False, None, None, SCENARIO_1_2)
        popen_calls = self._deal(None, SCENARIO_1_2)
        assert_equal([DEFAULT_TEST_COMMAND.split(), ], popen_calls)

class TestDealFromMultipleBanks(BaseDealerTest):
    """Test dealing from multiple banks."""
    def test_deal_from_second_bank(self):
        """When the first bank is done, deal from the second if available."""
        self._mock_dealer_functions()
        self._load_dealer(banks = [BANK_PATH_1, BANK_PATH_2, ])

        self._setup_bank(BANK_PATH_1, True, False, "", FEATURE_1 + "\n", SCENARIO_1_1)
        self._setup_bank(BANK_PATH_2, True, False, None, None, None)
        popen_calls = self._deal(FEATURE_1, SCENARIO_1_1, BANK_PATH_1)
        assert_equal([], popen_calls)

        self._setup_bank(BANK_PATH_1, False, True, None, None, None)
        self._setup_bank(BANK_PATH_2, True, False, "", FEATURE_2 + "\n", SCENARIO_2_1)
        popen_calls = self._deal(FEATURE_2, SCENARIO_2_1, BANK_PATH_2)
        assert_equal([DEFAULT_TEST_COMMAND.split(), ], popen_calls)

class TestPersistency(BaseDealerTest):
    """Test storing and loading the bot's state."""
    def setup(self):
        self._mock_dealer_functions()

    def test_save(self):
        """Verify a call to save with or without loading banks."""
        for banks in ([], [BANK_PATH_1, ], [BANK_PATH_1, BANK_PATH_2, ]):
            yield self._check_save, False, banks, []
            yield self._check_save, True, banks, banks

    def test_resume(self):
        """Test resuming from a previous state."""
        self._setup_bank(BANK_PATH_1, False, False, None, None, SCENARIO_1_2)

        # Load a dealer's state.
        with patch("bddbot.dealer.pickle.load") as mocked_load:
            mocked_load.return_value = self.mocked_bank.values()
            self.dealer = Dealer()

        self.mocked_open.assert_called_once_with(STATE_PATH, "rb")
        mocked_load.assert_called_once_with(ANY)
        self.mocked_popen.assert_not_called()

        # Reset the open mock before calling `_deal`, required for assertions.
        self.mocked_open.reset_mock()

        # Verify successful loading by dealing from the bank.
        popen_calls = self._deal(None, SCENARIO_1_2, BANK_PATH_1)
        assert_equal([DEFAULT_TEST_COMMAND.split(), ], popen_calls)

    def _check_save(self, should_load, bank_paths, expected_banks):
        # pylint: disable=missing-docstring
        if not should_load:
            self._create_dealer(bank_paths)
        else:
            self._load_dealer(banks = bank_paths)

        with patch("bddbot.dealer.pickle.dump") as mocked_dump:
            self.dealer.save()

        self.mocked_open.assert_called_once_with(STATE_PATH, "wb")
        mocked_dump.assert_called_once_with(
            [self.mocked_bank[path] for path in expected_banks],
            self.mocked_open[STATE_PATH])
        self.mocked_popen.assert_not_called()
