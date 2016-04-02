#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random

###############################################################################

ACCEPT = [
    "I'm on it, boss.",
    "I will do it.",
    "Sure, that's exactly what I'll do, meatbag.",
    "I shall follow your orders, товарищ.",
    "Consider it done.", ]

REJECT = [
    "I'm sorry Dave, I'm afraid I can't do that.",
    "No dice.",
    "No such luck.",
    "Are you sure this is what you want me to do?",
    "Maybe another time.",
    "How about you do it yourself if you want it that much.", ]

NODATA = [
    "I have nothing for you.",
    "There is nothing here. Null. Void. Nada.", ]

COMPLETED = [
    "Mission accomplished.", ]

FAILED = [
    "I tried, but it doesn't look like it's working.",
    "Something has gone terribly wrong.", ]

###############################################################################


def tell_stored():
    messages = [
        "I will deliver it.",
        "What am I, a postman? Oh well, alright, I'll pass it on.",
        "I'll tell them when I see them.", ]
    messages += ACCEPT
    return random.choice(messages)


def no_tells():
    messages = [
        "You have no pending tells.", ]
    return random.choice(messages)


def out_of_range():
    messages = [
        "That index is sooo big. It will never fit.", ]
    messages += REJECT
    return random.choice(messages)


def author_not_found():
    messages = [
        "Your author is in another castle.",
        "There is nobody here by that name. Now go away.",
        "That person has been retconned from existence.",
        "E72 - Author Not Found. That's a made-up error. I made it up.", ]
    messages += NODATA
    return random.choice(messages)


def page_not_found():
    messages = [
        "E74 - Page Not Found. That's a real error. It's in the book. Look it up.",
        "The future author of that page haven't wrote it yet.",
        "You're better off reading something else.",
        "Yesterday, upon the wiki, I saw a page that wasn't there. It didn't rhyme again today.",
        "Your search query does not match any existing pages.", ]
    messages += NODATA
    return random.choice(messages)


def banlist_updated():
    messages = [
        "Banlist updated, boss.", ]
    messages += COMPLETED
    return random.choice(messages)


def banlist_update_failed():
    messages = [
        "Your banlist is broken, mate. You should into fixing it.", ]
    messages += FAILED
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
    messages += REJECT
    return random.choice(messages)


def die_count_too_high():
    messages = [
        "That's a hella a lot of dice, mister."]
    messages += REJECT
    return random.choice(messages)
