"""Test the Dealer class."""

from cStringIO import StringIO
from subprocess import PIPE
from nose.tools import assert_raises, assert_in, assert_equal
from mock import ANY, DEFAULT, MagicMock, mock_open, patch
from bddbot import Dealer
from bddbot.dealer import BotError
from bddbot.dealer import FEATURE_BANK_FILENAME, FEATURES_DIRECTORY, OUTPUT_FEATURES_FILENAME

class BaseDealerTest(object):
    """A container for utility classes common when testing the Dealer class."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.__stdout = None
        self.mocked_open = None
        self.mocked_mkdir = None
        self.mocked_popen = None

    @property
    def stdout(self):
        """Get everything captured on stdout as a string."""
        if self.__stdout is None:
            return None

        return self.__stdout.getvalue()

    def _capture_stdout(self):
        """Mock out stdout to capture any calls to print."""
        self.__stdout = StringIO()
        patcher = patch("sys.stdout", self.__stdout)
        patcher.start()

        return patcher

    def _mock_dealer_functions(self, content = ""):
        """Mock out standard library functions used by the dealer module."""
        self.mocked_open = mock_open(read_data = content)
        self.mocked_mkdir = MagicMock()
        self.mocked_popen = MagicMock()
        patcher = patch.multiple(
            "bddbot.dealer",
            open = self.mocked_open,
            mkdir = self.mocked_mkdir,
            Popen = self.mocked_popen)

        patcher.start()

        return patcher

    def _load_dealer(self):
        """Simulate a call to load() and verify success."""
        dealer = Dealer()
        dealer.load()

        # Assert actions during load().
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")
        self.mocked_open().read.assert_called_once_with()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

        # Reset mocks.
        self.mocked_open.reset_mock()
        self.mocked_mkdir.reset_mock()
        self.mocked_popen.reset_mock()

        return dealer

class TestLoading(BaseDealerTest):
    """Test various situations when calling load()."""
    CONTENT = "Feature: Some awesome stuff"

    def setup(self):
        self._capture_stdout()
        self._mock_dealer_functions(content = self.CONTENT)

    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()
        assert_equal("", self.stdout)

    def test_no_features_bank_file(self):
        """Catch exception when trying to open a non-existent bank file."""
        self.mocked_open.side_effect = IOError()

        dealer = Dealer()
        with assert_raises(BotError) as error_context:
            dealer.load()

        assert_in("no features bank", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

    def test_successful_call(self):
        """A successful call to load() should read from the bank file."""
        dealer = Dealer()
        dealer.load()

        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

    def test_call_load_twice(self):
        """Calling load() twice only reads the features bank once."""
        dealer = Dealer()
        dealer.load()
        dealer.load()

        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

class TestDealFirst(BaseDealerTest):
    """Test dealing the first scenario."""
    DEFAULT_CONTENTS = [
        "Feature: An awesome feature",
        "  Scenario: Scenario A",
        "  Scenario: Scenario B",
        ]

    def setup(self):
        self._capture_stdout()

    def teardown(self):
        patch.stopall()

        self.mocked_popen.assert_not_called()

    def test_cant_open_features_file_for_writing(self):
        """Capture exceptions in open()."""
        self._mock_dealer_functions(content = "\n".join(self.DEFAULT_CONTENTS))
        dealer = self._load_dealer()

        self.mocked_open.side_effect = [IOError(), DEFAULT, ]
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_not_called()
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

    def test_cant_write_to_feature_file(self):
        """Capture exceptions in write()."""
        self._mock_dealer_functions(content = "\n".join(self.DEFAULT_CONTENTS))
        dealer = self._load_dealer()

        self.mocked_open().write.side_effect = IOError()
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_called_once_with(ANY)
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

    def test_successful_write(self):
        """A successful call to deal() should write the feature and the first scenario."""
        self._mock_dealer_functions(content = "\n".join(self.DEFAULT_CONTENTS))
        dealer = self._load_dealer()

        dealer.deal()

        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_any_call(self.DEFAULT_CONTENTS[0] + "\n")
        self.mocked_open().write.assert_any_call(self.DEFAULT_CONTENTS[1] + "\n")
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

    def test_empty_features_bank(self):
        """Dealing from an empty feature file should give the 'done' message."""
        self._mock_dealer_functions(content = "")
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        assert_in("no more scenarios", self.stdout.lower())

    def test_feature_with_no_scenarios(self):
        """Dealing a "null" feature should give the 'done' message."""
        feature = "Feature: An empty feature"
        self._mock_dealer_functions(content = feature)
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_any_call(feature)
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_in("no more scenarios", self.stdout.lower())

    def test_features_directory_already_exists(self):
        """Test deal() works even if the features directory already exist."""
        self._mock_dealer_functions(content = "\n".join(self.DEFAULT_CONTENTS))
        dealer = self._load_dealer()

        self.mocked_mkdir.side_effect = OSError()
        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_any_call(self.DEFAULT_CONTENTS[0] + "\n")
        self.mocked_open().write.assert_any_call(self.DEFAULT_CONTENTS[1] + "\n")
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

class TestDealNext(BaseDealerTest):
    """Test logic and actions when calling deal() continously."""
    BASE_CONTENTS = [
        "Feature: An awesome feature",
        "  Scenario: First scenario",
        "", # A new-line for the assertion in _deal_first(), with/out more scenarios.
        ]

    def setup(self):
        self._capture_stdout()

    def teardown(self):
        # pylint: disable=no-self-use
        patch.stopall()

    def test_no_more_scenarios(self):
        """If no more scenarios to deal, print 'done' message."""
        self._mock_dealer_functions(content = "\n".join(self.BASE_CONTENTS))
        dealer = self._deal_first()

        dealer.deal()

        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()
        assert_in("no more scenarios", self.stdout.lower())

    def test_should_not_deal_another(self):
        """If a scenario fails, don't deal another scenario."""
        expected_scenario = "  Scenario: Another scenario"
        contents = self.BASE_CONTENTS + [
            expected_scenario,
            "  Scenario: The last scenario",
            ]
        self._mock_dealer_functions(content = "\n".join(contents))
        dealer = self._deal_first()

        self.mocked_popen().returncode = -1
        dealer.deal()

        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call("behave", stdout = PIPE, stderr = PIPE)
        self.mocked_popen().wait.assert_called_once_with()
        assert_in("can't deal", self.stdout.lower())

    def test_should_deal_another(self):
        """When all scenarios pass, deal a new scenario."""
        expected_scenario = "  Scenario: Another scenario"
        contents = self.BASE_CONTENTS + [
            expected_scenario,
            "  Scenario: The last scenario",
            ]
        self._mock_dealer_functions(content = "\n".join(contents))
        dealer = self._deal_first()

        self.mocked_popen().returncode = 0
        dealer.deal()

        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "ab")
        self.mocked_open().write.assert_any_call("\n" + expected_scenario + "\n")
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call("behave", stdout = PIPE, stderr = PIPE)
        self.mocked_popen().wait.assert_called_once_with()
        assert_in("", self.stdout.lower())

    def _deal_first(self):
        """Simulate dealing the first scenario and verify success."""
        dealer = self._load_dealer()
        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_any_call(self.BASE_CONTENTS[0] + "\n")
        self.mocked_open().write.assert_any_call(self.BASE_CONTENTS[1] + "\n")
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

        self.mocked_open.reset_mock()
        self.mocked_mkdir.reset_mock()

        return dealer
