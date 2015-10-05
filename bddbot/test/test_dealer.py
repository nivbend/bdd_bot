"""Test the Dealer class."""

from subprocess import Popen
from os.path import dirname
from nose.tools import assert_true, assert_false, assert_equal, assert_in, assert_raises
from mock import Mock, patch, call, create_autospec, ANY
from mock_open import MockOpen
from bddbot.dealer import Dealer, STATE_PATH
from bddbot.config import TEST_COMMAND
from bddbot.errors import BotError
from bddbot.test.utils import BankMockerTest
from bddbot.test.constants import BANK_PATH_1, BANK_PATH_2, FEATURE_PATH_1, FEATURE_PATH_2
from bddbot.test.constants import DEFAULT_TEST_COMMANDS, CLIENT

FEATURES_DIRECTORY = "features"

(FEATURE_1, SCENARIO_1_1, SCENARIO_1_2) = (
    "Feature: First feature",
    "    Scenario: First feature, first scenario",
    "    Scenario: First feature, second scenario")
(FEATURE_2, SCENARIO_2_1, SCENARIO_2_2) = (
    "Feature: Second feature",
    "    Scenario: Second feature, first scenario",
    "    Scenario: Second feature, second scenario")

class BaseDealerTest(BankMockerTest):
    # pylint: disable=too-few-public-methods
    """A container for utility classes common when testing the Dealer class."""
    FEATURES = {
        BANK_PATH_1: (FEATURE_PATH_1, "", FEATURE_1 + "\n"),
        BANK_PATH_2: (FEATURE_PATH_2, "", FEATURE_2 + "\n"),
    }

    def __init__(self):
        super(BaseDealerTest, self).__init__()
        self.dealer = None
        self.mocked_open = MockOpen()
        self.mocked_popen = create_autospec(Popen)
        self.mocked_mkdir = Mock()

    def teardown(self):
        super(BaseDealerTest, self).teardown()
        patch.stopall()

        # Reset dealer instance.
        self.dealer = None

    def _mock_dealer_functions(self):
        """Mock out standard library functions used by the dealer module."""
        self._reset_mocks()

        patcher = patch.multiple(
            "bddbot.dealer",
            open = self.mocked_open,
            Bank = self.mock_bank_class,
            RemoteBank = self.mock_bank_class,
            Popen = self.mocked_popen,
            mkdir = self.mocked_mkdir)

        patcher.start()

    def _create_dealer(self, banks, tests, name = ""):
        """Create a new dealer instance without loading state."""
        if tests is None:
            tests = DEFAULT_TEST_COMMANDS

        self.mocked_open[STATE_PATH].side_effect = IOError()
        self.dealer = Dealer(banks, tests, name = name)

        self.mocked_open.assert_called_once_with(STATE_PATH, "rb")

        self._reset_mocks()

    def _load_dealer(self, banks = None, tests = None, name = ""):
        """Simulate a call to load() and verify success."""
        if banks is None:
            banks = [BANK_PATH_1, ]
        if not tests:
            tests = DEFAULT_TEST_COMMANDS

        # Setup and call load().
        self._create_dealer(banks, tests, name = name)

        # pylint: disable=bad-continuation
        with patch.multiple("bddbot.dealer",
             Bank = self.mock_bank_class,
             RemoteBank = self.mock_bank_class):
            self.dealer.load()

        # Verify calls to mocks.
        self.mocked_open.assert_not_called()
        self.mocked_popen.assert_not_called()

        for path in banks:
            if not path.startswith("@"):
                self.mock_bank_class.assert_any_call(path)
            else:
                (host, port) = path[1:].split(":")
                self.mock_bank_class.assert_called_with(name, host, int(port))

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

            self.mocked_mkdir.assert_called_once_with(dirname(feature_path))

        # If feature isn't specified, simulate a consecutive deal.
        # Note that calls to Popen should be verified outside of this function in this case.
        else:
            self.mocked_open.assert_called_once_with(feature_path, "ab")
            self.mocked_open[feature_path].write.assert_called_once_with(expected_scenario)
            self.mocked_popen.return_value.communicate.assert_called_with()
            self.mocked_mkdir.assert_not_called()

        self.mock_banks[bank_path].is_fresh.assert_called_with()
        self.mock_banks[bank_path].is_done.assert_called_with()
        self.mock_banks[bank_path].get_next_scenario.assert_called_once_with()

        # We return the commands because we reset the mocks at the end of the function.
        # The stdout/stderr values aren't important, we only care about the commands.
        popen_calls = [command for ((command, ), _) in self.mocked_popen.call_args_list]

        # Reset mocks.
        self._reset_mocks()

        return popen_calls

    def _assert_writes(self, chunks, path = FEATURE_PATH_1):
        """Verify all calls to write()."""
        assert_equal([call(chunk) for chunk in chunks], self.mocked_open[path].write.mock_calls)

    def _reset_mocks(self):
        """Reset all mocks."""
        self.mocked_open.reset_mock()
        self.mocked_popen.reset_mock()
        self.mock_bank_class.reset_mock()
        self.mocked_mkdir.reset_mock()

        for mock_bank in self.mock_banks.itervalues():
            mock_bank.reset_mock()

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

    def test_set_bank(self):
        for (bank_path, expected_feature_path) in self.BANK_FILE_PATHS:
            yield (self._check_set_bank, bank_path, expected_feature_path)

    def test_set_remote_bank(self):
        self._load_dealer(banks = ["@host:3037", ], name = CLIENT)
        assert_true(self.mock_banks["@host:3037"].is_remote)

    def test_set_multiple_banks(self):
        self._load_dealer(banks = [BANK_PATH_1, BANK_PATH_2, ])

    def test_set_test_command(self):
        test_command_1 = ["some_test", ]
        test_command_2 = ["another_test", "--awesome", ]

        self._load_dealer(tests = [test_command_1, test_command_2, ])

        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1 + "\n")
        popen_calls = self._deal(FEATURE_1, SCENARIO_1_1 + "\n")
        assert_equal([], popen_calls)

        self._setup_bank(BANK_PATH_1, False, False, SCENARIO_1_2)
        self.mocked_popen.return_value.returncode = 0
        popen_calls = self._deal(None, SCENARIO_1_2)

        assert_equal([test_command_1, test_command_2, ], popen_calls)

    def _check_set_bank(self, bank_path, expected_feature_path):
        self._load_dealer(banks = [bank_path, ])

        feature_path = bank_path.replace("bank", "feature")
        if not feature_path.endswith(".feature"):
            feature_path += ".feature"

        self.mock_banks[bank_path].is_fresh.return_value = True
        self.mock_banks[bank_path].is_done.return_value = False
        self.mock_banks[bank_path].output_path = feature_path
        self.mock_banks[bank_path].header = ""
        self.mock_banks[bank_path].feature = FEATURE_1 + "\n"
        self.mock_banks[bank_path].get_next_scenario.return_value = SCENARIO_1_1

        self._deal(FEATURE_1, SCENARIO_1_1, bank_path, feature_path = expected_feature_path)
        assert_false(self.mock_banks[bank_path].is_remote)

