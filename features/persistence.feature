Feature: Persistent State
    In order to work on a project for a period of time
    As a developer
    I want the bot to keep track of dealt scenarios between individual runs

    Background: The steps directory exists (mandatory for running `behave`)
        Given a directory "features/steps"
        And the features bank "banks/movie.bank":
            """
            Feature: Watching a movie
                Scenario: At home
                Scenario: Going to the cinema
            """
        And the features bank "banks/book.bank":
            """
            Feature: Reading a book
                Scenario: In bed
            """
        And the file "bddbot.yml" contains:
            """
            bank:
                - banks/movie.bank
                - banks/book.bank
            """

    Scenario: Deal another scenario after a restart
        Given 1 scenario/s were dealt
        When the bot's state is saved
        And the bot is restarted
        And another scenario is dealt
        Then "features/movie.feature" contains:
            """
            Feature: Watching a movie
                Scenario: At home
                Scenario: Going to the cinema
            """
        And the "features/book.feature" file wasn't created

    Scenario: Deal another feature after a restart
        Given 2 scenario/s were dealt
        When the bot's state is saved
        And the bot is restarted
        And another scenario is dealt
        Then "features/movie.feature" contains:
            """
            Feature: Watching a movie
                Scenario: At home
                Scenario: Going to the cinema
            """
        And "features/book.feature" contains:
            """
            Feature: Reading a book
                Scenario: In bed
            """