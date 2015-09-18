Feature: Configure parameters
    In order to tweak the way the bot works
    As any type of user
    I want to be able to set certain parameters in a configuration file

    Scenario: No configuration file
        Given the file "bddbot.yml" doesn't exist
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
        Given the file "bddbot.yml" contains:
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
        Given the file "bddbot.yml" contains:
            """
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
        Given the file "bddbot.yml" contains:
            """
            bank:
                - banks/goodness-1.bank
                - banks/goodness-2.bank
            """
        And the features bank "banks/goodness-1.bank":
            """
            Feature: Volunteering
                Scenario: Helping in a soup kitchen
            """
        And the features bank "banks/goodness-2.bank":
            """
            Feature: Donations
                Scenario: Giving money to the poor
                Scenario: Organizing a neighberhood fund-raiser
            """
        And 1 scenario/s were dealt
        When another scenario is dealt
        Then "features/goodness-1.feature" contains:
            """
            Feature: Volunteering
                Scenario: Helping in a soup kitchen
            """
        Then "features/goodness-2.feature" contains:
            """
            Feature: Donations
                Scenario: Giving money to the poor
            """

    Scenario: Searching a directory for feature banks
        Given the file "bddbot.yml" contains:
            """
            bank: my-banks
            """
        And the features bank "my-banks/first.bank":
            """
            Feature: The first feature
                Scenario: The first scenario
            """
        And the features bank "my-banks/second.bank":
            """
            Feature: The second feature
                Scenario: The second scenario
            """
        And 1 scenario/s were dealt
        When another scenario is dealt
        Then "my-features/first.feature" contains:
            """
            Feature: The first feature
                Scenario: The first scenario
            """
        Then "my-features/second.feature" contains:
            """
            Feature: The second feature
                Scenario: The second scenario
            """

    Scenario: Setting the test command
        Given the file "bddbot.yml" contains:
            """
            test_command: behave --format=null
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
        Given the file "bddbot.yml" contains:
            """
            test_command:
                - behave --format=null
                - echo YAY
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
