"""Test the bank module."""

from nose.tools import assert_equal, assert_multi_line_equal, assert_raises, assert_in
from bddbot.bank import Bank, BankParser
from bddbot.errors import BotError

def test_without_header():
    """Test splitting feature files without headers."""
    for (contents, feature, scenarios) in TEST_CASES:
        yield (_check_split_bank, ("", feature, scenarios), contents)

def test_with_header():
    """Test splitting feature files with headers."""
    header_text = "Some header text."
    for (contents, feature, scenarios) in TEST_CASES:
        yield (_check_split_bank,
               (header_text + "\n", feature, scenarios),
               "\n".join([header_text, contents, ]))

def test_multiline_text_error():
    """If a multiline text is started but not finished, raise a parser error."""
    contents = "\n".join([
        "Feature: A multiline text error",
        "    Scenario: A bad scenario",
        "        Given a multiline text that isn't closed:",
        "            \"\"\"",
        "            This multiline text has no end!",
    ])

    parser = BankParser()
    with assert_raises(BotError) as error_context:
        parser.parse(contents)

    assert_in("multiline", error_context.exception.message.lower())

def test_dangling_feature_tags():
    """Raise exception if there are any tags without a feature definition."""
    contents = "\n".join([
        "@dangling",
    ])

    parser = BankParser()
    with assert_raises(BotError) as error_context:
        parser.parse(contents)

    assert_in("dangling tags", error_context.exception.message.lower())

def test_dangling_scenario_tags():
    """Raise exception if there are any dangling tags."""
    contents = "\n".join([
        "Feature: Tags and the end of the file",
        "    Scenario: A bad scenario",
        "        Given we a scenario",
        "        And then some tags come out of nowhere, really",
        "        @this_is_bad",
    ])

    parser = BankParser()
    with assert_raises(BotError) as error_context:
        parser.parse(contents)

    assert_in("dangling tags", error_context.exception.message.lower())

def _check_split_bank(expected, text):
    """Compare two bank splits by their structure."""
    (expected_header, expected_feature, expected_scenarios) = expected
    bank = Bank(text)

    # Verify header.
    assert_multi_line_equal(expected_header, bank.header)

    # Verify feature's text.
    assert_multi_line_equal(expected_feature, bank.feature)

    # Verify each scenario.
    scenario = bank.get_next_scenario()
    count = 0
    while scenario:
        assert_multi_line_equal(scenario, expected_scenarios[count])

        scenario = bank.get_next_scenario()
        count += 1

    # Make sure we don't miss any expected scenarios in feature.
    assert_equal(count, len(expected_scenarios))

# pylint: disable=bad-continuation
TEST_CASES = [
    # Empty file.
    ("", "", []),

    # A feature with no scenarios.
    ("Feature: Empty feature", "Feature: Empty feature", []),

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
