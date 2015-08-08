Feature: Initialize Bot
    In order to start serving features on a repository
    As a repository's features moderator
    I want to deal the first scenario in a feature file

    Scenario: One feature, no scenarios
        Given the features bank:
            """
            Feature: A feature with no scenarios
            """
        When we first deal a scenario
        Then the "features/all.feature" file isn't created

    Scenario: One feature, one scenario
        Given the features bank:
            """
            Feature: A single feature to test with
                Scenario: First scenario
                    Given some preconditions
                    When something happens
                    Then stuff will go down
            """
        When we first deal a scenario
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
        When we first deal a scenario
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
        When we first deal a scenario
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

    Scenario: Scenarios with multiline texts
        Given the features bank:
            """
            Feature: A challenging feature
                Scenario: The troublesome scenario
                    Given some text
                        \"\"\"
                        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
                        sed do eiusmod tempor incididunt ut labore et dolore magna
                        aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                        ullamco laboris nisi ut aliquip ex ea commodo consequat.
                        Duis aute irure dolor in reprehenderit in voluptate velit
                        esse cillum dolore eu fugiat nulla pariatur.
                        \"\"\"
                    When we print it in Arial
                    Then graphic designers start twitching
            """
        When we first deal a scenario
        Then "features/all.feature" contains:
            """
            Feature: A challenging feature
                Scenario: The troublesome scenario
                    Given some text
                        \"\"\"
                        Lorem ipsum dolor sit amet, consectetur adipiscing elit,
                        sed do eiusmod tempor incididunt ut labore et dolore magna
                        aliqua. Ut enim ad minim veniam, quis nostrud exercitation
                        ullamco laboris nisi ut aliquip ex ea commodo consequat.
                        Duis aute irure dolor in reprehenderit in voluptate velit
                        esse cillum dolore eu fugiat nulla pariatur.
                        \"\"\"
                    When we print it in Arial
                    Then graphic designers start twitching
            """

    Scenario: Steps with data tables
        Given the features bank:
            """
            Feature: Unable to even
                Scenario: The MOST AWEFUL thing happened
                    Given a group of girls
                        | Name    | Role in gang      |
                        | Jane    | Tag-a-long        |
                        | Merry   | Wannabe           |
                        | Christy | Drama queen       |
                        | Sasha   | Like, who is she? |
                    When you wouldn't BELIEVE what they did
                    Then I can't even!
            """
        When we first deal a scenario
        Then "features/all.feature" contains:
            """
            Feature: Unable to even
                Scenario: The MOST AWEFUL thing happened
                    Given a group of girls
                        | Name    | Role in gang      |
                        | Jane    | Tag-a-long        |
                        | Merry   | Wannabe           |
                        | Christy | Drama queen       |
                        | Sasha   | Like, who is she? |
                    When you wouldn't BELIEVE what they did
                    Then I can't even!
            """

    Scenario: A feature with tags
        Given the features bank:
            """
            @bad @dont_implement_this_guys
            Feature: Being a party-pooper
                Scenario: People in the office are having fun
                    Given people are telling jokes instead of working
                    When we enter the room
                    Then we'll "casually" mention there are pubs for that kind of thing
                    And we'll stick around and glare until everyone are back to work
            """
        When we first deal a scenario
        Then "features/all.feature" contains:
            """
            @bad @dont_implement_this_guys
            Feature: Being a party-pooper
                Scenario: People in the office are having fun
                    Given people are telling jokes instead of working
                    When we enter the room
                    Then we'll "casually" mention there are pubs for that kind of thing
                    And we'll stick around and glare until everyone are back to work
            """
