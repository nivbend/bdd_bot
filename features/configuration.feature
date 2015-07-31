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

    Scenario: Setting the test command
        Given the file ".bddbotrc" contains:
            """
            test_command: behave --format=null
            """
        And the features bank:
            """
            Feature: Doing great deeds #2
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
        And the directory "features/steps" exists
        And we dealt 1 scenario/s
        When we deal another scenario
        Then the command "behave --format=null" is executed
        And "features/all.feature" contains:
            """
            Feature: Doing great deeds #2
                Scenario: Feeding the homeless
                Scenario: Helping children in Africa
            """
