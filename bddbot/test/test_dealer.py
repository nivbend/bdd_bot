from cStringIO import StringIO
from subprocess import PIPE
from nose.tools import assert_raises, assert_in, assert_equal
from mock import ANY, DEFAULT, MagicMock, mock_open, patch
from bddbot import Dealer
from bddbot.dealer import BotError
from bddbot.dealer import FEATURE_BANK_FILENAME, FEATURES_DIRECTORY, OUTPUT_FEATURES_FILENAME

class BaseDealerTest(object):
    @property
    def stdout(self):
        try:
            return self.__stdout.getvalue()
        except AttributeError:
            return None

    def _capture_stdout(self):
        self.__stdout = StringIO()
        patcher = patch("sys.stdout", self.__stdout)
        patcher.start()

        return patcher

    def _mock_dealer_functions(self, content = ""):
        self.mocked_open = mock_open(read_data = content)
        self.mocked_mkdir = MagicMock()
        self.mocked_popen = MagicMock()
        patcher = patch.multiple("bddbot.dealer",
            open = self.mocked_open,
            mkdir = self.mocked_mkdir,
            Popen = self.mocked_popen)

        patcher.start()

        return patcher

    def _load_dealer(self):
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
        self.mocked_open.side_effect = IOError()

        dealer = Dealer()
        with assert_raises(BotError) as error_context:
            dealer.load()

        assert_in("no features bank", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

    def test_successful_call(self):
        dealer = Dealer()
        dealer.load()

        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

    def test_call_load_twice(self):
        dealer = Dealer()
        dealer.load()
        dealer.load()

        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")

class TestDealFirst(BaseDealerTest):
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

    def test_succesfull_write(self):
        self._mock_dealer_functions(content = "\n".join(self.DEFAULT_CONTENTS))
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_open().write.assert_any_call(self.DEFAULT_CONTENTS[0] + "\n")
        self.mocked_open().write.assert_any_call(self.DEFAULT_CONTENTS[1] + "\n")
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

    def test_empty_features_bank(self):
        self._mock_dealer_functions(content = "")
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        assert_in("no more scenarios", self.stdout.lower())

    def test_feature_with_no_scenarios(self):
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
    BASE_CONTENTS = [
        "Feature: An awesome feature",
        "  Scenario: First scenario",
        "", # A new-line for the assertion in _deal_first(), with/out more scenarios.
        ]

    def setup(self):
        self._capture_stdout()

    def teardown(self):
        patch.stopall()

    def test_no_more_scenarios(self):
        self._mock_dealer_functions(content = "\n".join(self.BASE_CONTENTS))
        dealer = self._deal_first()

        dealer.deal()

        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()
        assert_in("no more scenarios", self.stdout.lower())

    def test_should_not_deal_another(self):
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
