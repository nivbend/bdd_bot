# pylint: disable=missing-docstring, no-name-in-module, invalid-name

from behave import given, then
from os.path import isdir, isfile
from nose.tools import assert_true, assert_false, assert_multi_line_equal
from bddbot.config import DEFAULT_CONFIG_FILENAME

@given("the file \"{filename:Path}\" doesn't exist")
def file_does_not_exist(context, filename):
    # pylint: disable=unused-argument
    assert_false(isfile(filename))

@given("the file \"{filename:Path}\" contains")
def the_file_contains(context, filename):
    assert_false(isfile(filename), "'{:s}' already exist".format(filename))
    context.sandbox.write(filename, context.text)

@given("the features bank \"{filename:Path}\"")
def the_features_bank_contains(context, filename):
    assert_true(filename.endswith(".bank"))
    the_file_contains(context, filename)

@given("the configuration file")
def the_configuration_file_contains(context):
    the_file_contains(context, DEFAULT_CONFIG_FILENAME)

@given("a directory \"{directory:Path}\"")
def directory_exist(context, directory):
    context.sandbox.makedir(directory)

@then("the \"{filename:Path}\" file wasn't created")
def file_was_not_created(context, filename):
    # pylint: disable=unused-argument
    assert_false(isfile(filename), "'{:s}' shouldn't exist".format(filename))

@then("the \"{directory:Path}\" directory wasn't created")
def directory_was_not_created(context, directory):
    # pylint: disable=unused-argument
    assert_false(isdir(directory), "'{:s}' shouldn't exist".format(directory))

@then("\"{filename:Path}\" contains")
def file_contains(context, filename):
    features = context.sandbox.read(filename)
    assert_multi_line_equal(context.text.strip(" \n"), features.strip(" \n"))
