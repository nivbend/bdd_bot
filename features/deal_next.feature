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
        And we dealt 1 scenario/s

    Scenario: Last scenario isn't implemented
        Given the file "calc/calculator.py" contains:
            """
            def calculate(value_1, operator, value_2):
                # This is bound to fail.
                return None
            """
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
