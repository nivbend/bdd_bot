# pylint: disable=missing-docstring

from tempfile import mkdtemp
from os import chdir
from shutil import rmtree
from bddbot import Dealer

def before_scenario(context, scenario):
    # pylint: disable=unused-argument
    # Setup a temporary directory for the scenario to run in.
    context.temp_dir = mkdtemp()
    chdir(context.temp_dir)

    # Reset attributes.
    context.dealer = Dealer()
    context.dealt = 0
    context.error = None

def after_scenario(context, scenario):
    # pylint: disable=unused-argument
    # Delete temporary sandbox directory.
    rmtree(context.temp_dir)
