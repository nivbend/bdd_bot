from behave import given, then
from os.path import isdir, isfile

@given("the features bank file doesn't exist")
def a_repository_without_a_features_bank(context):
    assert not isfile("features.bank")

@then("the \"{directory}\" directory isn't created")
def directory_is_not_created(context, directory):
    assert not isdir(directory)
