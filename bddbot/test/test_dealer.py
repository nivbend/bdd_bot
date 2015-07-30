from cStringIO import StringIO
from nose.tools import assert_raises, assert_equal
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
        patcher = patch.multiple("bddbot.dealer",
            open = self.mocked_open,
            mkdir = self.mocked_mkdir)

        patcher.start()

        return patcher

    def _load_dealer(self):
        dealer = Dealer()
        dealer.load()

        # Assert actions during load().
        self.mocked_open.assert_called_once_with(FEATURE_BANK_FILENAME, "rb")
        self.mocked_open().read.assert_called_once_with()
        self.mocked_mkdir.assert_not_called()

        # Reset mocks.
        self.mocked_open.reset_mock()
        self.mocked_mkdir.reset_mock()

        return dealer

class TestLoading(BaseDealerTest):
    CONTENT = "Feature: Some awesome stuff"

    def setup(self):
        self._capture_stdout()
        self._mock_dealer_functions(content = self.CONTENT)

    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_not_called()
        assert_equal("", self.stdout)

    def test_no_features_bank_file(self):
        self.mocked_open.side_effect = IOError()

        dealer = Dealer()
        with assert_raises(BotError):
            dealer.load()

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

class TestOutput(BaseDealerTest):
    CONTENT = "Feature: Stuff"

    def setup(self):
        self._capture_stdout()
        self._mock_dealer_functions(content = self.CONTENT)
        self.dealer = self._load_dealer()

    def teardown(self):
        patch.stopall()

        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        assert_equal("", self.stdout)

    def test_features_directory_already_exists(self):
        self.mocked_mkdir.side_effect = OSError()

        self.dealer.deal()

        # If directory already exist, we should proceed as usual.
        self.mocked_open().write.assert_any_call(self.CONTENT)

    def test_cant_open_features_file_for_writing(self):
        self.mocked_open.side_effect = [IOError(), DEFAULT, ]

        with assert_raises(BotError):
            self.dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        self.mocked_open().write.assert_not_called()

    def test_cant_write_to_feature_file(self):
        self.mocked_open().write.side_effect = IOError()

        with assert_raises(BotError):
            self.dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        self.mocked_open().write.assert_called_once_with(ANY)
