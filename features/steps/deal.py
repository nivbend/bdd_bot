# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import given, when, then
from nose.tools import assert_equal, assert_is_not_none, assert_greater, assert_multi_line_equal
from bddbot.dealer import Dealer
from bddbot.errors import BotError

@given("we dealt (?P<count>[1-9][0-9]*) scenario/s")
def we_dealt_n_scenarios(context, count):
    if not context.dealer:
        context.dealer = Dealer()

    for _ in xrange(int(count)):
        context.dealer.deal()
        context.dealt += 1

@when("we first deal a scenario")
def we_first_deal_a_scenario(context):
    assert_equal(0, context.dealt)

    if not context.dealer:
        context.dealer = Dealer()

    try:
        context.dealer.deal()
        context.dealt += 1
    except BotError as error:
        context.error = error

@when("we deal another scenario")
def we_deal_another_scenario(context):
    assert_is_not_none(context.dealer)
    assert_greater(context.dealt, 0)

    try:
        context.dealer.deal()
        context.dealt += 1
    except BotError as error:
        context.error = error

@then("\"(?P<filename>.+)\" contains")
def file_contains(context, filename):
    features = context.sandbox.read(filename)
    assert_multi_line_equal(context.text.strip(" \n"), features.strip(" \n"))
