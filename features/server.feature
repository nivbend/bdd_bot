Feature: Remote bot server
    Since multiple team members usually work on the same project
    And each team member will likely implement their own features/scenarios
    As a repository's features moderator
    I would like to set up a remote bot server which will deal and synchronize scenarios

    Background: Setup server
        Given the file "banks/first.bank" on the server contains:
            """
            Feature: The first remote feature
                Scenario: The first remote scenario
                Scenario: The second remote scenario
            """

    Scenario: Bind to port
        Given the configuration file on the server:
            """
            [paths]
            bank: banks/first.bank

            [server]
            host: localhost
            port: 3037
            """
        When the dealer is loaded on the server
        And the server is started
        Then port 3037 is open on localhost

    Scenario: Deal the first scenario
        Given the configuration file on the server:
            """
            [paths]
            bank: banks/first.bank

            [server]
            host: localhost
            port: 3037
            """
        When the dealer is loaded on the server
        And the server is started
        Given the configuration file on the client:
            """
            [paths]
            bank: @localhost:3037
            """
        And a directory "features/steps" on the client
        When a scenario is dealt on the client
        Then "features/first.feature" on the client contains:
            """
            Feature: The first remote feature
                Scenario: The first remote scenario
            """
        When a scenario is dealt on the client
        Then "features/first.feature" on the client contains:
            """
            Feature: The first remote feature
                Scenario: The first remote scenario
                Scenario: The second remote scenario
            """

    Scenario: Deal separate features to different clients
        Given the configuration file on the server:
            """
            [paths]
            bank:
                banks/first.bank
                banks/second.bank

            [server]
            host: localhost
            port: 3037
            """
        And the file "banks/second.bank" on the server contains:
            """
            Feature: The second remote feature
                Scenario: The third remote scenario
                Scenario: The fourth remote scenario
            """
        And the configuration file on client #1:
            """
            [paths]
            bank: @localhost:3037
            """
        And the configuration file on client #2:
            """
            [paths]
            bank: @localhost:3037
            """
        When the dealer is loaded on the server
        And the server is started
        And a scenario is dealt on client #1
        Then "features/first.feature" on client #1 contains:
            """
            Feature: The first remote feature
                Scenario: The first remote scenario
            """
        And the "features/second.feature" file wasn't created on client #2
        When a scenario is dealt on client #2
        Then "features/second.feature" on client #2 contains:
            """
            Feature: The second remote feature
                Scenario: The third remote scenario
            """
