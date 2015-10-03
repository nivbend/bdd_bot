Feature: Initialize Bot
    In order to start serving features on a repository
    As a repository's features moderator
    I want to initialize the bot's state on a given repository

    Scenario: No features bank file
        When the dealer is loaded
        Then there are no more scenarios to deal
        And the "features" directory wasn't created

    Scenario: No features in bank
        Given the features bank "banks/default.bank":
            """
            """
        When the dealer is loaded
        And the first scenario is dealt
        Then there are no more scenarios to deal
