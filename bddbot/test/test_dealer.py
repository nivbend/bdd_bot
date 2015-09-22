"""Test the Dealer class."""

from subprocess import Popen
from os import mkdir, listdir
from os.path import dirname, basename, join, isdir
from collections import OrderedDict
from nose.tools import assert_true, assert_false, assert_equal, assert_in, assert_raises
from mock import patch, call, create_autospec, ANY
from mock_open import MockOpen
from bddbot.dealer import Dealer, BotError, STATE_PATH
from bddbot.bank import Bank, ParsingError
from bddbot.config import DEFAULT_BANK_DIRECTORY, DEFAULT_TEST_COMMAND

FEATURES_DIRECTORY = "features"
DEFAULT_BANK_PATH = join(DEFAULT_BANK_DIRECTORY, "default.bank")
DEFAULT_FEATURE_PATH = DEFAULT_BANK_PATH.replace("bank", "feature")

(FEATURE_1, SCENARIO_1_1, SCENARIO_1_2) = (
    "Feature: First feature",
    "    Scenario: First feature, first scenario",
    "    Scenario: First feature, second scenario")
(FEATURE_2, SCENARIO_2_1, SCENARIO_2_2) = (
    "Feature: Second feature",
    "    Scenario: Second feature, first scenario",
    "    Scenario: Second feature, second scenario")

class BaseDealerTest(object):
    """A container for utility classes common when testing the Dealer class."""
    # pylint: disable=too-few-public-methods
    def __init__(self):
        self.mocked_open = None
        self.mocked_mkdir = create_autospec(mkdir)
        self.mocked_popen = create_autospec(Popen)

    def _mock_dealer_functions(self, default_bank = None):
        """Mock out standard library functions used by the dealer module."""
        self.mocked_open = MockOpen()
        self._reset_mocks()

        if default_bank:
            self.mocked_open[DEFAULT_BANK_PATH].read_data = default_bank

        patcher = patch.multiple(
            "bddbot.dealer",
            open = self.mocked_open,
            mkdir = self.mocked_mkdir,
            Popen = self.mocked_popen)

        patcher.start()

        return patcher

    def _load_dealer(self, banks = None, test_commands = None):
        """Simulate a call to load() and verify success.

        The `banks` argument is a list of tuples of bank paths and either None (to
        indicate the path represents a file, not a directory), or the return value
        of listdir.
        """
        if not banks:
            banks = [(DEFAULT_BANK_DIRECTORY, [basename(DEFAULT_BANK_PATH), ]), ]
        if not test_commands:
            test_commands = [DEFAULT_TEST_COMMAND.split(), ]

        banks = OrderedDict(banks)

        self.mocked_open[STATE_PATH].side_effect = IOError()
        dealer = Dealer(bank_paths = banks.keys(), tests = test_commands)
        self.mocked_open.assert_any_call(STATE_PATH, "rb")

        # Setup and call load().
        self.mocked_open.side_effect = None
        mocked_isdir = create_autospec(isdir, side_effect = lambda path: banks[path] is not None)
        mocked_listdir = create_autospec(listdir, side_effect = lambda path: banks[path])
        with patch.multiple("bddbot.dealer", isdir = mocked_isdir, listdir = mocked_listdir):
            dealer.load()

        # Verify number of calls to open() (number of features banks plus the state file).
        assert_equal(
            sum(len(paths) if paths else 1 for paths in banks.itervalues()) + 1,
            self.mocked_open.call_count)

        # Verify calls to isdir(), listdir() and open() according to banks' paths.
        for (bank, paths) in banks.iteritems():
            mocked_isdir.assert_any_call(bank)

            if paths is None:
                self.mocked_open.assert_any_call(bank, "r")
            else:
                mocked_listdir.assert_any_call(bank)
                for path in paths:
                    self.mocked_open.assert_any_call(join(bank, path), "r")
                    self.mocked_open[join(bank, path)].read.assert_called_once_with()

        # Verify the rest of the mocks.
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

        # Reset mocks.
        self._reset_mocks()

        return dealer

    def _deal(self, dealer, feature, scenario, path = DEFAULT_FEATURE_PATH):
        """Simulate dealing a scenario and verify success.

        If `feature` is specified, simulate the first time a scenario is dealt from
        the features bank. Otherwise, simulate a consecutive deal from a previous bank.

        Return the commands passed to `Popen()` to verify outside of this function.
        """
        self.mocked_popen.return_value.returncode = 0
        self.mocked_popen.return_value.communicate.return_value = ("", "")

        dealer.deal()

        # If feature is specified, simulate the first deal from the features bank.
        if feature:
            self.mocked_open.assert_called_once_with(path, "w")
            self._assert_writes(["", feature + "\n", scenario, ], path = path)
            self.mocked_mkdir.assert_called_once_with(dirname(path))

        # If feature isn't specified, simulate a consecutive deal.
        # Note that calls to Popen should be verified outside of this function in this case.
        else:
            self.mocked_open.assert_called_once_with(path, "ab")
            self._assert_writes([scenario], path = path)
            self.mocked_mkdir.assert_not_called()

        # We return the commands because we reset the mocks at the end of the function.
        # The stdout/stderr values aren't important, we only care about the commands.
        popen_calls = [command for ((command, ), _) in self.mocked_popen.call_args_list]

        # Reset mocks.
        self._reset_mocks()

        return popen_calls

    def _reset_mocks(self):
        """Reset all mocks."""
        self.mocked_open.reset_mock()
        self.mocked_mkdir.reset_mock()
        self.mocked_popen.reset_mock()

    def _assert_writes(self, chunks, path = DEFAULT_FEATURE_PATH):
        """Verify all calls to write()."""
        assert_equal([call(chunk) for chunk in chunks], self.mocked_open[path].write.mock_calls)

