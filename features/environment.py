from tempfile import mkdtemp
from os import chdir, devnull
from shutil import rmtree
from subprocess import check_call
from bddbot import Dealer

def before_scenario(context, scenario):
    # Setup a temporary directory for the scenario to run in.
    context.temp_dir = mkdtemp()
    chdir(context.temp_dir)

    # Reset attributes.
    context.dealer = Dealer()
    context.error = None

def after_scenario(context, scenario):
    # Delete temporary sandbox directory.
    rmtree(context.temp_dir)
