from os.path import join
from os import mkdir, getcwd
from subprocess import Popen, PIPE
from bank import split_bank
from errors import BotError

FEATURE_BANK_FILENAME = "features.bank"
FEATURES_DIRECTORY = "features"
OUTPUT_FEATURES_FILENAME = join(FEATURES_DIRECTORY, "all.feature")

class Dealer(object):
    def __init__(self):
        self.__is_loaded = False
        self.__header = ""
        self.__feature = ""
        self.__scenarios = []

    def load(self):
        if self.__is_loaded:
            return

        try:
            with open(FEATURE_BANK_FILENAME, "rb") as bank_input:
                (self.__header, self.__feature, scenarios) = split_bank(bank_input.read())
        except IOError:
            raise BotError("No features bank in {:s}".format(getcwd()))

        self.__scenarios = [(False, scenario) for scenario in scenarios]
        self.__is_loaded = True

    def deal(self):
        deal_flags = (was_dealt for (was_dealt, _) in self.__scenarios)

        if not any(deal_flags):
            self._deal_first()
        elif not all(deal_flags):
            if self._are_tests_passing():
                self._deal_another()
            else:
                print "Can't deal while there are unimplemented scenarios"
        else:
            self._done()

    def _are_tests_passing(self):
        process = Popen("behave", stdout = PIPE, stderr = PIPE)
        process.wait()

        return (0 == process.returncode)

    def _deal_first(self):
        self.load()

        if not self.__feature:
            self._done()
            return

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
                    (was_dealt, scenario) = self.__scenarios[0]
                    features.write(scenario)
                    self.__scenarios[0] = (True, scenario)
                else:
                    self._done()
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(OUTPUT_FEATURES_FILENAME))

    def _deal_another(self):
        try:
            with open(OUTPUT_FEATURES_FILENAME, "ab") as features:
                for i in xrange(len(self.__scenarios)):
                    (was_dealt, scenario) = self.__scenarios[i]
                    if not was_dealt:
                        features.write(scenario)
                        self.__scenarios[i] = (True, scenario)
                        break
        except IOError:
            raise BotError("Couldn't write to '{:s}'".format(OUTPUT_FEATURES_FILENAME))

    def _done(self):
        print("No more scenarios to deal")
