"""Test configuration properties."""

from nose.tools import assert_equal, assert_in, assert_raises
from mock import patch
from mock_open import MockOpen
from bddbot.config import BotConfiguration, ConfigError
from bddbot.config import CONFIG_FILENAME
from bddbot.test.constants import BANK_PATH_1, DEFAULT_TEST_COMMANDS

class BaseConfigTest(object):
    # pylint: disable=missing-docstring
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.config = None

    def _create_config(self, contents, filename = CONFIG_FILENAME, side_effect = None):
        """Configure from a mocked file."""
        mocked_open = MockOpen()
        mocked_open[filename].read_data = contents
        mocked_open[filename].side_effect = side_effect

        with patch("bddbot.config.open", mocked_open):
            self.config = BotConfiguration(filename)

        mocked_open.assert_called_once_with(filename, "r")

class TestConfigPath(BaseConfigTest):
    def test_no_config_file(self):
        self._create_config("", side_effect = IOError())
        assert_equal(DEFAULT_TEST_COMMANDS, self.config.tests)
        assert_equal([], self.config.banks)

    def test_empty_config_file(self):
        self._create_config("")
        assert_equal(DEFAULT_TEST_COMMANDS, self.config.tests)
        assert_equal([], self.config.banks)

    def test_custom_config_path(self):
        tests = ["behave", "--format=null", ]
        contents = "\n".join([
            "[paths]",
            "bank: %s" % (BANK_PATH_1, ),
            "",
            "[test]",
            "run: %s" % (" ".join(tests), ),
        ])

        self._create_config(contents, filename = "/path/to/bddbot.cfg")

        assert_equal([BANK_PATH_1, ], self.config.banks)
        assert_equal([tests, ], self.config.tests)

class TestBankPath(BaseConfigTest):
    # pylint: disable=too-few-public-methods
    CASES = [
        (["banks/single-file.bank", ],          ["banks/single-file.bank", ]),
        (["banks/1.bank", "banks/2.bank", ],    ["banks/1.bank", "banks/2.bank", ]),
    ]

    def test_empty_value(self):
        # Verify setting an empty bank path value is an error.
        with assert_raises(ConfigError) as error_context:
            self._create_config("\n".join([
                "[paths]",
                "bank:",
            ]))

        assert_in("no features banks", error_context.exception.message.lower())

    def test_set_bank_path(self):
        for (bank_paths, expected_paths) in self.CASES:
            yield (self._check_bank_path, bank_paths, expected_paths)

    def _check_bank_path(self, bank_paths, expected_paths):
        self._create_config("\n".join([
            "[paths]",
            "bank: {:s}".format("\n    ".join(bank_paths)),
        ]))

        assert_equal(expected_paths, self.config.banks)

class TestBDDTestCommands(BaseConfigTest):
    # pylint: disable=too-few-public-methods
    CASES = [
        (["", ],                            []),
        (["", "", ],                        []),
        (["", "test_stuff", ],              [["test_stuff", ], ]),
        (["my_tester --some-value=x", ],    [["my_tester", "--some-value=x", ], ]),
        (["test_1", "test_2 --foo", ],      [["test_1", ], ["test_2", "--foo", ], ]),
    ]

    def test_set_test_commands(self):
        for (actual_commands, expected_commands) in self.CASES:
            yield (self._check_test_command, actual_commands, expected_commands)

    def _check_test_command(self, actual_commands, expected_commands):
        self._create_config("\n".join([
            "[test]",
            "run: {:s}".format("\n    ".join(actual_commands)),
        ]))

        assert_equal(expected_commands, self.config.tests)
