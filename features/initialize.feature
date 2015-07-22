Feature: Initialize Bot
    In order to start serving features on a repository
    As a repository's features moderator
    I want to initialize the bot's state on a given repository.

    Scenario: No features bank file
        Given the features bank file doesn't exist
        When we first assign a scenario
        Then an error saying "no features bank" is raised
        And the "features" directory isn't created
