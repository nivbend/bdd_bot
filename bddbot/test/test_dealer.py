from os import strerror
from nose.tools import assert_raises
from mock import ANY, DEFAULT, MagicMock, mock_open, patch
from bddbot import Dealer
from bddbot.dealer import BotError
from bddbot.dealer import FEATURE_BANK_FILENAME, FEATURES_DIRECTORY, OUTPUT_FEATURES_FILENAME

def test_no_features_bank_file():
    dealer = Dealer()

    mocked_open = mock_open()
    mocked_open.side_effect = IOError()
    with patch("bddbot.dealer.open", mocked_open):
        with assert_raises(BotError):
            dealer.assign()

    mocked_open.assert_called_once_with("features.bank", "rb")

class TestOutput(object):
    CONTENT = "Feature: Stuff"

    def setup(self):
        self.mocked_open = mock_open(read_data = self.CONTENT)
        self.mocked_mkdir = MagicMock()
        patcher = patch.multiple("bddbot.dealer",
            open = self.mocked_open,
            mkdir = self.mocked_mkdir)

        patcher.start()

        self.dealer = Dealer()

    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)
        self.mocked_open.assert_any_call(FEATURE_BANK_FILENAME, "rb")
        self.mocked_open().read.assert_called_once_with()
        self.mocked_open.assert_any_call(OUTPUT_FEATURES_FILENAME, "wb")

    def test_features_directory_already_exists(self):
        self.mocked_mkdir.side_effect = OSError()

        self.dealer.assign()

        # If directory already exist, we should proceed as usual.
        self.mocked_open().write.assert_any_call(self.CONTENT)

    def test_cant_open_features_file_for_writing(self):
        self.mocked_open.side_effect = [DEFAULT, IOError(), DEFAULT, DEFAULT, ]

        with assert_raises(BotError):
            self.dealer.assign()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        self.mocked_open().write.assert_not_called()

    def test_cant_write_to_feature_file(self):
        self.mocked_open().write.side_effect = IOError()

        with assert_raises(BotError):
            self.dealer.assign()

        # First call to write() raised an IOError which was caught and translated.
        self.mocked_open().write.assert_called_once_with(ANY)
