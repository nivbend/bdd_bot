from behave import when
from bddbot.errors import BotError

@when("we first assign a scenario")
def we_first_assign_a_scenario(context):
    try:
        context.dealer.assign()
    except BotError as error:
        context.error = error
