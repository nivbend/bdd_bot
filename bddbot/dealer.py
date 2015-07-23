from os import mkdir, getcwd
import re
from errors import BotError

REGEX_SCENARIO_START = re.compile(r"^\s*Scenario:", re.MULTILINE)

def _split_bank(bank):
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
        return (bank, [])

    # Add the last scenario.
    scenarios.append(bank[current_start:])

    return (feature, scenarios)

class Dealer(object):
    def __init__(self):
        self.__feature = ""
        self.__scenarios = []

    def assign(self):
        try:
            with open("features.bank", "rb") as bank_input:
                (self.__feature, self.__scenarios) = _split_bank(bank_input.read())
        except IOError:
            raise BotError("No features bank in {:s}".format(getcwd()))

        if not self.__feature:
            print("No more scenarios to deal")

        mkdir("features")
        with open("features/all.feature", "wb") as features:
            features.write(self.__feature)
            if self.__scenarios:
                features.write(self.__scenarios[0])
