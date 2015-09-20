# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import then
from nose.tools import assert_is_not_none, assert_in

@then(r"an error saying \"(?P<message>.+)\" is raised")
def an_error_is_raised(context, message):
    assert_is_not_none(context.error, "Expected an error saying {:s}".format(message))
    assert_in(message.lower(), context.error.message.lower())