class TestConfiguration(BaseDealerTest):
    """Test tweaking behavior with the configuration file.

    Most use-cases are already covered by the BotConfiguration's unit-tests, these tests
    are designed to make sure the dealer object uses its configuration properly.
    """
    BANK_FILE_PATHS = [
        ("empty-trash.bank",                "empty-trash.feature"),
        ("banks/empty-trash.bank",          "features/empty-trash.feature"),
        ("without-extension",               "without-extension.feature"),
        ("banks/without-extension",         "features/without-extension.feature"),
        ("/path/to/empty-trash.bank",       "/path/to/empty-trash.feature"),
        ("/path/to/banks/empty-trash.bank", "/path/to/features/empty-trash.feature"),
    ]

    def teardown(self):
        # pylint: disable=no-self-use
        patch.stopall()

    def test_setting_bank_file_path(self):
        """Set the path to the bank as a single file."""
        for (bank_path, expected_feature_path) in self.BANK_FILE_PATHS:
            yield self._check_setting_bank_file_path, bank_path, expected_feature_path

    def test_setting_multiple_bank_file_paths(self):
        """Setting multiple bank file paths will read from all of them."""
        bank_path_1 = "/path/to/first.bank"
        bank_path_2 = "/path/to/second.bank"
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, ]))
        self._load_dealer(banks = [(bank_path_1, None), (bank_path_2, None), ])

    def test_setting_bank_directory(self):
        """Supplying a directory path as a bank will iterate over all files under it."""
        bank_directory_path = "/path/to/banks"
        bank_path_1 = join(bank_directory_path, "first.bank")
        bank_path_2 = join(bank_directory_path, "second.bank")

        self._mock_dealer_functions()
        self.mocked_open[STATE_PATH].side_effect = IOError()
        mocked_isdir = create_autospec(isdir)
        mocked_listdir = create_autospec(listdir, return_value = [
            basename(bank_path_1),
            basename(bank_path_2),
            "not_a_bank.txt",
        ])

        dealer = Dealer(bank_paths = [bank_directory_path, ])
        with patch.multiple("bddbot.dealer", isdir = mocked_isdir, listdir = mocked_listdir):
            dealer.load()

        mocked_isdir.assert_called_once_with(bank_directory_path)
        mocked_listdir.assert_called_once_with(bank_directory_path)
        assert_equal(
            [call(STATE_PATH, "rb"), call(bank_path_1, "r"), call(bank_path_2, "r"), ],
            self.mocked_open.call_args_list)
        self.mocked_open[bank_path_1].read.assert_called_once_with()
        self.mocked_open[bank_path_2].read.assert_called_once_with()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_setting_test_command(self):
        """Using custom test commands to verify scenarios."""
        test_command_1 = ["some_test", ]
        test_command_2 = ["another_test", "--awesome", ]

        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))

        dealer = self._load_dealer(test_commands = [test_command_1, test_command_2, ])
        popen_calls = self._deal(dealer, FEATURE_1, SCENARIO_1_1 + "\n")
        assert_equal([], popen_calls)

        self.mocked_popen.return_value.returncode = 0
        popen_calls = self._deal(dealer, None, SCENARIO_1_2)

        assert_equal([test_command_1, test_command_2, ], popen_calls)

    def _check_setting_bank_file_path(self, bank_path, expected_feature_path):
        # pylint: disable=missing-docstring
        self._mock_dealer_functions()
        self.mocked_open[bank_path].read_data = "\n".join([FEATURE_1, SCENARIO_1_1, ])
        dealer = self._load_dealer(banks = [(bank_path, None), ])
        self._deal(dealer, FEATURE_1, SCENARIO_1_1, path = expected_feature_path)

