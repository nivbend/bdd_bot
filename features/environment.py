# pylint: disable=missing-docstring

from os import getcwd, chdir
from subprocess import Popen
from mock import patch, create_autospec
from testfixtures import TempDirectory
from behave import register_type
import parse

@parse.with_pattern(r"(?:\w+/)*\w+(?:\.\w+)?")
def parse_path(text):
    return text

@parse.with_pattern(r"[1-9][0-9]*")
def parse_count(text):
    return int(text)

register_type(Path = parse_path, Count = parse_count)

def before_scenario(context, scenario):
    # Setup a temporary directory for the scenario to run in.
    context.original_path = getcwd()
    context.sandbox = TempDirectory()
    chdir(context.sandbox.path)

    # Reset attributes.
    context.dealer = None
    context.dealt = 0
    context.error = None
    context.popen = create_autospec(Popen, side_effect = Popen)

    # Patch Popen.
    scenario.patcher = patch("bddbot.dealer.Popen", context.popen)
    scenario.patcher.start()

def after_scenario(context, scenario):
    # Return to original working directory.
    chdir(context.original_path)

    # Delete temporary sandbox directory.
    context.sandbox.cleanup()
    scenario.patcher.stop()
