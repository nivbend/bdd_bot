Feature: Configure parameters
    In order to tweak the way the bot works
    As any type of user
    I want to be able to set certain parameters in a configuration file

    Scenario: No configuration file
        Given the file "bddbot.cfg" doesn't exist
        And the features bank "banks/default.bank":
            """
            Feature: Doing great deeds
                Scenario: Helping children in Africa
            """
        When the first scenario is dealt
        Then "features/default.feature" contains:
            """
            Feature: Doing great deeds
                Scenario: Helping children in Africa
            """

    Scenario: An empty configuration file
        Given the configuration file:
            """
            """
        And the features bank "banks/default.bank":
            """
            Feature: Doing great deeds
                Scenario: Donating clothes to charity
            """
        When the first scenario is dealt
        Then "features/default.feature" contains:
            """
            Feature: Doing great deeds
                Scenario: Donating clothes to charity
            """

    Scenario: Setting a features bank file
        Given the configuration file:
            """
            [paths]
            bank: banks/goodness.bank
            """
        And the features bank "banks/goodness.bank":
            """
            Feature: Doing great deeds #2
                Scenario: Helping an old lady cross the street
            """
        When the first scenario is dealt
        Then "features/goodness.feature" contains:
            """
            Feature: Doing great deeds #2
                Scenario: Helping an old lady cross the street
            """

    Scenario: Setting multiple features bank files
        Given the configuration file:
            """
            [paths]
            bank:
                banks/goodness_1.bank
                banks/goodness_2.bank
            """
        And a directory "features/steps"
        And the features bank "banks/goodness_1.bank":
            """
            Feature: Volunteering
                Scenario: Helping in a soup kitchen
            """
        And the features bank "banks/goodness_2.bank":
            """
            Feature: Donations
                Scenario: Giving money to the poor
                Scenario: Organizing a neighberhood fund-raiser
            """
        And 1 scenario/s were dealt
        When another scenario is dealt
        Then "features/goodness_1.feature" contains:
            """
            Feature: Volunteering
                Scenario: Helping in a soup kitchen
            """
        Then "features/goodness_2.feature" contains:
            """
            Feature: Donations
                Scenario: Giving money to the poor
            """

    Scenario: Searching a directory for feature banks
        # Supplying a directory as a bank path will search all files under it
        # for '*.bank' files and will load them.
        Given the configuration file:
            """
            [paths]
            bank: my_banks

            [test]
            run: behave my_features
            """
        And a directory "my_features/steps"
        And the features bank "my_banks/first.bank":
            """
            Feature: The first feature
                Scenario: The first scenario
            """
        And the features bank "my_banks/second.bank":
            """
            Feature: The second feature
                Scenario: The second scenario
            """
        And 1 scenario/s were dealt
        When another scenario is dealt
        Then "my_features/first.feature" contains:
            """
            Feature: The first feature
                Scenario: The first scenario
            """
        Then "my_features/second.feature" contains:
            """
            Feature: The second feature
                Scenario: The second scenario
            """

    Scenario: Setting the test command
        Given the configuration file:
            """
            [test]
            run: behave --format=null
            """
        And the features bank "banks/default.bank":
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
        And a directory "features/steps"
        And 1 scenario/s were dealt
        When another scenario is dealt
        Then the command "behave --format=null" is executed
        And "features/default.feature" contains:
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """

    Scenario: Setting multiple test commands
        # Supplying more than one test command will run them consecutively.
        Given the configuration file:
            """
            [test]
            run:
                behave --format=null
                echo YAY
            """
        And the features bank "banks/default.bank":
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
        And a directory "features/steps"
        And 1 scenario/s were dealt
        When another scenario is dealt
        Then the command "behave --format=null" is executed
        And the command "echo YAY" is executed
        And "features/default.feature" contains:
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
