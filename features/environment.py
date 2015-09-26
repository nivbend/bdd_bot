# pylint: disable=missing-docstring

from os import getcwd, chdir
from subprocess import Popen
from mock import patch, create_autospec
from testfixtures import TempDirectory
from behave import use_step_matcher

use_step_matcher("re")

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
