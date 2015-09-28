"""Exception classes for the package."""

class BotError(Exception):
    """The base exception class for package's exceptions.

    This can also be used 'as-is'.
    """
    pass

class ParsingError(BotError):
    # pylint: disable=missing-docstring
    def __init__(self, message, line):
        super(ParsingError, self).__init__(message)
        self.filename = None
        self.line = line
