Feature: Initialize Bot
    In order to start serving features on a repository
    As a repository's features moderator
    I want to initialize the bot's state on a given repository.

    Scenario: No features bank file
        Given the features bank file doesn't exist
        When we first assign a scenario
        Then an error saying "no features bank" is raised
        And the "features" directory isn't created

    Scenario: No features in bank
        Given the features bank file is empty
        When we first assign a scenario
        Then there are no more scenarios to deal

    Scenario: One feature, no scenarios
        Given the features bank:
            """
            Feature: A feature with no scenarios
            """
        When we first assign a scenario
        Then the "features/all.feature" file is created
        And "features/all.feature" contains:
            """
            Feature: A feature with no scenarios
            """

    Scenario: One feature, one scenario
        Given the features bank:
            """
            Feature: A single feature to test with
                Scenario: First scenario
                    Given some preconditions
                    When something happens
                    Then stuff will go down
            """
        When we first assign a scenario
        Then "features/all.feature" contains:
            """
            Feature: A single feature to test with
                Scenario: First scenario
                    Given some preconditions
                    When something happens
                    Then stuff will go down
            """
