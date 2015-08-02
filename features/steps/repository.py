# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import given, when, then
from os import makedirs
from os.path import isdir, isfile, dirname
from nose.tools import assert_true, assert_false, assert_is_none
from bddbot.dealer import Dealer, FEATURE_BANK_FILENAME
from bddbot.errors import BotError

@given("the file \"{filename}\" doesn't exist")
def a_repository_without_a_features_bank(context, filename):
    # pylint: disable=unused-argument
    assert not isfile(filename)

@given("the features bank")
def a_features_bank(context):
    the_file_contains(context, FEATURE_BANK_FILENAME)

@given("the file \"{filename}\" contains")
def the_file_contains(context, filename):
    assert_false(isfile(filename), "'{:s}' already exist".format(filename))

    try:
        makedirs(dirname(filename))
    except OSError:
        # Directory already exist.
        pass

    with open(filename, "wb") as output:
        output.write(context.text)

@given("the directory \"{directory}\" exists")
def directory_exists(context, directory):
    # pylint: disable=unused-argument
    makedirs(directory)

@when("we initialize the bot's state")
def load_state(context):
    assert_is_none(context.dealer)
    context.dealer = Dealer()

    try:
        context.dealer.load()
    except BotError as error:
        context.error = error

@then("the \"{filename}\" file is created")
def file_is_created(context, filename):
    # pylint: disable=unused-argument
    assert_true(isfile(filename), "'{0:s}' wasn't created".format(filename))

@then("the \"{directory}\" directory isn't created")
def directory_is_not_created(context, directory):
    # pylint: disable=unused-argument
    assert_false(isdir(directory), "'{0:s}' exist".format(directory))
