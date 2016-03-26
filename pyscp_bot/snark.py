#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random

###############################################################################


def tell_stored(user):
    messages = [
        "{}: sure, I'll try and deliver it.",
        "What am I, a postman, {}? Oh well, alright, I'll pass it on.",
        "{}: sure, I'll tell them when I see them.",
        "{}: yup, sure, it shall be done.",
        "{}: I'm on it, boss."]
    return random.choice(messages).format(user)


def no_tells(user):
    return 'You have no pending tells.'