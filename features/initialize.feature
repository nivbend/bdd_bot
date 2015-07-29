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
        Given the features bank:
            """
            """
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

    Scenario: One feature, three scenarios
        Given the features bank:
            """
            Feature: A single feature to test with
                Scenario: First scenario
                    Given some preconditions
                    When something happens
                    Then stuff will go down

                Scenario: Second scenario
                    Given some more preconditions
                    When another thing happens
                    Then more stuff will go down

                Scenario: Third scenario
                    Given some quaky preconditions
                    And more preconditions
                    When all the chips have fallen
                    Then will the fat lasy sing
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

    Scenario: A Feature with background
        Given the features bank:
            """
            Feature: A single feature to test with

                Background: Some requirements on each scenario
                    Given some stuff that need to happen
                    And some more things

                Scenario: First scenario
                    Given some preconditions
                    When something happens
                    Then stuff will go down

                Scenario: Second scenario
                    Given some more preconditions
                    When another thing happens
                    Then more stuff will go down

                Scenario: Third scenario
                    Given some quaky preconditions
                    And more preconditions
                    When all the chips have fallen
                    Then will the fat lasy sing
            """
        When we first assign a scenario
        Then "features/all.feature" contains:
            """
            Feature: A single feature to test with

                Background: Some requirements on each scenario
                    Given some stuff that need to happen
                    And some more things

                Scenario: First scenario
                    Given some preconditions
                    When something happens
                    Then stuff will go down
            """
