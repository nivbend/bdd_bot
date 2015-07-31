"""Test the bank module."""
# pylint: disable=invalid-name

import itertools
from nose.tools import assert_equal, assert_multi_line_equal
from bddbot.dealer import split_bank

def test_without_header():
    """Test splitting feature files without headers."""
    for (contents, feature, scenarios) in TEST_CASES:
        yield (_check_split_bank, ("", feature, scenarios), contents)

def test_with_header():
    """Test splitting feature files with headers."""
    header_text = "Some header text.\n"
    for (contents, feature, scenarios) in TEST_CASES:
        yield (_check_split_bank,
               (header_text, feature, scenarios),
               "\n".join([header_text, contents, ]))

def _strip_whitespace(text):
    """Rebuild multi-line string without leading/trailing spaces or empty lines."""
    return "\n".join(
        " ".join(line.strip().split())  # Strip leading/trailing whitespace and multiple spaces.
        for line in text.splitlines()
        if line.strip())                # Ignore empty lines.

def _assert_equal_without_spaces(expected, actual):
    """Assert two strings are equal, ignoring whitespace."""
    assert_multi_line_equal(
        _strip_whitespace(expected),
        _strip_whitespace(actual))

def _check_split_bank(expected, text):
    """Compare two bank splits by their structure."""
    (expected_header, expected_feature, expected_scenarios) = expected
    (actual_header, actual_feature, actual_scenarios) = split_bank(text)

    # Verify header.
    _assert_equal_without_spaces(expected_header, actual_header)

    # Verify feature's text.
    _assert_equal_without_spaces(expected_feature, actual_feature)

    # Make sure we don't miss any expected scenarios in feature.
    assert_equal(len(actual_scenarios), len(expected_scenarios))
    itertools.imap(
        _assert_equal_without_spaces,
        expected_scenarios,
        actual_scenarios)

TEST_CASES = [
    # Empty file.
    ("", "", []),

    # One feature with no scenarios.
    ("Feature: Empty feature", "Feature: Empty feature", []),

    # One feature, one full scenario.
    # Other tests will have single line scenarios for readability.
    ("""Feature: A simple feature
          Scenario: A single scenario
            Given the past
            When stuff happen
            Then the future will come to be""",
     "Feature: A simple feature",
     ["""Scenario: A single scenario
           Given the past
           When stuff happen
           Then the future will come to be""",
     ],
    ),

    # One feature, three scenarios.
    ("""Feature: A simple feature
          Scenario: First scenario
          Scenario: Second scenario
          Scenario: Third scenario""",
     "Feature: A simple feature",
     ["Scenario: First scenario",
      "Scenario: Second scenario",
      "Scenario: Third scenario",
     ],
    ),
]
