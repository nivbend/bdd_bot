"""Test the bank module."""

import socket
from nose.tools import assert_equal, assert_multi_line_equal, assert_raises, assert_in
from mock import patch
from mock_open import MockOpen
from bddbot.bank import Bank, RemoteBank, ConnectionError
from bddbot.parser import parse_bank
from bddbot.errors import BotError, ParsingError
from bddbot.test.constants import BANK_PATH_1, FEATURE_PATH_1, HOST, PORT, CLIENT

class TestBankParsing(object):
    """Test parsing of feature bank files."""
    @staticmethod
    def test_multiline_text_error():
        # If a multiline text is started but not finished, raise a parser error.
        contents = "\n".join([
            "Feature: A multiline text error",
            "    Scenario: A bad scenario",
            "        Given a multiline text that isn't closed:",
            "            \"\"\"",
            "            This multiline text has no end!",
        ])

        with assert_raises(ParsingError) as error_context:
            parse_bank(contents)

        assert_in("multiline", error_context.exception.message.lower())
        assert_equal(4, error_context.exception.line)

    @staticmethod
    def test_dangling_feature_tags():
        # Raise exception if there are any tags without a feature definition.
        contents = "\n".join([
            "@dangling",
        ])

        with assert_raises(ParsingError) as error_context:
            parse_bank(contents)

        assert_in("dangling tags", error_context.exception.message.lower())
        assert_equal(1, error_context.exception.line)

    @staticmethod
    def test_dangling_scenario_tags():
        contents = "\n".join([
            "Feature: Tags and the end of the file",
            "    Scenario: A bad scenario",
            "        Given we a scenario",
            "        And then some tags come out of nowhere, really",
            "        @this_is_bad",
        ])

        with assert_raises(ParsingError) as error_context:
            parse_bank(contents)

        assert_in("dangling tags", error_context.exception.message.lower())
        assert_equal(5, error_context.exception.line)

class TestLocalBank(object):
    """Test local bank operations."""
    @staticmethod
    @patch("bddbot.bank.open", new_callable = MockOpen)
    def test_error_openning_file(mocked_open):
        mocked_open[BANK_PATH_1].side_effect = IOError()

        with assert_raises(BotError) as error_context:
            Bank(BANK_PATH_1)

        mocked_open.assert_called_once_with(BANK_PATH_1, "r")
        mocked_open[BANK_PATH_1].read.assert_not_called()
        assert_in("couldn't open features bank", error_context.exception.message.lower())

    @staticmethod
    @patch("bddbot.bank.open", new_callable = MockOpen)
    def test_error_reading_file(mocked_open):
        mocked_open[BANK_PATH_1].read.side_effect = IOError()

        with assert_raises(BotError) as error_context:
            Bank(BANK_PATH_1)

        mocked_open.assert_called_once_with(BANK_PATH_1, "r")
        mocked_open[BANK_PATH_1].read.assert_called_once_with()
        assert_in("couldn't open features bank", error_context.exception.message.lower())

    def test_without_header(self):
        for (contents, is_fresh, is_done, feature, scenarios) in TEST_CASES:
            yield (self._check_bank_splitting,
                   ("", feature, scenarios),
                   contents,
                   is_fresh, is_done)

    def test_with_header(self):
        header_text = "Some header text."
        for (contents, is_fresh, is_done, feature, scenarios) in TEST_CASES:
            yield (self._check_bank_splitting,
                   (header_text + "\n", feature, scenarios),
                   "\n".join([header_text, contents, ]),
                   is_fresh, is_done)

    @staticmethod
    def _check_bank_splitting(expected, contents, is_fresh, is_done):
        """Compare two bank splits by their structure."""
        (expected_header, expected_feature, expected_scenarios) = expected

        mocked_open = MockOpen()
        mocked_open[BANK_PATH_1].read_data = contents
        with patch("bddbot.bank.open", mocked_open):
            bank = Bank(BANK_PATH_1)

        mocked_open.assert_called_once_with(BANK_PATH_1, "r")
        mocked_open[BANK_PATH_1].read.assert_called_once_with()

        assert_equal(is_fresh, bank.is_fresh())
        assert_equal(is_done, bank.is_done())
        assert_equal(FEATURE_PATH_1, bank.output_path)
        assert_multi_line_equal(expected_header, bank.header)
        assert_multi_line_equal(expected_feature, bank.feature)

        all_scenarios = list(iter(bank.get_next_scenario, None))
        for (expected_scenario, actual_scenario) in zip(expected_scenarios, all_scenarios):
            assert_multi_line_equal(expected_scenario, actual_scenario)