class TestLoading(BaseDealerTest):
    """Test various situations when calling load()."""
    def setup(self):
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, ]))
        self.mocked_open[STATE_PATH].side_effect = IOError()

    def teardown(self):
        patch.stopall()

        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_no_features_bank_file(self):
        """Catch exception when trying to open a non-existent bank file."""
        self.mocked_open[DEFAULT_BANK_PATH].side_effect = IOError()

        dealer = Dealer(bank_paths = [DEFAULT_BANK_PATH, ])
        with assert_raises(BotError) as error_context:
            dealer.load()

        assert_false(dealer.is_done)
        assert_in("couldn't open features bank", error_context.exception.message.lower())
        self.mocked_open.assert_any_call(DEFAULT_BANK_PATH, "r")

    def test_successful_call(self):
        """A successful call to load() should read from the bank file."""
        dealer = Dealer(bank_paths = [DEFAULT_BANK_PATH, ])
        dealer.load()

        assert_false(dealer.is_done)
        self.mocked_open.assert_any_call(DEFAULT_BANK_PATH, "r")

    def test_call_load_twice(self):
        """Calling load() twice only reads the features bank once."""
        dealer = Dealer(bank_paths = [DEFAULT_BANK_PATH, ])
        dealer.load()
        dealer.load()

        assert_false(dealer.is_done)
        self.mocked_open.assert_any_call(DEFAULT_BANK_PATH, "r")

    def test_parsing_error(self):
        """Verify the bank raises a parsing error on an invalid file.

        The dealer is in charge of setting the path attribute on the exception.
        """
        self.mocked_open[DEFAULT_BANK_PATH].read_data = "\n".join([
            FEATURE_1,
            SCENARIO_1_1,
            "@dangling_tag",
        ])

        dealer = Dealer(bank_paths = [DEFAULT_BANK_PATH, ])
        with assert_raises(ParsingError) as error_context:
            dealer.load()

        assert_equal(DEFAULT_BANK_PATH, error_context.exception.filename)
        assert_equal("dangling tags", error_context.exception.message.lower())
        self.mocked_open.assert_any_call(DEFAULT_BANK_PATH, "r")

class TestDealFirst(BaseDealerTest):
    """Test dealing the first scenario."""
    def teardown(self):
        patch.stopall()

        self.mocked_popen.assert_not_called()

    def test_cant_open_features_file_for_writing(self):
        """Capture exceptions in open()."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))
        dealer = self._load_dealer()

        self.mocked_open[DEFAULT_FEATURE_PATH].side_effect = IOError()
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # Couldn't open file for writing, so obviously no writes were perfomed.
        assert_false(dealer.is_done)
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "w")
        self._assert_writes([])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_cant_write_to_feature_file(self):
        """Capture exceptions in write()."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))
        dealer = self._load_dealer()

        self.mocked_open[DEFAULT_FEATURE_PATH].write.side_effect = IOError()
        with assert_raises(BotError) as error_context:
            dealer.deal()

        # First call to write() raised an IOError which was caught and translated.
        assert_false(dealer.is_done)
        assert_in("couldn't write", error_context.exception.message.lower())
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "w")
        self._assert_writes([ANY, ])
        self.mocked_mkdir.assert_called_once_with(FEATURES_DIRECTORY)

    def test_successful_write(self):
        """A successful call to deal() should write the feature and the first scenario."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))
        dealer = self._load_dealer()

        popen_calls = self._deal(dealer, FEATURE_1, SCENARIO_1_1 + "\n")
        assert_equal([], popen_calls)

    def test_empty_features_bank(self):
        """Dealing from an empty feature file should give the 'done' message."""
        self._mock_dealer_functions()
        dealer = self._load_dealer()

        dealer.deal()

        # If directory already exist, we should proceed as usual.
        assert_true(dealer.is_done)
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()

    def test_feature_with_no_scenarios(self):
        """An empty feature is skipped."""
        self._mock_dealer_functions("Feature: an empty feature")
        dealer = self._load_dealer()

        dealer.deal()

        assert_true(dealer.is_done)
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()

    def test_features_directory_already_exists(self):
        """Test deal() works even if the features directory already exist."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))
        dealer = self._load_dealer()

        self.mocked_mkdir.side_effect = OSError()

        # If directory already exist, we should proceed as usual.
        self._deal(dealer, FEATURE_1, SCENARIO_1_1 + "\n")

