"""Test serving scenarios from a remote bot server."""

from threading import Thread
from nose.tools import assert_equal, assert_items_equal
from mock import Mock, call, patch, ANY
from bddbot.server import BankServer
from bddbot.test.utils import BankMockerTest
from bddbot.test.constants import BANK_PATH_1, BANK_PATH_2, FEATURE_PATH_1, FEATURE_PATH_2
from bddbot.test.constants import HOST, PORT, CLIENT

QUERIES = {
    "is_fresh",
    "is_done",
    "get_output_path",
    "get_header",
    "get_feature",
    "get_next_scenario",
}

(HEADER_1, FEATURE_1, SCENARIO_1_1, SCENARIO_1_2) = (
    "# Some header text",
    "Feature: Feature #1",
    "    Scenario: Scenario #1-1",
    "    Scenario: Scenario #1-2",
)

(FEATURE_2, SCENARIO_2_1) = (
    "Feature: Feature #2",
    "    Scenario: Scenario #2-1",
)

class BaseServerTest(BankMockerTest):
    # pylint: disable=too-few-public-methods
    """A base test case class to mock out BankServer handling."""
    def __init__(self):
        super(BaseServerTest, self).__init__()
        self.server = None
        self.mock_socket = Mock()

        self.mock_socket.fileno.return_value = 0

    def teardown(self):
        super(BaseServerTest, self).__init__()
        self.server = None

    def _create_server(self, banks):
        """Create a new server instance."""
        with patch("bddbot.server.Bank", self.mock_bank_class), \
             patch("bddbot.server.gethostname", return_value = HOST), \
             patch("socket.socket", return_value = self.mock_socket), \
             patch("fcntl.fcntl"):
            self.server = BankServer(PORT, banks)

        self.mock_bank_class.assert_has_calls([call(path) for path in banks])

class TestBankServer(BaseServerTest):
    FEATURES = {
        None: (None, "", ""),
        BANK_PATH_1: (FEATURE_PATH_1, HEADER_1, FEATURE_1),
        BANK_PATH_2: (FEATURE_PATH_2, "", FEATURE_2),
    }

    def __init__(self):
        super(TestBankServer, self).__init__()

    def teardown(self):
        super(TestBankServer, self).teardown()

    def test_serving(self):
        for banks in ([], [BANK_PATH_1, ], [BANK_PATH_1, BANK_PATH_2, ]):
            yield (self._check_serving, banks)

    def test_single_client(self):
        self._create_server([BANK_PATH_1, BANK_PATH_2, ])

        # Deal the first scenario from the first bank.
        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self.__verify_properties(CLIENT, True, False, BANK_PATH_1, SCENARIO_1_1)
        self.mock_banks[BANK_PATH_1].is_fresh.assert_not_called()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_called_once_with()
        self.mock_banks[BANK_PATH_2].is_fresh.assert_not_called()
        self.mock_banks[BANK_PATH_2].get_next_scenario.assert_not_called()
        self.mock_banks[BANK_PATH_1].reset_mock()
        self.mock_banks[BANK_PATH_2].reset_mock()

        # Deal another scenario from the same bank.
        self._setup_bank(BANK_PATH_1, False, False, SCENARIO_1_2)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self.__verify_properties(CLIENT, False, False, BANK_PATH_1, SCENARIO_1_2)
        self.mock_banks[BANK_PATH_1].is_fresh.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_called_once_with()
        self.mock_banks[BANK_PATH_2].is_fresh.assert_not_called()
        self.mock_banks[BANK_PATH_2].get_next_scenario.assert_not_called()
        self.mock_banks[BANK_PATH_1].reset_mock()
        self.mock_banks[BANK_PATH_2].reset_mock()

        # Start dealing from the second bank after the first is done, marking as fresh again.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self.__verify_properties(CLIENT, True, False, BANK_PATH_2, SCENARIO_2_1)
        self.mock_banks[BANK_PATH_1].is_fresh.assert_not_called()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mock_banks[BANK_PATH_2].is_fresh.assert_called_once_with()
        self.mock_banks[BANK_PATH_2].get_next_scenario.assert_called_once_with()
        self.mock_banks[BANK_PATH_1].reset_mock()
        self.mock_banks[BANK_PATH_2].reset_mock()

        # Finished dealing.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, False, True, None)
        self.__verify_properties(CLIENT, False, True, None, None)
        self.mock_banks[BANK_PATH_1].is_fresh.assert_not_called()
        self.mock_banks[BANK_PATH_1].get_next_scenario.assert_not_called()
        self.mock_banks[BANK_PATH_2].is_fresh.assert_not_called()
        self.mock_banks[BANK_PATH_2].get_next_scenario.assert_not_called()

    def test_multiple_clients(self):
        (client_1, client_2) = (CLIENT + "_1", CLIENT + "_2")
        self._create_server([BANK_PATH_1, BANK_PATH_2, ])

        # Deal from the first bank to the first client.
        self._setup_bank(BANK_PATH_1, True, False, SCENARIO_1_1)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self.__verify_properties(client_1, True, False, BANK_PATH_1, SCENARIO_1_1)

        # Deal from the second bank to the second client.
        self._setup_bank(BANK_PATH_1, False, False, SCENARIO_1_2)
        self._setup_bank(BANK_PATH_2, True, False, SCENARIO_2_1)
        self.__verify_properties(client_2, True, False, BANK_PATH_2, SCENARIO_2_1)

        # Deal only from the first bank to the first client
        self._setup_bank(BANK_PATH_1, False, False, SCENARIO_1_2)
        self._setup_bank(BANK_PATH_2, False, True, None)
        self.__verify_properties(client_1, False, False, BANK_PATH_1, SCENARIO_1_2)

        # All banks are done - remote server is done.
        self._setup_bank(BANK_PATH_1, False, True, None)
        self._setup_bank(BANK_PATH_2, False, True, None)
        self.__verify_properties(client_1, False, True, None, None)
        self.__verify_properties(client_2, False, True, None, None)

    def _check_serving(self, banks):
        self._create_server(banks)

        self.mock_bank_class.assert_has_calls([call(path) for path in banks])
        assert_items_equal(banks, self.mock_banks.keys())
        assert_items_equal(QUERIES, self.server.funcs.keys())
        self.mock_socket.bind.assert_called_once_with((HOST, PORT))
        self.mock_socket.listen.assert_called_once_with(ANY)

        self.server.server_address = (HOST, PORT)
        thread = Thread(target = self.server.serve_forever)
        with patch("select.select", return_value = ([], [], [])):
            thread.start()

        self.server.shutdown()
        thread.join()

    def __verify_properties(self, client, is_fresh, is_done, bank, scenario):
        # pylint: disable=too-many-arguments
        """Verify server's RPC properties."""
        (output_path, header, feature) = self.FEATURES[bank]

        assert_equal(is_fresh, self.server.funcs["is_fresh"](client))
        assert_equal(is_done, self.server.funcs["is_done"](client))
        assert_equal(output_path, self.server.funcs["get_output_path"](client))
        assert_equal(header, self.server.funcs["get_header"](client))
        assert_equal(feature, self.server.funcs["get_feature"](client))
        assert_equal(scenario, self.server.funcs["get_next_scenario"](client))
