"""Test configuration properties."""

import yaml
from nose.tools import assert_equal
from mock import patch, mock_open, DEFAULT
from bddbot.config import BotConfiguration
from bddbot.config import DEFAULT_CONFIG_FILENAME, DEFAULT_BANK_PATH, DEFAULT_TEST_COMMAND

class BaseConfigTest(object):
    """The base class for BotConfiguration test-cases."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.mocked_open = None

    def teardown(self):
        # pylint: disable=no-self-use
        # Make sure to stop all patches.
        patch.stopall()

    def _mock_config_functions(self, configuration):
        """Mock builtin functions used in the config module."""
        self.mocked_open = mock_open(read_data = yaml.dump(configuration))
        patcher = patch("bddbot.config.open", self.mocked_open)

        patcher.start()
        self.mocked_open.return_value.read.assert_not_called()

class TestGeneral(BaseConfigTest):
    """Test general use-cases for the BotConfiguration class."""
    def test_no_config_file(self):
        """Load defaults if no configuration file exist."""
        self._mock_config_functions({})
        self.mocked_open.side_effect = [IOError(), DEFAULT, ]

        config = BotConfiguration()

        assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
        assert_equal([DEFAULT_BANK_PATH, ], list(config.bank))
        self.mocked_open.assert_any_call(DEFAULT_CONFIG_FILENAME, "rb")
        self.mocked_open.return_value.read.assert_not_called()

    def test_empty_config_file(self):
        """Load defaults if configuration is empty."""
        self._mock_config_functions({})

        config = BotConfiguration()

        assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
        assert_equal([DEFAULT_BANK_PATH, ], list(config.bank))
        self.mocked_open.assert_any_call(DEFAULT_CONFIG_FILENAME, "rb")
        self.mocked_open.return_value.read.assert_called_once_with()
        self.mocked_open.return_value.read.assert_called_once_with()

    def test_multiple_options(self):
        """Supplying multiple options should set all appropriate attributes."""
        bank_path = "/path/to/features.bank"
        test_command = ["behave", "--format=null", ]
        self._mock_config_functions({
            "test_command": " ".join(test_command),
            "bank": bank_path,
        })

        config = BotConfiguration()

        assert_equal([test_command, ], list(config.test_commands))
        assert_equal([bank_path, ], list(config.bank))
        self.mocked_open.assert_any_call(DEFAULT_CONFIG_FILENAME, "rb")
        self.mocked_open.return_value.read.assert_called_once_with()

    def test_custom_config_file(self):
        """Test reading from a custom path."""
        config_path = "/path/to/bddbotrc"
        self._mock_config_functions({})

        config = BotConfiguration(config_path)

        assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
        assert_equal([DEFAULT_BANK_PATH, ], list(config.bank))
        self.mocked_open.assert_any_call(config_path, "rb")
        self.mocked_open.return_value.read.assert_called_once_with()

class TestBankPath(BaseConfigTest):
    """Test setting the bank path/s."""
    CASES = [
        (None,                                  [DEFAULT_BANK_PATH, ]),
        ("",                                    [DEFAULT_BANK_PATH, ]),
        ([],                                    [DEFAULT_BANK_PATH, ]),
        ("/path/to/main.bank",                  ["/path/to/main.bank", ]),
        (["banks/single-file.bank", ],          ["banks/single-file.bank", ]),
        (["banks/1.bank", "banks/2.bank", ],    ["banks/1.bank", "banks/2.bank", ]),
    ]

    def test_supply_bank_path(self):
        """Setting the bank value should set the appropriate attribute."""
        for (value, expected_paths) in self.CASES:
            yield self._check_bank_path, value, expected_paths

    def _check_bank_path(self, value, expected_paths):
        # pylint: disable=missing-docstring
        self._mock_config_functions({
            "bank": value,
        })

        config = BotConfiguration()

        assert_equal([DEFAULT_TEST_COMMAND.split(), ], list(config.test_commands))
        assert_equal(expected_paths, list(config.bank))
        self.mocked_open.assert_any_call(DEFAULT_CONFIG_FILENAME, "rb")
        self.mocked_open.return_value.read.assert_called_once_with()

class TestBDDTestCommands(BaseConfigTest):
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

    def _check_test_command(self, test_commands, expected_commands):
        # pylint: disable=missing-docstring
        self._mock_config_functions({
            "test_command": test_commands,
        })

        config = BotConfiguration()

        assert_equal(expected_commands, list(config.test_commands))
        assert_equal([DEFAULT_BANK_PATH, ], list(config.bank))
        self.mocked_open.assert_any_call(DEFAULT_CONFIG_FILENAME, "rb")
        self.mocked_open.return_value.read.assert_called_once_with()
