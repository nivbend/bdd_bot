# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import then
from nose.tools import assert_in
from mock import call, ANY

@then("the command \"{command}\" is executed")
def command_is_executed(context, command):
    assert_in(
        call(str(command).split(), stdout = ANY, stderr = ANY),
        context.popen.mock_calls)
