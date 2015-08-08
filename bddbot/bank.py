"""Split a bank (basically a feature file) to its feature definition and its scenarios.
"""
import re

REGEX_FEATURE_START = re.compile(r"^\s*Feature:", re.MULTILINE)
REGEX_SCENARIO_START = re.compile(r"^\s*Scenario:", re.MULTILINE)

class Bank(object):
    """Holds a bank file's parsed contents and allows access to its scenarios in order."""
    def __init__(self, contents):
        (header, feature, scenarios) = _split_bank(contents)

        self.__header = header
        self.__feature = feature
        self.__scenarios = [(False, scenario) for scenario in scenarios]

    def is_fresh(self):
        """Return True if no scenario was dealt yet.

        This also returns True if there aren't any scenarios.
        """
        return not any(was_dealt for (was_dealt, _) in self.__scenarios)

    def is_done(self):
        """Return True if all scenarios in the bank were dealt.

        This also returns True if there aren't any scenarios.
        """
        return all(was_dealt for (was_dealt, _) in self.__scenarios)

    @property
    def header(self):
        """Return anything up the beginning of the feature (comments, etc.)."""
        return self.__header

    @property
    def feature(self):
        """Return the feature text and anything up to the first scenario (including the feature's
        description and the Background section)."""
        return self.__feature

    def get_next_scenario(self):
        """Get the next scenario which wasn't dealt yet.

        This has the effect of marking the scenario returned as dealt.
        """
        for i in xrange(len(self.__scenarios)):
            (was_dealt, scenario) = self.__scenarios[i]

            if not was_dealt:
                self.__scenarios[i] = (True, scenario)
                return scenario

        # No more scenarios.
        return None

def _split_bank(bank):
    """Split a bank (feature) file to three parts: header, feature and scenarios.

    The header is everything preceding the 'Feature:' part.
    The feature is the everything until the first 'Scenario:' part.
    The scenarios are returned as a list.
    """
    # Find the first occurence of 'Feature:'. Everything thing before that is the header.
    feature_match = REGEX_FEATURE_START.search(bank)
    if not feature_match:
        return (bank, "", [])

    (header, bank) = (bank[:feature_match.start()], bank[feature_match.start():])

    # Iterate over every occurence of 'Scenario:' and add everything from its line
    # to the beginning of the next occurence.
    # Everything until the start of the first occurence is considered the feature's
    # header.
    previous_start = None
    feature = ""
    scenarios = []
    for match in REGEX_SCENARIO_START.finditer(bank):
        current_start = match.start()

        # If on the first iteration, consider it the feature's header.
        if previous_start is None:
            feature = bank[:current_start]
        else:
            scenarios.append(bank[previous_start:current_start])

        previous_start = current_start

    # If no scenarios were found in bank, return the whole bank.
    if previous_start is None:
        return (header, bank, [])

    # Add the last scenario.
    scenarios.append(bank[current_start:])

    return (header, feature, scenarios)
