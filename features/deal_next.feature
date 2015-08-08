Feature: Deal another scenario
    In order to continue developement
    As a developer
    I want to be dealt a new scenario when all previous scenarios were implemented

    Background: One scenario was already dealt
        Given the features bank:
            """
            Feature: Basic calculator operations
                Scenario: Adding
                    Given a value of 1 was entered
                    And the '+' button was pressed
                    And a value of 1 was entered
                    When we calculate the outcome
                    Then the result is 2

                Scenario: Subtracting
                    Given a value of 5 was entered
                    And the '-' button was pressed
                    And a value of 2 was entered
                    When we calculate the outcome
                    Then the result is 3

                Scenario: Multiplying
                    Given a value of 3 was entered
                    And the '*' button was pressed
                    And a value of 7 was entered
                    When we calculate the outcome
                    Then the result is 21

                Scenario: Dividing
                    Given a value of 45 was entered
                    And the '/' button was pressed
                    And a value of 9 was entered
                    When we calculate the outcome
                    Then the result is 5
            """
        And the file "features/steps/calculator.py" contains:
            """
            from behave import given, when, then
            from calc import calculate

            @given("a value of {value:n} was entered")
            def value_was_entered(context, value):
                try:
                    context.args.append(value)
                except AttributeError:
                    context.args = [value, ]

            @given("the '{operator}' button was pressed")
            def operator_was_pressed(context, operator):
                context.operator = operator

            @when("we calculate the outcome")
            def we_calculate_the_outcome(context):
                (arg_1, arg_2) = context.args
                context.result = calculate(arg_1, context.operator, arg_2)

            @then("the result is {result:n}")
            def the_result_is(context, result):
                assert result == context.result
            """
        And the file "calc/__init__.py" contains:
            """
            from calculator import calculate
            """

    Scenario: Last scenario isn't implemented
        Given the file "calc/calculator.py" contains:
            """
            def calculate(value_1, operator, value_2):
                # This is bound to fail.
                return None
            """
        And we dealt 1 scenario/s
        When we deal another scenario
        Then "features/all.feature" contains:
            """
            Feature: Basic calculator operations
                Scenario: Adding
                    Given a value of 1 was entered
                    And the '+' button was pressed
                    And a value of 1 was entered
                    When we calculate the outcome
                    Then the result is 2
            """

    Scenario: Last scenario implemented properly
        Given the file "calc/calculator.py" contains:
            """
            def calculate(value_1, operator, value_2):
                # This isn't a full solution yet but hey, baby, that's TDD.
                return value_1 + value_2
            """
        And we dealt 1 scenario/s
        When we deal another scenario
        Then "features/all.feature" contains:
            """
            Feature: Basic calculator operations
                Scenario: Adding
                    Given a value of 1 was entered
                    And the '+' button was pressed
                    And a value of 1 was entered
                    When we calculate the outcome
                    Then the result is 2

                Scenario: Subtracting
                    Given a value of 5 was entered
                    And the '-' button was pressed
                    And a value of 2 was entered
                    When we calculate the outcome
                    Then the result is 3
            """

    Scenario: Deal more than two scenarios
        Given the file "calc/calculator.py" contains:
            """
            OPERATIONS = {
                "+": lambda a,b: a + b,
                "-": lambda a,b: a - b,
                "*": lambda a,b: a * b,
            }

            def calculate(value_1, operator, value_2):
                return OPERATIONS[operator](value_1, value_2)
            """
        And we dealt 3 scenario/s
        When we deal another scenario
        Then "features/all.feature" contains:
            """
            Feature: Basic calculator operations
                Scenario: Adding
                    Given a value of 1 was entered
                    And the '+' button was pressed
                    And a value of 1 was entered
                    When we calculate the outcome
                    Then the result is 2

                Scenario: Subtracting
                    Given a value of 5 was entered
                    And the '-' button was pressed
                    And a value of 2 was entered
                    When we calculate the outcome
                    Then the result is 3

                Scenario: Multiplying
                    Given a value of 3 was entered
                    And the '*' button was pressed
                    And a value of 7 was entered
                    When we calculate the outcome
                    Then the result is 21

                Scenario: Dividing
                    Given a value of 45 was entered
                    And the '/' button was pressed
                    And a value of 9 was entered
                    When we calculate the outcome
                    Then the result is 5
            """

    Scenario: Deal all scenarios
        Given the file "calc/calculator.py" contains:
            """
            OPERATIONS = {
                "+": lambda a,b: a + b,
                "-": lambda a,b: a - b,
                "*": lambda a,b: a * b,
                "/": lambda a,b: a / b,
            }

            def calculate(value_1, operator, value_2):
                return OPERATIONS[operator](value_1, value_2)
            """
        And we dealt 4 scenario/s
        When we deal another scenario
        Then "features/all.feature" contains:
            """
            Feature: Basic calculator operations
                Scenario: Adding
                    Given a value of 1 was entered
                    And the '+' button was pressed
                    And a value of 1 was entered
                    When we calculate the outcome
                    Then the result is 2

                Scenario: Subtracting
                    Given a value of 5 was entered
                    And the '-' button was pressed
                    And a value of 2 was entered
                    When we calculate the outcome
                    Then the result is 3

                Scenario: Multiplying
                    Given a value of 3 was entered
                    And the '*' button was pressed
                    And a value of 7 was entered
                    When we calculate the outcome
                    Then the result is 21

                Scenario: Dividing
                    Given a value of 45 was entered
                    And the '/' button was pressed
                    And a value of 9 was entered
                    When we calculate the outcome
                    Then the result is 5
            """
        And there are no more scenarios to deal

    Scenario: Deal from two feature files
        Given the file "calc/calculator.py" contains:
            """
            OPERATIONS = {
                "+": lambda a,b: a + b,
                "-": lambda a,b: a - b,
                "*": lambda a,b: a * b,
                "/": lambda a,b: a / b,
            }

            def calculate(value_1, operator, value_2):
                return OPERATIONS[operator](value_1, value_2)
            """
        And the file "banks/edge_cases.bank" contains:
            """
            Feature: Edge cases
                Scenario: Dividing by zero
                    Given a value of 18 was entered
                    And the '/' button was pressed
                    And a value of 0 was entered
                    When we calculate the outcome
                    Then the result is None
            """
        And the file ".bddbotrc" contains:
            """
            bank:
                - banks/all.bank
                - banks/edge_cases.bank
            """
        And we dealt 4 scenario/s
        When we deal another scenario
        Then "features/all.feature" contains:
            """
            Feature: Basic calculator operations
                Scenario: Adding
                    Given a value of 1 was entered
                    And the '+' button was pressed
                    And a value of 1 was entered
                    When we calculate the outcome
                    Then the result is 2

                Scenario: Subtracting
                    Given a value of 5 was entered
                    And the '-' button was pressed
                    And a value of 2 was entered
                    When we calculate the outcome
                    Then the result is 3

                Scenario: Multiplying
                    Given a value of 3 was entered
                    And the '*' button was pressed
                    And a value of 7 was entered
                    When we calculate the outcome
                    Then the result is 21

                Scenario: Dividing
                    Given a value of 45 was entered
                    And the '/' button was pressed
                    And a value of 9 was entered
                    When we calculate the outcome
                    Then the result is 5
            """
        And "features/edge_cases.feature" contains:
            """
            Feature: Edge cases
                Scenario: Dividing by zero
                    Given a value of 18 was entered
                    And the '/' button was pressed
                    And a value of 0 was entered
                    When we calculate the outcome
                    Then the result is None
            """
