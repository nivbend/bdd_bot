# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from socket import socket, AF_INET, SOCK_STREAM
from errno import ECONNREFUSED
from nose.tools import assert_not_equal
from behave import then

@then("port {port:d} is open on {host}")
def port_n_is_open(context, port, host):
    # pylint: disable=unused-argument
    test_socket = socket(AF_INET, SOCK_STREAM)

    assert_not_equal(
        ECONNREFUSED,
        test_socket.connect_ex((host, port)),
        "Port {:d} is not open".format(port))