class TestRemoteBank(object):
    """Test connection to a remote bank."""
    def __init__(self):
        self.bank = None
        self.mocked_proxy = None

    def setup(self):
        with patch("bddbot.bank.ServerProxy") as mocked_proxy_class:
            self.bank = RemoteBank(CLIENT, HOST, PORT)

        mocked_proxy_class.assert_called_once_with("http://{}:{:d}".format(HOST, PORT))
        self.mocked_proxy = mocked_proxy_class.return_value

    def test_access(self):
        self.bank.is_fresh()
        self.mocked_proxy.is_fresh.assert_called_once_with(CLIENT)

        self.bank.is_done()
        self.mocked_proxy.is_done.assert_called_once_with(CLIENT)

        _ = self.bank.output_path
        self.mocked_proxy.get_output_path.assert_called_once_with(CLIENT)

        _ = self.bank.header
        self.mocked_proxy.get_header.assert_called_once_with(CLIENT)

        _ = self.bank.feature
        self.mocked_proxy.get_feature.assert_called_once_with(CLIENT)

        self.bank.get_next_scenario()
        self.mocked_proxy.get_next_scenario.assert_called_once_with(CLIENT)

    def test_access_error(self):
        self.mocked_proxy.is_fresh.side_effect = socket.error()
        with assert_raises(ConnectionError):
            self.bank.is_fresh()

        self.mocked_proxy.is_done.side_effect = socket.error()
        with assert_raises(ConnectionError):
            self.bank.is_done()

        self.mocked_proxy.get_output_path.side_effect = socket.error()
        with assert_raises(ConnectionError):
            _ = self.bank.output_path

        self.mocked_proxy.get_header.side_effect = socket.error()
        with assert_raises(ConnectionError):
            _ = self.bank.header

        self.mocked_proxy.get_feature.side_effect = socket.error()
        with assert_raises(ConnectionError):
            _ = self.bank.feature

        self.mocked_proxy.get_next_scenario.side_effect = socket.error()
        with assert_raises(ConnectionError):
            self.bank.get_next_scenario()

    def test_operation_error(self):
        self.mocked_proxy.is_fresh.side_effect = socket.error()

        with assert_raises(ConnectionError) as error_context:
            self.bank.is_fresh()

        assert_in("failed on remote", error_context.exception.message.lower())
        assert_equal("is_fresh", error_context.exception.operation)

