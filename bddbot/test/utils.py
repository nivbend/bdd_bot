"""Utility constructs for testing purposes."""

from collections import defaultdict
from mock import Mock

class BankMockerTest(object):
    # pylint: disable=too-few-public-methods
    """A base test case class to mock out Bank creation."""
    def __init__(self):
        self.mock_banks = defaultdict(Mock)
        self.mock_bank_class = Mock(side_effect = self.__create_bank)

    def teardown(self):
        self.mock_bank_class.reset_mock()
        self.mock_banks.clear()

    def _setup_bank(self, bank, is_fresh, is_done, scenario):
        """Setup a mock bank."""
        # pylint: disable=no-member
        (output_path, header, feature) = self.FEATURES[bank]

        self.mock_banks[bank].is_fresh.return_value = is_fresh
        self.mock_banks[bank].is_done.return_value = is_done
        self.mock_banks[bank].output_path = output_path
        self.mock_banks[bank].header = header
        self.mock_banks[bank].feature = feature
        self.mock_banks[bank].get_next_scenario.return_value = scenario

    def __create_bank(self, *args):
        """Return a mock Bank instance, or creates a new one and adds it to the map."""
        if 1 == len(args):
            is_remote = False
            (key, ) = args
        else:
            is_remote = True
            (_, host, port) = args
            key = "@{host}:{port:d}".format(host = host, port = port)

        return self.mock_banks.setdefault(key, Mock(is_remote = is_remote))
