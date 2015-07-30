from behave import when, then
from nose.tools import assert_multi_line_equal
from bddbot.errors import BotError

@given("we dealt {count:n} scenario/s")
def we_dealt_n_scenarios(context, count):
    try:
        for i in xrange(count):
            context.dealer.deal()
    except BotError as error:
        context.error = error

@when("we first deal a scenario")
def we_first_deal_a_scenario(context):
    try:
        context.dealer.deal()
    except BotError as error:
        context.error = error

@when("we deal another scenario")
def we_deal_another_scenario(context):
    try:
        context.dealer.deal()
    except BotError as error:
        context.error = error

@then("\"{filename}\" contains")
def file_contains(context, filename):
    with open(filename, "rb") as feature_file:
        features = feature_file.read()
    assert_multi_line_equal(context.text.strip(" \n"), features.strip(" \n"))