# pylint: disable=bad-continuation
TEST_CASES = [
    # Empty file.
    ("", False, True, "", []),

    # A feature with no scenarios.
    ("Feature: Empty feature", False, True, "Feature: Empty feature", []),

    # A feature with a single scenario.
    ("\n".join([
         "Feature: A simple feature",
         "    This is the feature's description.",
         "    It can go on for several lines.",
         "",
         "    Scenario: A single scenario",
         "        Given the past",
         "        When stuff happen",
         "        Then the future will come to be",
     ]),
     True, False,
     "\n".join([
         "Feature: A simple feature",
         "    This is the feature's description.",
         "    It can go on for several lines.",
         "\n",
     ]),
     ["\n".join([
          "    Scenario: A single scenario",
          "        Given the past",
          "        When stuff happen",
          "        Then the future will come to be",
      ]),
     ],
    ),

    # A feature with three scenarios.
    ("\n".join([
         "Feature: A slightly bigger feature",
         "    Scenario: The first scenario",
         "    Scenario: The second scenario",
         "    Scenario: The third scenario",
     ]),
     True, False,
     "Feature: A slightly bigger feature\n",
     ["    Scenario: The first scenario\n",
      "    Scenario: The second scenario\n",
      "    Scenario: The third scenario",
     ],
    ),

    # A feature with tags.
    ("\n".join([
         "@awesome",
         "@cool @groovy",
         "Feature: Having tags",
         "    Scenario: Something to test",
     ]),
     True, False,
     "\n".join([
         "@awesome",
         "@cool @groovy",
         "Feature: Having tags",
         "",
     ]),
     ["    Scenario: Something to test", ],
    ),

    # A very complex example, with a background and scenario outlines and tags.
    ("\n".join([
         "Feature: A very complex feature indeed",
         "    If we can parse this baby, we can probably parse anything.",
         "",
         "    Background:",
         "        Given the long, forgotten past",
         "        And some stuff best not remembered",
         "",
         "    @first_scenario",
         "    Scenario: The very first scenario",
         "        Given we have a few scenarios",
         "        When we split the feature file",
         "        But don't check it properly",
         "        Then we may get a false-positive",
         "        And we suck as testers",
         "",
         "    @outline @data_table",
         "    Scenario Outline: Some cases",
         "        Given <value>",
         "        When <action>",
         "        Then <result>",
         "        | value | action | result |",
         "        | A1    | B1     | C1     |",
         "        | A2    | B2     | C2     |",
         "        | A3    | B3     | C3     |",
         "",
         "    @tricky",
         "    @complex",
         "    Scenario: Another scenario",
         "        Given some multiline text:",
         "            \"\"\"",
         "            This is some cool text.",
         "            But wait, there's more!",
         "            \"\"\"",
         "        And even a data table",
         "            | a | b |",
         "            | 1 | 2 |",
         "            | 3 | 4 |",
         "        When we try to challenge our parser",
         "        Then it won't fail us",
         "",
         "    Scenario: The last scenario",
         "        Given more text:",
         "            '''",
         "            Feature: A fake feature",
         "                Scenario: this is a fake scenario",
         "            '''",
         "        When we try to challenge our parser",
         "        Then it won't fail us",
     ]),
     True, False,
     "\n".join([
         "Feature: A very complex feature indeed",
         "    If we can parse this baby, we can probably parse anything.",
         "",
         "    Background:",
         "        Given the long, forgotten past",
         "        And some stuff best not remembered",
         "\n",
     ]),
     ["\n".join([
          "    @first_scenario",
          "    Scenario: The very first scenario",
          "        Given we have a few scenarios",
          "        When we split the feature file",
          "        But don't check it properly",
          "        Then we may get a false-positive",
          "        And we suck as testers",
          "\n",
      ]),
      "\n".join([
          "    @outline @data_table",
          "    Scenario Outline: Some cases",
          "        Given <value>",
          "        When <action>",
          "        Then <result>",
          "        | value | action | result |",
          "        | A1    | B1     | C1     |",
          "        | A2    | B2     | C2     |",
          "        | A3    | B3     | C3     |",
          "\n",
      ]),
      "\n".join([
          "    @tricky",
          "    @complex",
          "    Scenario: Another scenario",
          "        Given some multiline text:",
          "            \"\"\"",
          "            This is some cool text.",
          "            But wait, there's more!",
          "            \"\"\"",
          "        And even a data table",
          "            | a | b |",
          "            | 1 | 2 |",
          "            | 3 | 4 |",
          "        When we try to challenge our parser",
          "        Then it won't fail us",
          "\n",
      ]),
      "\n".join([
          "    Scenario: The last scenario",
          "        Given more text:",
          "            '''",
          "            Feature: A fake feature",
          "                Scenario: this is a fake scenario",
          "            '''",
          "        When we try to challenge our parser",
          "        Then it won't fail us",
      ]),
     ],
    ),
]
