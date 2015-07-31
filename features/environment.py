# pylint: disable=missing-docstring

from tempfile import mkdtemp
from os import chdir
from shutil import rmtree
from subprocess import Popen
from mock import patch, create_autospec

def before_scenario(context, scenario):
    # Setup a temporary directory for the scenario to run in.
    context.temp_dir = mkdtemp()
    chdir(context.temp_dir)

    # Reset attributes.
    context.dealer = None
    context.dealt = 0
    context.error = None
    context.popen = create_autospec(Popen, side_effect = Popen)

    # Patch Popen.
    scenario.patcher = patch("bddbot.dealer.Popen", context.popen)
    scenario.patcher.start()

def after_scenario(context, scenario):
    # Delete temporary sandbox directory.
    rmtree(context.temp_dir)
    scenario.patcher.stop()
