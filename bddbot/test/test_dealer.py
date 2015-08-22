"""Test the Dealer class."""

from subprocess import Popen
from os import mkdir, listdir
from os.path import dirname, basename, join, isdir
from stat import S_IFDIR
from nose.tools import assert_equal, assert_in, assert_raises
from mock import patch, call, create_autospec, ANY
from mock_open import MockOpen
from bddbot.dealer import Dealer, BotError
from bddbot.config import BotConfiguration
from bddbot.config import DEFAULT_CONFIG_FILENAME, DEFAULT_BANK_PATH, DEFAULT_TEST_COMMAND

FEATURES_DIRECTORY = "features"
DEFAULT_FEATURE_PATH = DEFAULT_BANK_PATH.replace("bank", "feature")

class BaseDealerTest(object):
    """A container for utility classes common when testing the Dealer class."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.mocked_open = None
        self.mocked_mkdir = create_autospec(mkdir)
        self.mocked_popen = create_autospec(Popen)
        self.mocked_config = create_autospec(BotConfiguration)

    def _mock_dealer_functions(self, content = ""):
        """Mock out standard library functions used by the dealer module."""
        self.mocked_open = MockOpen(read_data = content)
        self.mocked_mkdir.reset_mock()
        self.mocked_popen.reset_mock()
        self.mocked_config.reset_mock()
        patcher = patch.multiple(
            "bddbot.dealer",
            open = self.mocked_open,
            mkdir = self.mocked_mkdir,
            Popen = self.mocked_popen,
            BotConfiguration = self.mocked_config)

        patcher.start()

        return patcher

    def _load_dealer(self, bank_paths = None):
        """Simulate a call to load() and verify success."""
        if not bank_paths:
            bank_paths = [DEFAULT_BANK_PATH, ]

        self.mocked_config.return_value.bank = bank_paths

        dealer = Dealer()
        dealer.load()

        # Assert actions during load().
        assert_equal([call(path, "rb") for path in bank_paths], self.mocked_open.call_args_list)
        assert_equal(len(bank_paths), self.mocked_open.call_count)
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_called_once_with(DEFAULT_CONFIG_FILENAME)

        # Reset mocks.
        self.mocked_open.reset_mock()
        self.mocked_mkdir.reset_mock()
        self.mocked_popen.reset_mock()
        self.mocked_config.reset_mock()

        return dealer

    def _deal_first(self, feature, scenario):
        """Simulate dealing the first scenario and verify success."""
        dealer = self._load_dealer()
        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "wb")
        self._assert_writes(["", feature + "\n", scenario, ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_not_called()

        # Reset mocks.
        self.mocked_open.reset_mock()
        self.mocked_mkdir.reset_mock()
        self.mocked_popen.reset_mock()
        self.mocked_config.reset_mock()

        return dealer

    def _assert_writes(self, chunks, path = DEFAULT_FEATURE_PATH):
        """Verify all calls to write()."""
        assert_equal([call(chunk) for chunk in chunks], self.mocked_open[path].write.mock_calls)

class TestConfiguration(BaseDealerTest):
    """Test tweaking behavior with the configuration file.

    Most use-cases are already covered by the BotConfiguration's unit-tests, these tests
    are designed to make sure the dealer object uses its configuration properly.
    """
    FEATURE = "Feature: Taking out the garbage"
    SCENARIO_A = "  Scenario: The trash is empty"
    SCENARIO_B = "  Scenario: The bag is torn"
    BANK_FILE_PATHS = [
        ("empty-trash.bank",                "empty-trash.feature"),
        ("banks/empty-trash.bank",          "features/empty-trash.feature"),
        ("without-extension",               "without-extension.feature"),
        ("banks/without-extension",         "features/without-extension.feature"),
        ("/path/to/empty-trash.bank",       "/path/to/empty-trash.feature"),
        ("/path/to/banks/empty-trash.bank", "/path/to/features/empty-trash.feature"),
    ]

    def teardown(self):
        # pylint: disable=no-self-use
        patch.stopall()

    def test_setting_costum_file(self):
        """Setting a custom configuration file path."""
        path = "/path/to/bddbotrc"
        self._mock_dealer_functions()

        # pylint: disable=unused-variable
        dealer = Dealer(config = path)

        self.mocked_open.assert_not_called()
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_called_once_with(path)

    def test_setting_bank_file_path(self):
        """Set the path to the bank as a single file."""
        for (bank_path, expected_feature_path) in self.BANK_FILE_PATHS:
            yield self._check_setting_bank_file_path, bank_path, expected_feature_path

    def test_setting_multiple_bank_file_paths(self):
        """Setting multiple bank file paths will read from all of them."""
        bank_path_1 = "/path/to/first.bank"
        bank_path_2 = "/path/to/second.bank"
        self._mock_dealer_functions("\n".join([self.FEATURE, self.SCENARIO_A, ]))
        self._load_dealer(bank_paths = [bank_path_1, bank_path_2, ])

    def test_setting_bank_directory(self):
        """Supplying a directory path as a bank will iterate over all files under it."""
        bank_directory_path = "/path/to/banks"
        bank_path_1 = join(bank_directory_path, "first.bank")
        bank_path_2 = join(bank_directory_path, "second.bank")

        self._mock_dealer_functions("\n".join([self.FEATURE, self.SCENARIO_A, ]))
        self.mocked_config.return_value.bank = [bank_directory_path, ]
        mocked_isdir = create_autospec(isdir)
        mocked_isdir.return_value.st_mode = S_IFDIR
        mocked_listdir = create_autospec(listdir, return_value = [
            basename(bank_path_1),
            basename(bank_path_2),
            "not_a_bank.txt",
        ])

        dealer = Dealer()
        with patch.multiple("bddbot.dealer", isdir = mocked_isdir, listdir = mocked_listdir):
            dealer.load()

        mocked_isdir.assert_called_once_with(bank_directory_path)
        mocked_listdir.assert_called_once_with(bank_directory_path)
        assert_equal(
            [call(bank_path_1, "rb"), call(bank_path_2, "rb"), ],
            self.mocked_open.call_args_list)
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_called_once_with(DEFAULT_CONFIG_FILENAME)

    def test_setting_test_command(self):
        """Using custom test commands to verify scenarios."""
        test_command_1 = ["some_test", ]
        test_command_2 = ["another_test", "--awesome", ]

        self._mock_dealer_functions("\n".join([self.FEATURE, self.SCENARIO_A, self.SCENARIO_B, ]))
        dealer = self._deal_first(self.FEATURE, self.SCENARIO_A + "\n")

        self.mocked_popen.return_value.returncode = 0
        self.mocked_config.return_value.test_commands = [test_command_1, test_command_2, ]
        dealer.deal()

        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "ab")
        self._assert_writes([self.SCENARIO_B, ])
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call(test_command_1, stdout = ANY, stderr = ANY)
        self.mocked_popen.assert_any_call(test_command_2, stdout = ANY, stderr = ANY)
        self.mocked_config.assert_not_called()

    def _check_setting_bank_file_path(self, bank_path, expected_feature_path):
        # pylint: disable=missing-docstring
        self._mock_dealer_functions("\n".join([self.FEATURE, self.SCENARIO_A, ]))
        dealer = self._load_dealer(bank_paths = [bank_path, ])

        dealer.deal()

        self.mocked_open.assert_called_once_with(expected_feature_path, "wb")
        self._assert_writes(
            ["", self.FEATURE + "\n", self.SCENARIO_A, ],
            path = expected_feature_path)
        self.mocked_mkdir.assert_called_once_with(dirname(expected_feature_path))
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_not_called()

class TestLoading(BaseDealerTest):
    """Test various situations when calling load()."""
    CONTENTS = "\n".join([
        "Feature: Some awesome stuff",
        "  Scenario: Doing cool things",
    ])

    def setup(self):
        self._mock_dealer_functions(self.CONTENTS)
        self.mocked_config.return_value.bank = [DEFAULT_BANK_PATH, ]

    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_called_once_with(DEFAULT_CONFIG_FILENAME)

    def test_no_features_bank_file(self):
        """Catch exception when trying to open a non-existent bank file."""
        self.mocked_open.side_effect = IOError()

        dealer = Dealer()
        with assert_raises(BotError) as error_context:
            dealer.load()

        assert dealer.is_done
        assert_in("no features bank", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(DEFAULT_BANK_PATH, "rb")

    def test_successful_call(self):
        """A successful call to load() should read from the bank file."""
        dealer = Dealer()
        dealer.load()

        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(DEFAULT_BANK_PATH, "rb")

    def test_call_load_twice(self):
        """Calling load() twice only reads the features bank once."""
        dealer = Dealer()
        dealer.load()
        dealer.load()

        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(DEFAULT_BANK_PATH, "rb")

class TestDealFirst(BaseDealerTest):
    """Test dealing the first scenario."""
    FEATURE = "Feature: An awesome feature"
    SCENARIO_A = "  Scenario: Scenario A"
    SCENARIO_B = "  Scenario: Scenario B"
    CONTENTS = [FEATURE, SCENARIO_A, SCENARIO_B, ]

    def teardown(self):
        patch.stopall()

        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_not_called()

    def test_cant_open_features_file_for_writing(self):
        """Capture exceptions in open()."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        self.mocked_open[DEFAULT_FEATURE_PATH].side_effect = IOError()
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        assert not dealer.is_done
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "wb")
        self._assert_writes([])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_cant_write_to_feature_file(self):
        """Capture exceptions in write()."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        self.mocked_open[DEFAULT_FEATURE_PATH].write.side_effect = IOError()
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        assert not dealer.is_done
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "wb")
        self._assert_writes([ANY, ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_successful_write(self):
        """A successful call to deal() should write the feature and the first scenario."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        dealer.deal()

        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "wb")
        self._assert_writes(["", self.FEATURE + "\n", self.SCENARIO_A + "\n", ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_empty_features_bank(self):
        """Dealing from an empty feature file should give the 'done' message."""
        self._mock_dealer_functions("")
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        assert dealer.is_done
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()

    def test_feature_with_no_scenarios(self):
        """An empty feature is skipped."""
        feature = "Feature: An empty feature"
        self._mock_dealer_functions(feature)
        dealer = self._load_dealer()

        dealer.deal()

        assert dealer.is_done
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()

    def test_features_directory_already_exists(self):
        """Test deal() works even if the features directory already exist."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        self.mocked_mkdir.side_effect = OSError()
        dealer.deal()

        # If directory already exist, we should proceed as usual.
        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "wb")
        self._assert_writes(["", self.FEATURE + "\n", self.SCENARIO_A + "\n", ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

class TestDealNext(BaseDealerTest):
    """Test logic and actions when calling deal() continously."""
    FEATURE = "Feature: An awesome feature"
    SCENARIO_1 = "  Scenario: First scenario"

    def teardown(self):
        patch.stopall()

        self.mocked_config.assert_not_called()

    def test_no_more_scenarios(self):
        """If no more scenarios to deal, print 'done' message."""
        self._mock_dealer_functions("\n".join([self.FEATURE, self.SCENARIO_1, ]))
        dealer = self._deal_first(self.FEATURE, self.SCENARIO_1)

        dealer.deal()

        assert dealer.is_done
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_should_not_deal_another(self):
        """If a scenario fails, don't deal another scenario."""
        expected_scenario = "  Scenario: Another scenario"
        contents = [
            self.FEATURE,
            self.SCENARIO_1,
            expected_scenario,
            "  Scenario: The last scenario",
            ]

        self._mock_dealer_functions("\n".join(contents))
        dealer = self._deal_first(self.FEATURE, self.SCENARIO_1 + "\n")

        self.mocked_popen.return_value.returncode = -1
        self.mocked_config.return_value.test_commands = [DEFAULT_TEST_COMMAND.split(), ]
        with assert_raises(BotError) as error_context:
            dealer.deal()

        assert not dealer.is_done
        assert_in("can't deal", error_context.exception.message.lower())
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.wait.assert_called_once_with()

    def test_should_deal_another(self):
        """When all scenarios pass, deal a new scenario."""
        expected_scenario = "  Scenario: Another scenario"
        contents = [
            self.FEATURE,
            self.SCENARIO_1,
            expected_scenario,
            "  Scenario: The last scenario",
            ]

        self._mock_dealer_functions(content = "\n".join(contents))
        self.mocked_config.return_value.test_commands = [DEFAULT_TEST_COMMAND.split(), ]
        dealer = self._deal_first(self.FEATURE, self.SCENARIO_1 + "\n")

        self.mocked_popen.return_value.returncode = 0
        dealer.deal()

        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "ab")
        self._assert_writes([expected_scenario + "\n", ])
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.wait.assert_called_once_with()

    def test_dealing_from_two_banks(self):
        """When the first bank is done, deal from the second if available."""
        bank_path_1 = "/path/to/first.bank"
        bank_path_2 = "/path/to/second.bank"
        (feature_1, scenario_1_1) = (
            "Feature: Tweedle-Dee",
            "  Scenario: Agree to have a battle")
        (feature_2, scenario_2_1, scenario_2_2) = (
            "Feature: Tweedle-Dum",
            "  Scenario: Being frightened by a monsterous crow",
            "  Scenario: Forget quarrel")

        feature_path_1 = bank_path_1.replace("bank", "feature")
        feature_path_2 = bank_path_2.replace("bank", "feature")

        self._mock_dealer_functions()

        self.mocked_open[bank_path_1].read_data = "\n".join([
            feature_1,
            scenario_1_1,
        ])
        self.mocked_open[bank_path_2].read_data = "\n".join([
            feature_2,
            scenario_2_1,
            scenario_2_2,
        ])

        dealer = self._load_dealer(bank_paths = [bank_path_1, bank_path_2, ])
        dealer.deal()

        self.mocked_open.assert_called_once_with(feature_path_1, "wb")
        self._assert_writes(["", feature_1 + "\n", scenario_1_1, ], path = feature_path_1)
        self.mocked_mkdir.assert_called_once_with(dirname(feature_path_1))
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_not_called()

        self.mocked_mkdir.reset_mock()
        self.mocked_popen.reset_mock()
        self.mocked_config.reset_mock()

        dealer.deal()

        self.mocked_open.assert_called_with(feature_path_2, "wb")
        self._assert_writes(["", feature_2 + "\n", scenario_2_1 + "\n", ], path = feature_path_2)
        self.mocked_mkdir.assert_called_once_with(dirname(feature_path_2))
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_not_called()
