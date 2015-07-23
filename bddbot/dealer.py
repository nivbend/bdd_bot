from os.path import isfile
from os import mkdir, getcwd
from errors import BotError

class Dealer(object):
    def assign(self):
        if not isfile("features.bank"):
            raise BotError("No features bank in {:s}".format(getcwd()))

        with open("features.bank", "rb") as bank_input:
            whole_bank = bank_input.read()

        if not whole_bank:
            print("No more scenarios to deal")

        mkdir("features")
        with open("features/all.feature", "wb") as features:
            features.write(whole_bank)