class TestDealNext(BaseDealerTest):
    """Test logic and actions when calling deal() continously."""
    def teardown(self):
        # pylint: disable=no-self-use
        patch.stopall()

    def test_no_more_scenarios(self):
        """If no more scenarios to deal, mark as done."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, ]))

        dealer = self._load_dealer()
        popen_calls = self._deal(dealer, FEATURE_1, SCENARIO_1_1)
        assert_equal([], popen_calls)

        dealer.deal()

        assert_true(dealer.is_done)
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_called_once_with(
            DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)

    def test_should_not_deal_another(self):
        """If a scenario fails, don't deal another scenario."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))

        dealer = self._load_dealer()
        self._deal(dealer, FEATURE_1, SCENARIO_1_1 + "\n")

        self.mocked_popen.return_value.returncode = -1
        with assert_raises(BotError) as error_context:
            dealer.deal()

        assert_false(dealer.is_done)
        assert_in("can't deal", error_context.exception.message.lower())
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.communicate.assert_called_once_with()

    def test_should_deal_another(self):
        """When all scenarios pass, deal a new scenario."""
        self._mock_dealer_functions("\n".join([FEATURE_1, SCENARIO_1_1, SCENARIO_1_2, ]))
        dealer = self._load_dealer()

        self._deal(dealer, FEATURE_1, SCENARIO_1_1 + "\n")

        self.mocked_popen.return_value.returncode = 0
        dealer.deal()

        assert_true(dealer.is_done)
        self.mocked_open.assert_called_once_with(DEFAULT_FEATURE_PATH, "ab")
        self._assert_writes([SCENARIO_1_2, ])
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.communicate.assert_called_once_with()

    def test_should_not_from_second_bank(self):
        """If the first bank isn't done, do not deal from the second bank."""
        bank_path_1 = join(DEFAULT_BANK_DIRECTORY, "first.bank")
        bank_path_2 = join(DEFAULT_BANK_DIRECTORY, "second.bank")
        feature_path_1 = bank_path_1.replace("bank", "feature")

        self._mock_dealer_functions()
        self.mocked_open[bank_path_1].read_data = "\n".join([FEATURE_1, SCENARIO_1_1, ])
        self.mocked_open[bank_path_2].read_data = "\n".join([FEATURE_2, SCENARIO_2_1, ])

        dealer = self._load_dealer(banks = [
            (DEFAULT_BANK_DIRECTORY, [basename(bank_path_1), basename(bank_path_2), ]),
        ])

        self._deal(dealer, FEATURE_1, SCENARIO_1_1, path = feature_path_1)
        assert_false(dealer.is_done)

        self.mocked_popen.return_value.returncode = -1
        with assert_raises(BotError) as error_context:
            dealer.deal()

        assert_false(dealer.is_done)
        assert_in("can't deal", error_context.exception.message.lower())
        self.mocked_open.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_any_call(DEFAULT_TEST_COMMAND.split(), stdout = ANY, stderr = ANY)
        self.mocked_popen.return_value.communicate.assert_called_once_with()

    def test_should_deal_from_second_bank(self):
        """When the first bank is done, deal from the second if available."""
        bank_path_1 = join(DEFAULT_BANK_DIRECTORY, "first.bank")
        bank_path_2 = join(DEFAULT_BANK_DIRECTORY, "second.bank")
        feature_path_1 = bank_path_1.replace("bank", "feature")
        feature_path_2 = bank_path_2.replace("bank", "feature")

        self._mock_dealer_functions()
        self.mocked_open[bank_path_1].read_data = "\n".join([FEATURE_1, SCENARIO_1_1, ])
        self.mocked_open[bank_path_2].read_data = "\n".join([FEATURE_2, SCENARIO_2_1, ])

        dealer = self._load_dealer(banks = [
            (DEFAULT_BANK_DIRECTORY, [basename(bank_path_1), basename(bank_path_2), ]),
        ])

        self._deal(dealer, FEATURE_1, SCENARIO_1_1, path = feature_path_1)
        assert_false(dealer.is_done)

        self._deal(dealer, FEATURE_2, SCENARIO_2_1, path = feature_path_2)
        assert_true(dealer.is_done)