class TestLoading(BaseDealerTest):
    def setup(self):
        self._mock_dealer_functions()

    def teardown(self):
        super(TestLoading, self).teardown()

    def test_successful_call(self):
        self._load_dealer(banks = [BANK_PATH_1, ])

    def test_call_load_twice(self):
        # Calling load() twice only reads the features bank once.
        self._load_dealer(banks = [BANK_PATH_1, ])

        self.dealer.load()

        self.mocked_open.assert_not_called()
        self.mock_bank_class.assert_not_called()
        self.mocked_popen.assert_not_called()

class TestDealFirst(BaseDealerTest):
    def setup(self):
        self._mock_dealer_functions()

    def teardown(self):
        super(TestDealFirst, self).teardown()

        self.mocked_popen.assert_not_called()

    def test_failed_open(self):
        self._load_dealer()

        self.mocked_open[FEATURE_PATH_1].side_effect = IOError()
        self._setup_bank(BANK_PATH_1, True, False, None)
        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        self.mocked_open.assert_called_once_with(FEATURE_PATH_1, "w")
        self.mocked_open[FEATURE_PATH_1].write.assert_not_called()
        assert_equal(2, self.mock_banks[BANK_PATH_1].is_fresh.call_count)
        self.mock_banks[BANK_PATH_1].is_done.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_failed_write(self):
        self._load_dealer()

        self.mocked_open[FEATURE_PATH_1].write.side_effect = IOError()
        self._setup_bank(BANK_PATH_1, True, False, None)
        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(FEATURE_PATH_1, "w")
        self.mocked_open[FEATURE_PATH_1].write.assert_called_once_with("")
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal(2, self.mock_banks[BANK_PATH_1].is_fresh.call_count)
        self.mock_banks[BANK_PATH_1].is_done.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_successful_write(self):
        # A successful call to deal() should write the feature and the first scenario.
        self._load_dealer()

        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._deal(FEATURE_1, SCENARIO_1_1)

    def test_features_directory_exists(self):
        # Test deal() works even if the features directory already exist.
        self._load_dealer()

        self.mocked_mkdir.side_effect = OSError()
        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._deal(FEATURE_1, SCENARIO_1_1)

