"""Test configuration properties."""

import yaml
from nose.tools import assert_equal
from mock import patch
from mock_open import MockOpen
from bddbot.config import BotConfiguration
from bddbot.config import DEFAULT_CONFIG_FILENAME, DEFAULT_BANK_DIRECTORY, DEFAULT_TEST_COMMAND

@patch("bddbot.config.open", new_callable = MockOpen)
def test_no_config_file(mock_open):
    """Load defaults if no configuration file exist."""
    mock_open[DEFAULT_CONFIG_FILENAME].side_effect = IOError()

    config = BotConfiguration()

    mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "rb")
    mock_open[DEFAULT_CONFIG_FILENAME].read.assert_not_called()
    assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
    assert_equal([DEFAULT_BANK_DIRECTORY, ], list(config.bank))

@patch("bddbot.config.open", new_callable = MockOpen)
def test_empty_config_file(mock_open):
    """Load defaults if configuration is empty."""
    mock_open[DEFAULT_CONFIG_FILENAME].read_data = yaml.dump({})

    config = BotConfiguration()

    mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "rb")
    mock_open[DEFAULT_CONFIG_FILENAME].read.assert_called_once_with()
    assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
    assert_equal([DEFAULT_BANK_DIRECTORY, ], list(config.bank))

@patch("bddbot.config.open", new_callable = MockOpen)
def test_multiple_options(mock_open):
    """Supplying multiple options should set all appropriate attributes."""
    bank_path = "/path/to/features.bank"
    test_command = ["behave", "--format=null", ]
    mock_open[DEFAULT_CONFIG_FILENAME].read_data = yaml.dump({
        "test_command": " ".join(test_command),
        "bank": bank_path,
    })

    config = BotConfiguration()

    mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "rb")
    mock_open[DEFAULT_CONFIG_FILENAME].read.assert_called_once_with()
    assert_equal([test_command, ], list(config.test_commands))
    assert_equal([bank_path, ], list(config.bank))

@patch("bddbot.config.open", new_callable = MockOpen)
def test_custom_config_file(mock_open):
    """Test reading from a custom path."""
    config_path = "/path/to/bddbotrc.yml"
    mock_open[config_path].read_data = yaml.dump({})

    config = BotConfiguration(config_path)

    mock_open.assert_called_once_with(config_path, "rb")
    mock_open[config_path].read.assert_called_once_with()
    assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
    assert_equal([DEFAULT_BANK_DIRECTORY, ], list(config.bank))

class TestBankPath(object):
    # pylint: disable=too-few-public-methods
    """Test setting the bank path/s."""
    CASES = [
        (None,                                  [DEFAULT_BANK_DIRECTORY, ]),
        ("",                                    [DEFAULT_BANK_DIRECTORY, ]),
        ([],                                    [DEFAULT_BANK_DIRECTORY, ]),
        ("/path/to/main.bank",                  ["/path/to/main.bank", ]),
        (["banks/single-file.bank", ],          ["banks/single-file.bank", ]),
        (["banks/1.bank", "banks/2.bank", ],    ["banks/1.bank", "banks/2.bank", ]),
    ]

    def test_supply_bank_path(self):
        """Setting the bank value should set the appropriate attribute."""
        for (value, expected_paths) in self.CASES:
            yield self._check_bank_path, value, expected_paths

    @staticmethod
    @patch("bddbot.config.open", new_callable = MockOpen)
    def _check_bank_path(value, expected_paths, mock_open):
        # pylint: disable=missing-docstring
        mock_open[DEFAULT_CONFIG_FILENAME].read_data = yaml.dump({
            "bank": value,
        })

        config = BotConfiguration()

        mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "rb")
        mock_open[DEFAULT_CONFIG_FILENAME].read.assert_called_once_with()
        assert_equal(expected_paths, list(config.bank))
        assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))

class TestBDDTestCommands(object):
    # pylint: disable=too-few-public-methods
    """Test configuration of the test_command option."""
    CASES = [
        (None,                          [DEFAULT_TEST_COMMAND.split(), ]),
        ("",                            [DEFAULT_TEST_COMMAND.split(), ]),
        ("my_tester --some-value=x",    [["my_tester", "--some-value=x", ], ]),
        (["test_1", "test_2 --foo", ],  [["test_1", ], ["test_2", "--foo", ], ]),
    ]

    def test_supplying_test_commands(self):
        """Setting the test_command should set the appropriate attribute."""
        for (test_commands, expected_commands) in self.CASES:
            yield self._check_test_command, test_commands, expected_commands

    @staticmethod
    @patch("bddbot.config.open", new_callable = MockOpen)
    def _check_test_command(test_commands, expected_commands, mock_open):
        # pylint: disable=missing-docstring
        mock_open[DEFAULT_CONFIG_FILENAME].read_data = yaml.dump({
            "test_command": test_commands,
        })

        config = BotConfiguration()

        mock_open.assert_called_once_with(DEFAULT_CONFIG_FILENAME, "rb")
        mock_open[DEFAULT_CONFIG_FILENAME].read.assert_called_once_with()
        assert_equal(expected_commands, list(config.test_commands))
        assert_equal([DEFAULT_BANK_DIRECTORY, ], list(config.bank))