class TestPersistency(BaseDealerTest):
    """Test storing and loading the bot's state."""
    BANK_PATH_1 = join(DEFAULT_BANK_DIRECTORY, "first.bank")
    BANK_PATH_2 = join(DEFAULT_BANK_DIRECTORY, "second.bank")
    FEATURE_PATH_1 = BANK_PATH_1.replace("bank", "feature")
    FEATURE_PATH_2 = BANK_PATH_2.replace("bank", "feature")

    def setup(self):
        self._mock_dealer_functions()
        self.mocked_open[self.BANK_PATH_1].read_data = "\n".join([FEATURE_1, SCENARIO_1_1, ])
        self.mocked_open[self.BANK_PATH_2].read_data = "\n".join([
            FEATURE_2,
            SCENARIO_2_1,
            SCENARIO_2_2,
            ])

    def teardown(self):
        # pylint: disable=no-self-use
        patch.stopall()

    def test_creation(self):
        """Test creation without a state file and a call to save()."""
        self.mocked_open[STATE_PATH].side_effect = IOError()
        dealer = Dealer()

        self.mocked_open.assert_any_call(STATE_PATH, "rb")
        self.mocked_open[STATE_PATH].read.assert_not_called()
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

        self._reset_mocks()
        with patch("bddbot.dealer.pickle.dump") as mocked_dump:
            dealer.save()

        self.mocked_open.assert_called_once_with(STATE_PATH, "wb")
        mocked_dump.assert_called_once_with({}, ANY)
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

    def test_save(self):
        """Test saving the bot's state."""
        self.mocked_open[STATE_PATH].side_effect = IOError()

        # Verify state after a call to load().
        dealer = self._load_dealer(banks = [
            (DEFAULT_BANK_DIRECTORY, [
                basename(self.BANK_PATH_1),
                basename(self.BANK_PATH_2),
            ]),
        ])

        self._verify_save(dealer, True, False, True, False)

        # Verify state after first call to save().
        self._deal(dealer, FEATURE_1, SCENARIO_1_1, path = self.FEATURE_PATH_1)
        self._verify_save(dealer, False, True, True, False)

        # Verify state after consecutive calls to save().
        self._deal(dealer, FEATURE_2, SCENARIO_2_1 + "\n", path = self.FEATURE_PATH_2)
        self._verify_save(dealer, False, True, False, False)
        self._deal(dealer, None, SCENARIO_2_2, path = self.FEATURE_PATH_2)
        self._verify_save(dealer, False, True, False, True)

    def test_resume(self):
        """Test resuming from a previous state."""
        self._mock_dealer_functions()
        mock_bank = create_autospec(Bank)
        mock_bank.is_done.return_value = False
        mock_bank.is_fresh.return_value = False
        mock_bank.get_next_scenario.return_value = SCENARIO_1_2
        state = OrderedDict([(DEFAULT_FEATURE_PATH, mock_bank), ])
        with patch("bddbot.dealer.pickle.load", return_value = state) as mocked_load:
            dealer = Dealer()

        self.mocked_open.assert_called_once_with(STATE_PATH, "rb")
        mocked_load.assert_called_once_with(ANY)
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

        self._reset_mocks()
        popen_calls = self._deal(dealer, None, SCENARIO_1_2)
        mock_bank.get_next_scenario.assert_called_once_with()
        assert_equal(1, len(popen_calls))

    def _verify_save(self, dealer,
                     is_bank_1_fresh, is_bank_1_done,
                     is_bank_2_fresh, is_bank_2_done):
        # pylint: disable=missing-docstring, too-many-arguments
        with patch("bddbot.dealer.pickle.dump") as mocked_dump:
            dealer.save()

        self.mocked_open.assert_called_once_with(STATE_PATH, "wb")
        mocked_dump.assert_called_once_with(ANY, ANY)
        self.mocked_mkdir.assert_not_called()
        self.mocked_popen.assert_not_called()

        # Verify stored banks' states.
        ((banks, _), _) = mocked_dump.call_args
        (bank_1, bank_2) = (banks[self.FEATURE_PATH_1], banks[self.FEATURE_PATH_2])
        assert_equal(is_bank_1_fresh, bank_1.is_fresh())
        assert_equal(is_bank_1_done, bank_1.is_done())
        assert_equal("", bank_1.header)
        assert_equal(FEATURE_1 + "\n", bank_1.feature)
        assert_equal(is_bank_2_fresh, bank_2.is_fresh())
        assert_equal(is_bank_2_done, bank_2.is_done())
        assert_equal("", bank_2.header)
        assert_equal(FEATURE_2 + "\n", bank_2.feature)

        # Reset mocks.
        self._reset_mocks()
