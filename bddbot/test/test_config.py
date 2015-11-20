"""Test configuration properties."""

from nose.tools import assert_equal, assert_in, assert_is_none, assert_raises
from mock import Mock, patch
from bddbot.config import BotConfiguration, ConfigError
from bddbot.config import CONFIG_FILENAME
from bddbot.test.constants import BANK_PATH_1, DEFAULT_TEST_COMMANDS, HOST, PORT

class BaseConfigTest(object):
    # pylint: disable=missing-docstring
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.config = None
        self.mocked_config_parser_class = Mock()
        self.mocked_config_parser = self.mocked_config_parser_class.return_value

    def teardown(self):
        self.config = None
        self.mocked_config_parser_class.reset_mock()
        self.mocked_config_parser.reset_mock()

    def _create_config(self, contents, filename = CONFIG_FILENAME):
        """Configure from a mocked file."""
        def _has_option(section, value):
            if section not in contents:
                return False
            return value in contents[section]

        def _get(section, value):
            return contents[section][value]

        def _getint(section, value):
            return int(_get(section, value))

        self.mocked_config_parser.read.return_value = [filename, ]
        self.mocked_config_parser.has_option.side_effect = _has_option
        self.mocked_config_parser.get.side_effect = _get
        self.mocked_config_parser.getint.side_effect = _getint

        with patch("bddbot.config.ConfigParser", self.mocked_config_parser_class):
            self.config = BotConfiguration(filename)

        self.mocked_config_parser_class.assert_called_once_with()
        self.mocked_config_parser.read.assert_called_once_with([filename, ])

class TestConfigPath(BaseConfigTest):
    def test_default_path(self):
        self.mocked_config_parser.has_option.side_effect = lambda section, value: False
        with patch("bddbot.config.ConfigParser", self.mocked_config_parser_class):
            BotConfiguration()

        self.mocked_config_parser_class.assert_called_once_with()
        self.mocked_config_parser.read.assert_called_once_with([CONFIG_FILENAME, ])

    def test_no_file(self):
        self.mocked_config_parser.read.return_value = []
        self.mocked_config_parser.has_option.side_effect = lambda section, value: False
        with patch("bddbot.config.ConfigParser", self.mocked_config_parser_class):
            self.config = BotConfiguration()

        self.mocked_config_parser_class.assert_called_once_with()
        self.mocked_config_parser.read.assert_called_once_with([CONFIG_FILENAME, ])
        assert_equal(DEFAULT_TEST_COMMANDS, self.config.tests)
        assert_equal([], self.config.banks)

    def test_empty(self):
        self._create_config({})
        assert_equal(DEFAULT_TEST_COMMANDS, self.config.tests)
        assert_equal([], self.config.banks)

    def test_custom_path(self):
        tests = ["behave", "--format=null", ]
        contents = {
            "paths": {
                "bank": BANK_PATH_1,
            },
            "test": {
                "run": " ".join(tests),
            },
        }

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
            self._create_config({"paths": {"bank": "", }, })

        assert_in("no features banks", error_context.exception.message.lower())

    def test_set_bank_path(self):
        for (bank_paths, expected_paths) in self.CASES:
            yield (self._check_bank_path, bank_paths, expected_paths)

    def _check_bank_path(self, bank_paths, expected_paths):
        self._create_config({
            "paths": {
                "bank": "\n".join(bank_paths),
            },
        })

        assert_equal(expected_paths, self.config.banks)

class TestTestCommands(BaseConfigTest):
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
        self._create_config({
            "test": {
                "run": "\n".join(actual_commands),
            },
        })

        assert_equal(expected_commands, self.config.tests)
        assert_equal([], self.config.banks)

class TestServer(BaseConfigTest):
    def test_empty_value(self):
        self._create_config({"server": {}, })

        assert_is_none(self.config.host)
        assert_is_none(self.config.port)

    def test_set_host(self):
        self._create_config({
            "server": {
                "host": HOST,
            },
        })

        assert_equal(HOST, self.config.host)

    def test_set_port(self):
        self._create_config({
            "server": {
                "port": PORT,
            },
        })

        assert_equal(PORT, self.config.port)
