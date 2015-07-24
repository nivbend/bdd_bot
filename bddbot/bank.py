import re

REGEX_SCENARIO_START = re.compile(r"^\s*Scenario:", re.MULTILINE)

def split_bank(bank):
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
