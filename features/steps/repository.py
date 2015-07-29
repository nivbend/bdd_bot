from behave import given, then
from os.path import isdir, isfile
from nose.tools import assert_true

@given("the features bank file doesn't exist")
def a_repository_without_a_features_bank(context):
    assert not isfile("features.bank")

@given("the features bank")
def a_features_bank(context):
    with open("features.bank", "wb") as bank:
        bank.write(context.text)

@then("the \"{filename}\" file is created")
def file_is_created(context, filename):
    assert_true(isfile(filename), "'{0:s}' wasn't created".format(filename))

@then("the \"{directory}\" directory isn't created")
def directory_is_not_created(context, directory):
    assert not isdir(directory)
