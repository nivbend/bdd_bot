from behave import when, then
from nose.tools import assert_multi_line_equal
from bddbot.errors import BotError

@when("we first assign a scenario")
def we_first_assign_a_scenario(context):
    try:
        context.dealer.assign()
    except BotError as error:
        context.error = error

@then("\"{filename}\" contains")
def file_contains(context, filename):
    with open(filename, "rb") as feature_file:
        features = feature_file.read()
    assert_multi_line_equal(context.text.strip("\n"), features.strip("\n"))
