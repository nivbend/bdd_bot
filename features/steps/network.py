# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from socket import socket, gethostname, AF_INET, SOCK_STREAM
from errno import ECONNREFUSED
from nose.tools import assert_not_equal
from behave import then

@then("port {port:d} is open")
def port_n_is_open(context, port):
    # pylint: disable=unused-argument
    test_socket = socket(AF_INET, SOCK_STREAM)

    assert_not_equal(
        ECONNREFUSED,
        test_socket.connect_ex((gethostname(), port)),
        "Port {:d} is not open".format(port))
