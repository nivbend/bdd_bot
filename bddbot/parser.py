"""Split a bank (basically a feature file) to its feature definition and its scenarios."""

import re
from .errors import ParsingError

REGEX_FEATURE_START = re.compile(r"^\s*Feature:")
REGEX_TAGS = re.compile(r"^\s*(?:@\w+(?:\s+@\w+)*)")
REGEX_SCENARIO_START = re.compile(r"^\s*Scenario(?: Outline)?:")
REGEX_MULTILINE_START = re.compile(r"^\s*(?:\"\"\"|''')")

(STATE_HEADER,
 STATE_FEATURE_TAGS,
 STATE_FEATURE,
 STATE_SCENARIO_TAGS,
 STATE_SCENARIO,
 STATE_MULTILINE) = range(6)

def parse_bank(contents):
    """Parse the contents of a bank file."""
    parser = BankParser(contents)
    return parser.parse()

class BankParser(object):
    # pylint: disable=too-few-public-methods
    # pylint: disable=too-many-instance-attributes
    """A simple feature parser.

    Since we only really need to know mostly when the feature/scenarios start we don't really
    require a full Gherkin parser. This parser mostly takes care of separating the contents of the
    file to the header (anything before the beginning of the feature), the feature's body (including
    the description and background section), and the scenarios (including multiline texts, data
    tables and scenario outlines' examples).
    """

    def __init__(self, contents):
        self.header = []
        self.feature = []
        self.scenarios = []

        self.__contents = contents.splitlines()
        self.__state = STATE_HEADER
        self.__line = 0
        self.__multiline_start = 0
        self.__multiline_delimiter = None
        self.__tags = []
        self.__callbacks = {
            STATE_HEADER: self.__parse_header,
            STATE_FEATURE_TAGS: self.__parse_feature_tags,
            STATE_FEATURE: self.__parse_feature,
            STATE_SCENARIO_TAGS: self.__parse_scenario_tags,
            STATE_SCENARIO: self.__parse_scenario,
            STATE_MULTILINE: self.__parse_multiline_text,
        }

    @property
    def __parse_line(self):
        """Return a parsing callback according to the current state."""
        return self.__callbacks[self.__state]

    def parse(self):
        """Parse the contents of a bank file."""
        for line in self.__contents:
            self.__line += 1
            self.__parse_line(line)

        if STATE_MULTILINE == self.__state:
            raise ParsingError("Multiline text has no end", self.__multiline_start)

        if self.__state in (STATE_FEATURE_TAGS, STATE_SCENARIO_TAGS, ):
            raise ParsingError("Dangling tags", self.__line)

        self.__normalize()

        return (self.header, self.feature, self.scenarios)

    def __parse_header(self, line):
        """Add the beginning of a file up to the Feature section to the header part."""
        if REGEX_TAGS.match(line):
            self.__state = STATE_FEATURE_TAGS
            self.__parse_line(line)

        elif REGEX_FEATURE_START.match(line):
            self.__state = STATE_FEATURE
            self.__parse_line(line)

        else:
            self.header.append(line)

    def __parse_feature_tags(self, line):
        """Add tags before the beginning of a feature to the feature once it is reached."""
        if REGEX_TAGS.match(line):
            self.feature.append(line)

        elif REGEX_FEATURE_START.match(line):
            self.__state = STATE_FEATURE
            self.__parse_line(line)

        else:
            raise ParsingError(
                "Invalid line (should be tags or feature): {:s}".format(line.lstrip()),
                self.__line)

    def __parse_feature(self, line):
        """Add everything up to the beginning of the first scenario to the feature's body."""
        if REGEX_TAGS.match(line):
            self.__state = STATE_SCENARIO_TAGS
            self.__tags = []
            self.__parse_line(line)

        elif REGEX_SCENARIO_START.match(line):
            self.__state = STATE_SCENARIO
            self.__parse_line(line)

        else:
            self.feature.append(line)

    def __parse_scenario_tags(self, line):
        """Add tags before the beginning of a scenario to the scenario once it is reached."""
        if REGEX_TAGS.match(line):
            self.__tags.append(line)

        elif REGEX_SCENARIO_START.match(line):
            self.__state = STATE_SCENARIO
            self.scenarios.append(self.__tags)
            self.scenarios[-1].append(line)

        else:
            raise ParsingError(
                "Invalid line (should be tags or scenario): {:s}".format(line.lstrip()),
                self.__line)

    def __parse_scenario(self, line):
        """Add the body of the current scenario up till the next scenario starts.

        We take care to notice multiline texts since those might have Feature/Scenario sections
        in them that might confuse the parser.
        """
        if REGEX_TAGS.match(line):
            self.__state = STATE_SCENARIO_TAGS
            self.__tags = [line, ]
            return

        if REGEX_SCENARIO_START.match(line):
            self.scenarios.append([])

        if REGEX_MULTILINE_START.match(line):
            self.__state = STATE_MULTILINE
            self.__multiline_start = self.__line
            self.__multiline_delimiter = line.lstrip()[:3]

        self.scenarios[-1].append(line)

    def __parse_multiline_text(self, line):
        """Until the end of the multiline text, add the line to the current scenario."""
        if line.lstrip().startswith(self.__multiline_delimiter):
            self.__state = STATE_SCENARIO
            self.__multiline_start = 0
            self.__multiline_delimiter = None

        self.scenarios[-1].append(line)

    def __normalize(self):
        """Normalize values from lists of lines to actual texts.

        Each section (header, feature of scenarios) should end with a newline if there's
        anything after it.
        """
        self.header = "\n".join(self.header)
        if self.header:
            self.header += "\n"

        self.feature = "\n".join(self.feature)
        if self.scenarios:
            self.feature += "\n"

            for (i, scenario) in enumerate(self.scenarios[:-1]):
                self.scenarios[i] = "\n".join(scenario) + "\n"
            self.scenarios[-1] = "\n".join(self.scenarios[-1])
