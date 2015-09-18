# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import given, when, then
from nose.tools import assert_true, assert_equal, assert_is_none, assert_is_not_none, assert_greater
from bddbot.dealer import Dealer
from bddbot.errors import BotError

@given(r"(?P<count>[1-9][0-9]*) scenario/s were dealt")
def n_scenarios_were_dealt(context, count):
    if not context.dealer:
        context.dealer = Dealer()

    for _ in xrange(int(count)):
        context.dealer.deal()
        context.dealt += 1

@when(r"the bot is loaded")
def load_dealer(context):
    assert_is_none(context.dealer)
    context.dealer = Dealer()

    try:
        context.dealer.load()
    except BotError as error:
        context.error = error

@when(r"the first scenario is dealt")
def first_scenario_is_dealt(context):
    assert_equal(0, context.dealt)

    if not context.dealer:
        context.dealer = Dealer()

    try:
        context.dealer.deal()
    except BotError as error:
        context.error = error

    context.dealt += 1

@when(r"another scenario is dealt")
def another_scenario_is_dealt(context):
    assert_is_not_none(context.dealer)
    assert_greater(context.dealt, 0)

    try:
        context.dealer.deal()
    except BotError as error:
        context.error = error

    context.dealt += 1

@then(r"there are no more scenarios to deal")
def no_more_scenarios(context):
    assert_is_none(context.error)
    assert_is_not_none(context.dealer)
    assert_true(context.dealer.is_done)
