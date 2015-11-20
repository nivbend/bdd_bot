"""A server wrapper around dealer operations."""

from SimpleXMLRPCServer import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler
import logging
from .bank import Bank

QUERIES = {
    "is_done": (lambda bank: bank.is_done(), True),
    "get_output_path": (lambda bank: bank.output_path, None),
    "get_header": (lambda bank: bank.header, ""),
    "get_feature": (lambda bank: bank.feature, ""),
}

class BankServer(SimpleXMLRPCServer, object):
    """RPC command server."""
    allow_reuse_address = True

    def __init__(self, host, port, banks):
        super(BankServer, self).__init__(
            (host, port),
            SimpleXMLRPCRequestHandler,
            logRequests = False)
        self.__banks = [Bank(path) for path in banks]
        self.__assigned = {}
        self.__log = logging.getLogger(__name__)

        self.register_function(self.is_fresh, "is_fresh")
        self.register_function(self.get_next_scenario, "get_next_scenario")
        for (name, (callback, default)) in QUERIES.iteritems():
            self.register_function(self.__query_bank(callback, default), name)

    def serve_forever(self, poll_interval = 0.5):
        """Start serving."""
        (address, port) = self.server_address
        self.__log.info("Server started on %s:%d", address, port)

        super(BankServer, self).serve_forever(poll_interval)

    def shutdown(self):
        """Stop serving."""
        self.__log.info("Stopped serving")
        super(BankServer, self).shutdown()

    def is_fresh(self, client):
        """Returns whether the current bank is fresh.

        This functions always returns True as long as the client was not assigned a bank.
        """
        if client not in self.__assigned:
            return True

        else:
            query = self.__query_bank(lambda bank: bank.is_fresh(), False)
            return query(client)

    def get_next_scenario(self, client):
        """Returns the next scenario to deal to the client.

        This functions also assigns the bank to the client.
        """
        bank = self.__get_current_bank(client)
        if not bank:
            self.__log.debug("No more scenarios for '%s'", client)
            return None

        if client not in self.__assigned:
            self.__log.info("Assigning '%s' to '%s'", bank.feature.splitlines()[0], client)
            self.__assigned[client] = bank

        scenario = bank.get_next_scenario()
        self.__log.info("Sent '%s' to '%s'", scenario.lstrip(), client)

        return scenario

    def __query_bank(self, get_value, default):
        """Returns a callback to query the current bank's property."""
        def query(client):
            # pylint: disable=missing-docstring
            bank = self.__get_current_bank(client)
            if not bank:
                return default

            return get_value(bank)
        return query

    def __get_current_bank(self, client):
        """Returns the first bank that isn't done yet, None otherwise."""
        # If client was already assigned a bank, check it.
        if client in self.__assigned:
            bank = self.__assigned[client]

            # If bank isn't done, deal from it.
            if not bank.is_done():
                return bank

            # Bank is done. Unassign it and look for the next one.
            self.__log.info("Unassigning '%s' from '%s'", bank.feature.splitlines()[0], client)
            self.__assigned.pop(client)

        for bank in self.__banks:
            # Skip finished banks.
            if bank.is_done():
                continue

            # Skip banks which were already assigned.
            if bank in self.__assigned.itervalues():
                continue

            # Found a bank.
            return bank

        # No bank was found.
        return None
