"""Test configuration properties."""

from nose.tools import assert_equal, assert_in, assert_raises
from mock import patch
from mock_open import MockOpen
from bddbot.config import BotConfiguration, ConfigError
from bddbot.config import DEFAULT_CONFIG_FILENAME, DEFAULT_BANK_DIRECTORY, DEFAULT_TEST_COMMAND

@patch("bddbot.config.open", new_callable = MockOpen)
def test_no_config_file(mock_open):
    """Load defaults if no configuration file exist."""
    mock_open[DEFAULT_CONFIG_FILENAME].side_effect = IOError()

    config = BotConfiguration()

    mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "r")
    assert_equal([DEFAULT_TEST_COMMAND.split(), ], config.test_commands)
    assert_equal([DEFAULT_BANK_DIRECTORY, ], config.banks)

@patch("bddbot.config.open", new_callable = MockOpen)
def test_empty_config_file(mock_open):
    """Load defaults if configuration is empty."""
    mock_open[DEFAULT_CONFIG_FILENAME].read_data = ""

    config = BotConfiguration()

    mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "r")
    assert_equal([DEFAULT_TEST_COMMAND.split(), ], config.test_commands)
    assert_equal([DEFAULT_BANK_DIRECTORY, ], config.banks)

@patch("bddbot.config.open", new_callable = MockOpen)
def test_multiple_options(mock_open):
    """Supplying multiple options should set all appropriate attributes."""
    bank_path = "/path/to/features.bank"
    test_command = ["behave", "--format=null", ]
    mock_open[DEFAULT_CONFIG_FILENAME].read_data = "\n".join([
        "[paths]",
        "bank: {:s}".format(bank_path),
        "",
        "[test]",
        "run: {:s}".format(" ".join(test_command)),
    ])

    config = BotConfiguration()

    mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "r")
    assert_equal([test_command, ], config.test_commands)
    assert_equal([bank_path, ], config.banks)

@patch("bddbot.config.open", new_callable = MockOpen)
def test_custom_config_file(mock_open):
    """Test reading from a custom path."""
    config_path = "/path/to/bddbotrc.cfg"
    mock_open[config_path].read_data = ""

    config = BotConfiguration(config_path)

    mock_open.assert_called_once_with(config_path, "r")
    assert_equal([DEFAULT_TEST_COMMAND.split(), ], config.test_commands)
    assert_equal([DEFAULT_BANK_DIRECTORY, ], config.banks)

class TestBankPath(object):
    # pylint: disable=too-few-public-methods
    """Test setting the bank path/s."""
    CASES = [
        (["banks/single-file.bank", ],          ["banks/single-file.bank", ]),
        (["banks/1.bank", "banks/2.bank", ],    ["banks/1.bank", "banks/2.bank", ]),
    ]

    @staticmethod
    @patch("bddbot.config.open", new_callable = MockOpen)
    def test_empty_value(mock_open):
        """Verify setting an empty bank path value is an error."""
        mock_open[DEFAULT_CONFIG_FILENAME].read_data = "\n".join([
            "[paths]",
            "bank:",
        ])

        with assert_raises(ConfigError) as error_context:
            BotConfiguration()

        assert_in("no features banks", error_context.exception.message.lower())
        mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "r")

    def test_supply_bank_path(self):
        """Setting the bank value should set the appropriate attribute."""
        for (bank_paths, expected_paths) in self.CASES:
            yield self._check_bank_path, bank_paths, expected_paths

    @staticmethod
    @patch("bddbot.config.open", new_callable = MockOpen)
    def _check_bank_path(bank_paths, expected_paths, mock_open):
        # pylint: disable=missing-docstring
        mock_open[DEFAULT_CONFIG_FILENAME].read_data = "\n".join([
            "[paths]",
            "bank: {:s}".format("\n    ".join(bank_paths)),
        ])

        config = BotConfiguration()

        mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "r")
        assert_equal(expected_paths, config.banks)
        assert_equal([DEFAULT_TEST_COMMAND.split(), ], config.test_commands)

class TestBDDTestCommands(object):
    # pylint: disable=too-few-public-methods
    """Test configuration of the test_command option."""
    CASES = [
        (["", ],                            []),
        (["", "", ],                        []),
        (["", "test_stuff", ],              [["test_stuff", ], ]),
        (["my_tester --some-value=x", ],    [["my_tester", "--some-value=x", ], ]),
        (["test_1", "test_2 --foo", ],      [["test_1", ], ["test_2", "--foo", ], ]),
    ]

    def test_supplying_test_commands(self):
        """Setting the test_command should set the appropriate attribute."""
        for (test_commands, expected_commands) in self.CASES:
            yield self._check_test_command, test_commands, expected_commands

    @staticmethod
    @patch("bddbot.config.open", new_callable = MockOpen)
    def _check_test_command(test_commands, expected_commands, mock_open):
        # pylint: disable=missing-docstring
        mock_open[DEFAULT_CONFIG_FILENAME].read_data = "\n".join([
            "[test]",
            "run: {:s}".format("\n    ".join(test_commands)),
        ])

        config = BotConfiguration()

        mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "r")
        assert_equal(expected_commands, config.test_commands)
        assert_equal([DEFAULT_BANK_DIRECTORY, ], config.banks)
