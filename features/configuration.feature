Feature: Configure parameters
    In order to tweak the way the bot works
    As any type of user
    I want to be able to set certain parameters in a configuration file

    Scenario: No configuration file
        Given the file ".bddbotrc" doesn't exist
        And the features bank:
            """
            Feature: Doing great deeds
                Scenario: Helping children in Africa
            """
        When we first deal a scenario
        Then "features/all.feature" contains:
            """
            Feature: Doing great deeds
                Scenario: Helping children in Africa
            """

    Scenario: An empty configuration file
        Given the file ".bddbotrc" contains:
            """
            """
        And the features bank:
            """
            Feature: Doing great deeds
                Scenario: Donating clothes to charity
            """
        When we first deal a scenario
        Then "features/all.feature" contains:
            """
            Feature: Doing great deeds
                Scenario: Donating clothes to charity
            """

    Scenario: Setting a features bank file
        Given the file ".bddbotrc" contains:
            """
            bank: banks/goodness.bank
            """
        And the features bank "banks/goodness.bank":
            """
            Feature: Doing great deeds #2
                Scenario: Helping an old lady cross the street
            """
        When we first deal a scenario
        Then "features/goodness.feature" contains:
            """
            Feature: Doing great deeds #2
                Scenario: Helping an old lady cross the street
            """

    Scenario: Setting multiple features bank files
        Given the file ".bddbotrc" contains:
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
        And we dealt 1 scenario/s
        When we deal another scenario
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
        Given the file ".bddbotrc" contains:
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
        And we dealt 1 scenario/s
        When we deal another scenario
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
        Given the file ".bddbotrc" contains:
            """
            test_command: behave --format=null
            """
        And the features bank:
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
        And the directory "features/steps" exists
        And we dealt 1 scenario/s
        When we deal another scenario
        Then the command "behave --format=null" is executed
        And "features/all.feature" contains:
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """

    Scenario: Setting multiple test commands
        Given the file ".bddbotrc" contains:
            """
            test_command:
                - behave --format=null
                - echo YAY
            """
        And the features bank:
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
        And the directory "features/steps" exists
        And we dealt 1 scenario/s
        When we deal another scenario
        Then the command "behave --format=null" is executed
        And the command "echo YAY" is executed
        And "features/all.feature" contains:
            """
            Feature: Doing great deeds #3
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
