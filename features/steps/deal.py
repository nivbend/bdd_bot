# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from os import getcwd, chdir
from threading import Thread
from behave import given, when, then
from nose.tools import assert_true, assert_equal, assert_is_none, assert_is_not_none
from nose.tools import assert_in, assert_not_in, assert_greater
from bddbot.dealer import Dealer, STATE_PATH
from bddbot.server import BankServer
from bddbot.config import BotConfiguration
from bddbot.errors import BotError

@given("{count:Count} scenario/s were dealt")
def n_scenarios_were_dealt(context, count):
    if not context.dealer:
        config = BotConfiguration()
        context.dealer = Dealer(config.banks, config.tests)

    for _ in xrange(count):
        context.dealer.deal()
        context.dealt += 1

@when("the dealer is loaded")
def load_dealer(context):
    assert_is_none(context.dealer)

    config = BotConfiguration()
    context.dealer = Dealer(config.banks, config.tests)

    try:
        context.dealer.load()
    except BotError as error:
        context.error = error

@when("the dealer is loaded on {side:Side}")
def load_dealer_on_side(context, side):
    assert_not_in(side, context.bot_config)
    assert_not_in(side, context.dealer)

    # Change to side's sandbox.
    original_directory = getcwd()
    chdir(context.sandbox[side].path)

    config = BotConfiguration()
    dealer = Dealer(config.banks, config.tests, name = side)

    context.bot_config[side] = config
    context.dealer[side] = dealer

    try:
        context.dealer[side].load()
    except BotError as error:
        context.error = error

    # Return to original working directory.
    chdir(original_directory)

@when("the server is started")
def server_is_started(context):
    assert_is_none(context.server)
    assert_is_none(context.server_thread)
    assert_in("server", context.bot_config)
    assert_is_not_none(context.bot_config["server"].port)

    # Change to side's sandbox.
    original_directory = getcwd()
    chdir(context.sandbox["server"].path)

    context.server = BankServer(
        context.bot_config["server"].port,
        context.bot_config["server"].banks)
    context.server_thread = Thread(target = context.server.serve_forever)
    context.server_thread.start()

    # Return to original working directory.
    chdir(original_directory)

@when("the bot is restarted")
def restart_the_bot(context):
    assert_is_not_none(context.dealer)

    config = BotConfiguration()
    context.dealer = Dealer(config.banks, config.tests)

@when("the bot's state is saved")
def save_state(context):
    context.dealer.save()
    assert_in(STATE_PATH, context.sandbox.actual())

@when("the first scenario is dealt")
def first_scenario_is_dealt(context):
    assert_equal(0, context.dealt)

    if not context.dealer:
        config = BotConfiguration()
        context.dealer = Dealer(config.banks, config.tests)

    try:
        context.dealer.deal()
    except BotError as error:
        context.error = error

    context.dealt += 1

@when("a scenario is dealt on {side:Side}")
def scenario_is_dealt_on_side(context, side):
    if side not in context.dealer:
        load_dealer_on_side(context, side)

    original_directory = getcwd()
    chdir(context.sandbox[side].path)

    try:
        context.dealer[side].deal()
    except BotError as error:
        context.error = error

    # Return to original working directory.
    chdir(original_directory)

@when("another scenario is dealt")
def another_scenario_is_dealt(context):
    assert_is_not_none(context.dealer)
    assert_greater(context.dealt, 0)

    try:
        context.dealer.deal()
    except BotError as error:
        context.error = error

    context.dealt += 1

@then("there are no more scenarios to deal")
def no_more_scenarios(context):
    assert_is_none(context.error)
    assert_is_not_none(context.dealer)
    assert_true(context.dealer.is_done)
