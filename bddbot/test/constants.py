"""Constant definitions for testing purposes."""

from bddbot.config import TEST_COMMAND

BANK_PATH_1 = "banks/first.bank"
BANK_PATH_2 = "banks/second.bank"
FEATURE_PATH_1 = BANK_PATH_1.replace("bank", "feature")
FEATURE_PATH_2 = BANK_PATH_2.replace("bank", "feature")
(HOST, PORT) = ("bank_server", 0xBDD)
CLIENT = "client"

DEFAULT_TEST_COMMANDS = [TEST_COMMAND, ]
