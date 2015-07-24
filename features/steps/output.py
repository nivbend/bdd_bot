from behave import then
from nose.tools import assert_is_not_none, assert_is_none, assert_in

@then("an error saying \"{message}\" is raised")
def an_error_is_raised(context, message):
    assert_is_not_none(context.error, "Expected an error saying {}".format(message))
    assert_in(message.lower(), context.error.message.lower())

@then("there are no more scenarios to deal")
def no_more_features(context):
    assert_is_none(context.error)
    assert_in("no more scenarios to deal", context.stdout_capture.getvalue().lower())