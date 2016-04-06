#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import json
import random
import pathlib

###############################################################################

with open(str(pathlib.Path(__file__).parent / 'lexicon.json')) as file:
    lexicon = json.load(file)

###############################################################################
# Not Found Messages
###############################################################################


def not_found():
    messages = lexicon['not_found']
    return random.choice(messages)


def author_not_found():
    messages = lexicon['author_not_found'] + lexicon['not_found']
    return random.choice(messages)


def page_not_found():
    messages = lexicon['page_not_found'] + lexicon['not_found']
    return random.choice(messages)

###############################################################################


def unclear_input(options):
    if len(options) <= 5:
        head, tail = options[:-1], options[-1]
        messages = lexicon['options_few']
    else:
        head, tail = options[:5], len(options[5:])
        messages = lexicon['options_many']
    return random.choice(messages).format(head=', '.join(head), tail=tail)


def missing_arguments():
    messages = lexicon['missing_arguments'] + lexicon['reject']
    return random.choice(messages)


def bad_index():
    messages = lexicon['bad_index'] + lexicon['reject']
    return random.choice(messages)


def too_many_dice():
    messages = lexicon['too_many_dice'] + lexicon['reject']
    return random.choice(messages)


def bad_die():
    messages = lexicon['bad_die'] + lexicon['reject']
    return random.choice(messages)

###############################################################################


def tell_stored():
    messages = [
        "I will deliver it.",
        "What am I, a postman? Oh well, alright, I'll pass it on.",
        "I'll tell them when I see them.", ]
    messages += lexicon['accept']
    return random.choice(messages)


def no_tells():
    messages = [
        "You have no pending tells.", ]
    return random.choice(messages)


def banlist_updated():
    messages = [
        "Banlist updated, boss.", ]
    return random.choice(messages)


def banlist_update_failed():
    messages = [
        "Your banlist is broken, mate. You should into fixing it.", ]
    return random.choice(messages)


def profane_username(user):
    messages = [
        "Kicking {user}: they have a filty mouth that could use some soap.",
        "{user} is just untasteful, and I don't want their ilk here.",
        "Was {user} a troll? It was probably a troll.", ]
    return random.choice(messages).format(user=user.lstrip('~'))


def user_in_banlist(user, banned):
    messages = [
        "{user} was kicked - they're {banned}. See, I can kick ass too!",
        "{user} (better known as {banned}) was exiled from this fine and pure kingdom.",
        "{user} was kicked and banned because they look like {banned} and their face smells."]
    return random.choice(messages).format(user=user, banned=banned)


def user_never_seen():
    messages = [
        "I never saw anyone by that name here."]
    messages += lexicon['reject']
    return random.choice(messages)
