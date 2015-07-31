"""Test the Dealer class."""

from subprocess import Popen
from os import mkdir
from nose.tools import assert_equal, assert_in, assert_raises
from mock import patch, call, mock_open, create_autospec, ANY, DEFAULT
from bddbot.dealer import Dealer, BotError
from bddbot.dealer import FEATURE_BANK_FILENAME, FEATURES_DIRECTORY, OUTPUT_FEATURES_FILENAME
from bddbot.config import BotConfiguration, DEFAULT_CONFIG_FILENAME, DEFAULT_TEST_COMMAND

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
        self.mocked_open = mock_open(read_data = content)
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

    def _load_dealer(self):
        """Simulate a call to load() and verify success."""
        dealer = Dealer()
        dealer.load()

        # Assert actions during load().
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")
        self.mocked_open.return_value.read.assert_called_once_with()
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
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
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

    def _assert_writes(self, chunks):
        """Verify all calls to write()."""
        assert_equal(
            [call(chunk) for chunk in chunks],
            self.mocked_open.return_value.write.mock_calls)

class TestLoading(BaseDealerTest):
    """Test various situations when calling load()."""
    CONTENTS = "Feature: Some awesome stuff"

    def setup(self):
        self._mock_dealer_functions(self.CONTENTS)

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

        assert not dealer.is_done
        assert_in("no features bank", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

    def test_successful_call(self):
        """A successful call to load() should read from the bank file."""
        dealer = Dealer()
        dealer.load()

        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

    def test_call_load_twice(self):
        """Calling load() twice only reads the features bank once."""
        dealer = Dealer()
        dealer.load()
        dealer.load()

        assert not dealer.is_done
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

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

        self.mocked_open.side_effect = [IOError(), DEFAULT, ]
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        assert not dealer.is_done
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self._assert_writes([])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_cant_write_to_feature_file(self):
        """Capture exceptions in write()."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        self.mocked_open.return_value.write.side_effect = IOError()
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        assert not dealer.is_done
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self._assert_writes([ANY, ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_successful_write(self):
        """A successful call to deal() should write the feature and the first scenario."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        dealer.deal()

        assert not dealer.is_done
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
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
        """Dealing a "null" feature should give the 'done' message."""
        feature = "Feature: An empty feature"
        self._mock_dealer_functions(feature)
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        assert dealer.is_done
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self._assert_writes(["", feature, ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_features_directory_already_exists(self):
        """Test deal() works even if the features directory already exist."""
        self._mock_dealer_functions("\n".join(self.CONTENTS))
        dealer = self._load_dealer()

        self.mocked_mkdir.side_effect = OSError()
        dealer.deal()

        # If directory already exist, we should proceed as usual.
        assert not dealer.is_done
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self._assert_writes(["", self.FEATURE + "\n", self.SCENARIO_A + "\n", ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

class TestDealNext(BaseDealerTest):
    """Test logic and actions when calling deal() continously."""
    FEATURE = "Feature: An awesome feature"
    SCENARIO_1 = "  Scenario: First scenario"

    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_not_called()
        self.mocked_config.assert_not_called()

    def test_no_more_scenarios(self):
        """If no more scenarios to deal, print 'done' message."""
        self._mock_dealer_functions("\n".join([self.FEATURE, self.SCENARIO_1, ]))
        dealer = self._deal_first(self.FEATURE, self.SCENARIO_1)

        dealer.deal()

        assert dealer.is_done
        self.mocked_open.assert_not_called()
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
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "ab")
        self._assert_writes([expected_scenario + "\n", ])
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.wait.assert_called_once_with()

class TestConfiguration(BaseDealerTest):
    """Test tweaking behavior with the configuration file.

    Most use-cases are already covered by the BotConfiguration's unit-tests, these tests
    are designed to make sure the dealer object uses its configuration properly.
    """
    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_not_called()

    def test_setting_costum_file(self):
        """Setting a custom configuration file path."""
        path = "/path/to/bddbotrc"
        self._mock_dealer_functions()

        # pylint: disable=unused-variable
        dealer = Dealer(config = path)

        self.mocked_open.assert_not_called()
        self.mocked_popen.assert_not_called()
        self.mocked_config.assert_called_once_with(path)

    def test_setting_test_command(self):
        """Using custom test commands to verify scenarios."""
        feature = "Feature: Taking out the garbage"
        scenario_a = "  Scenario: The trash is empty"
        scenario_b = "  Scenario: The bag is torn"
        test_command_1 = ["some_test", ]
        test_command_2 = ["another_test", "--awesome", ]

        self._mock_dealer_functions("\n".join([feature, scenario_a, scenario_b, ]))
        dealer = self._deal_first(feature, scenario_a + "\n")

        self.mocked_popen.return_value.returncode = 0
        self.mocked_config.return_value.test_commands = [test_command_1, test_command_2, ]
        dealer.deal()

        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "ab")
        self._assert_writes([scenario_b, ])
        self.mocked_popen.assert_any_call(test_command_1, stdout = ANY, stderr = ANY)
        self.mocked_popen.assert_any_call(test_command_2, stdout = ANY, stderr = ANY)
        self.mocked_config.assert_not_called()
