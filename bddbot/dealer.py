from os import mkdir, getcwd
from bank import split_bank
from errors import BotError

class Dealer(object):
    def __init__(self):
        self.__feature = ""
        self.__scenarios = []

    def assign(self):
        try:
            with open("features.bank", "rb") as bank_input:
                (header, self.__feature, self.__scenarios) = split_bank(bank_input.read())
        except IOError:
            raise BotError("No features bank in {:s}".format(getcwd()))

        if not self.__feature:
            print("No more scenarios to deal")

        mkdir("features")
        with open("features/all.feature", "wb") as features:
            features.write(header)
            features.write(self.__feature)
            if self.__scenarios:
                features.write(self.__scenarios[0])