class TestDealNext(BaseDealerTest):
    def setup(self):
        self._mock_dealer_functions()
        self._load_dealer()

        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1 + "\n")
        popen_calls = self._deal(FEATURE_1, SCENARIO_1_1 + "\n")
        assert_equal([], popen_calls)

    def test_no_more_scenarios(self):
        # If no more scenarios to deal, mark as d.
        # This includes empty banks and banks with no scenarios.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self.mocked_popen.return_value.returncode = 0

        self.dealer.deal()

        self.mocked_mkdir.assert_not_called()
        self.mocked_open.assert_not_called()
        self.mock_banks[BANK_PATH_1].is_fresh.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].is_done.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_any_call(TEST_COMMAND, stdout = ANY, stderr = ANY)

    def test_should_not_deal_another(self):
        self._setup_bank(BANK_PATH_1, False, False, None)
        self.mocked_popen.return_value.returncode = -1

        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        assert_in("can't deal", error_context.exception.message.lower())
        self.mocked_mkdir.assert_not_called()
        self.mocked_open.assert_not_called()
        self.mock_banks[BANK_PATH_1].is_fresh.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].is_done.assert_not_called()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_any_call(TEST_COMMAND, stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.communicate.assert_called_once_with()

    def test_should_deal_another(self):
        self._setup_bank(BANK_PATH_1, False, False, SCENARIO_1_2)
        popen_calls = self._deal(None, SCENARIO_1_2)
        assert_equal(DEFAULT_TEST_COMMANDS, popen_calls)

class TestDealFromMultipleBanks(BaseDealerTest):
    SCENARIO_COUNTS = [3, 2, 1, 1, 5, ]
    BANKS = ["banks/{:d}.bank".format(i + 1) for i in xrange(len(SCENARIO_COUNTS))]

    def setup(self):
        self._mock_dealer_functions()

    def test_should_not_deal_from_second_bank(self):
        self._load_dealer(banks = [BANK_PATH_1, BANK_PATH_2, ])

        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._setup_bank(BANK_PATH_2, True, False, None)
        self._deal(FEATURE_1, SCENARIO_1_1, BANK_PATH_1)

        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self.mocked_popen.return_value.returncode = -1

        with assert_raises(BotError) as error_context:
            self.dealer.deal()

        assert_in("can't deal", error_context.exception.message.lower())
        self.mocked_open.assert_not_called()
        self.mock_banks[BANK_PATH_1].is_fresh.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].is_done.assert_not_called()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mocked_popen.assert_any_call(TEST_COMMAND, stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.communicate.assert_called_once_with()

    def test_should_deal_from_second_bank(self):
        self._load_dealer(banks = [BANK_PATH_1, BANK_PATH_2, ])

        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._setup_bank(BANK_PATH_2, True, False, None)
        popen_calls = self._deal(FEATURE_1, SCENARIO_1_1, BANK_PATH_1)
        assert_equal([], popen_calls)

        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        popen_calls = self._deal(FEATURE_2, SCENARIO_2_1, BANK_PATH_2)
        assert_equal(DEFAULT_TEST_COMMANDS, popen_calls)

    def test_deal_from_many(self):
        self._load_dealer(banks = self.BANKS)

        for bank in xrange(len(self.BANKS)):
            for scenario in xrange(self.SCENARIO_COUNTS[bank]):
                # Prepare all bank mocks, before and after.
                for previous_bank in xrange(len(self.BANKS[:bank])):
                    self.__setup_bank_at(previous_bank, None, False, True)

                self.__setup_bank_at(bank, scenario, 0 == scenario, False)

                for next_bank in xrange(bank + 1, len(self.BANKS)):
                    self.__setup_bank_at(next_bank, 0, True, False)

                # Deal scenario.
                self._deal(
                    None if 0 < scenario else self.__feature(bank),
                    self.__scenario(bank, scenario),
                    self.BANKS[bank])

    def __setup_bank_at(self, i, j, is_fresh, is_done):
        # pylint: disable=missing-docstring
        scenario = None
        if not is_done:
            scenario = self.__scenario(i, j)

        bank = self.BANKS[i]
        self.mock_banks[bank].is_fresh.return_value = is_fresh
        self.mock_banks[bank].is_done.return_value = is_done
        self.mock_banks[bank].output_path = bank.replace("bank", "feature")
        self.mock_banks[bank].header = ""
        self.mock_banks[bank].feature = self.__feature(i) + "\n"
        self.mock_banks[bank].get_next_scenario.return_value = scenario

    @staticmethod
    def __feature(i):
        # pylint: disable=missing-docstring
        return "Feature: Feature #{:d}".format(i + 1)

    @staticmethod
    def __scenario(i, j):
        # pylint: disable=missing-docstring
        return "Scenario: Scenario #{:d}-{:d}\n".format(i + 1, j + 1)

class TestPersistency(BaseDealerTest):
    def setup(self):
        self._mock_dealer_functions()

    def test_save(self):
        # Verify a call to save with or without loading banks.
        for banks in ([], [BANK_PATH_1, ], [BANK_PATH_1, BANK_PATH_2, ]):
            yield (self._check_save, False, banks, [])
            yield (self._check_save, True, banks, banks)

    def test_resume(self):
        self._setup_bank(BANK_PATH_1, False, False, SCENARIO_1_2)

        # Load a dealer's state.
        with patch("bddbot.dealer.pickle.load") as mocked_load:
            mocked_load.return_value = self.mock_banks.values()
            self.dealer = Dealer([], DEFAULT_TEST_COMMANDS)

        self.mocked_open.assert_called_once_with(STATE_PATH, "rb")
        mocked_load.assert_called_once_with(ANY)
        self.mocked_popen.assert_not_called()

        # Reset the open mock before calling `_deal`, required for assertions.
        self.mocked_open.reset_mock()

        # Verify successful loading by dealing from the bank.
        popen_calls = self._deal(None, SCENARIO_1_2, BANK_PATH_1)
        assert_equal(DEFAULT_TEST_COMMANDS, popen_calls)

    def _check_save(self, should_load, bank_paths, expected_banks):
        if not should_load:
            self._create_dealer(bank_paths, None)
        else:
            self._load_dealer(banks = bank_paths)

        with patch("bddbot.dealer.pickle.dump") as mocked_dump:
            self.dealer.save()

        self.mocked_open.assert_called_once_with(STATE_PATH, "wb")
        mocked_dump.assert_called_once_with(
            [self.mock_banks[path] for path in expected_banks],
            self.mocked_open[STATE_PATH])
        self.mocked_popen.assert_not_called()
