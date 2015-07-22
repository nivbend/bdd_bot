from os.path import isfile
from os import getcwd
from errors import BotError

class Dealer(object):
    def assign(self):
        if not isfile("features.bank"):
            raise BotError("No features bank in {:s}".format(getcwd()))
