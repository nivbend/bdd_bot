"""Store banks' contents (feature test, scenarios, etc.)."""

from .parser import parse_bank
from .errors import BotError

class Bank(object):
    """Holds a bank file's parsed contents and allows access to its scenarios in order."""
    def __init__(self, bank_path):
        try:
            with open(bank_path, "r") as bank_contents:
                (header, feature, scenarios) = parse_bank(bank_contents.read())
        except IOError:
            raise BotError("Couldn't open features bank '{:s}'".format(bank_path))

        self.__output_path = bank_path.replace("bank", "feature")
        self.__header = header
        self.__feature = feature
        self.__scenarios = [(False, scenario) for scenario in scenarios]

        # Ensure output path's extension is 'feature'.
        if not self.__output_path.endswith(".feature"):
            self.__output_path += ".feature"

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
    def output_path(self):
        """The feature's path to write to."""
        return self.__output_path

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
