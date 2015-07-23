from os import mkdir, getcwd
from errors import BotError

class Dealer(object):
    def assign(self):
        try:
            with open("features.bank", "rb") as bank_input:
                whole_bank = bank_input.read()
        except IOError:
            raise BotError("No features bank in {:s}".format(getcwd()))

        if not whole_bank:
            print("No more scenarios to deal")

        mkdir("features")
        with open("features/all.feature", "wb") as features:
            features.write(whole_bank)
