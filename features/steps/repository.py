# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import given, when, then
from os.path import isdir, isfile
from nose.tools import assert_true, assert_false, assert_is_none
from bddbot.dealer import Dealer
from bddbot.errors import BotError

@given("the file \"(?P<filename>.+)\" doesn't exist")
def a_repository_without_a_features_bank(context, filename):
    # pylint: disable=unused-argument
    assert not isfile(filename)

@given("the features bank \"(?P<filename>.+)\"")
def a_features_bank(context, filename):
    assert_true(filename.endswith(".bank"))
    write_to_file(context, filename)

@given("the file \"(?P<filename>.+)\" contains")
def write_to_file(context, filename):
    assert_false(isfile(filename), "'{:s}' already exist".format(filename))
    context.sandbox.write(filename, context.text)

@given("the directory \"(?P<directory>.+)\" exists")
def create_directory(context, directory):
    context.sandbox.makedir(directory)

@when("we initialize the bot's state")
def load_state(context):
    assert_is_none(context.dealer)
    context.dealer = Dealer()

    try:
        context.dealer.load()
    except BotError as error:
        context.error = error

@then("the \"(?P<filename>.+)\" file isn't created")
def file_is_created(context, filename):
    # pylint: disable=unused-argument
    assert_false(isfile(filename), "'{:s}' exist".format(filename))

@then("the \"(?P<directory>.+)\" directory isn't created")
def directory_is_not_created(context, directory):
    # pylint: disable=unused-argument
    assert_false(isdir(directory), "'{:s}' exist".format(directory))
