from os.path import join
from os import mkdir, getcwd
from bank import split_bank
from errors import BotError

FEATURE_BANK_FILENAME = "features.bank"
FEATURES_DIRECTORY = "features"
OUTPUT_FEATURES_FILENAME = join(FEATURES_DIRECTORY, "all.feature")

class Dealer(object):
    def __init__(self):
        self.__header = ""
        self.__feature = ""
        self.__scenarios = []

    def load(self):
        if self.__feature:
            return

        try:
            with open(FEATURE_BANK_FILENAME, "rb") as bank_input:
                (self.__header, self.__feature, self.__scenarios) = split_bank(bank_input.read())
        except IOError:
            raise BotError("No features bank in {:s}".format(getcwd()))

    def deal(self):
        self.load()

        if not self.__feature:
            print("No more scenarios to deal")

        try:
            mkdir(FEATURES_DIRECTORY)
        except OSError:
            # Directory exists.
            pass

        try:
            with open(OUTPUT_FEATURES_FILENAME, "wb") as features:
                features.write(self.__header)
                features.write(self.__feature)
                if self.__scenarios:
                    features.write(self.__scenarios[0])
        except IOError:
            raise BotError("Couldn't write to '{}'".format(OUTPUT_FEATURES_FILENAME))
