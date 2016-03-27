#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import random

###############################################################################

###############################################################################


def tell_stored(user):
    messages = [
        "{}: sure, I'll try and deliver it.",
        "What am I, a postman, {}? Oh well, alright, I'll pass it on.",
        "{}: sure, I'll tell them when I see them.",
        "{}: yup, sure, it shall be done.",
        "{}: I'm on it, boss."]
    return random.choice(messages).format(user.lstrip('~'))


def no_tells(user):
    messages = [
        '{}: you have no pending tells.']
    return random.choice(messages).format(user.lstrip('~'))


def out_of_range(user):
    messages = [
        '{}: index out of range.']
    return random.choice(messages).format(user.lstrip('~'))


def author_not_found(user):
    messages = [
        '{}: your author is in another castle.',
        '{}: there is nobody here by that name. Now go away.',
        "{}: I'm sorry Dave, I'm afraid I can't do that.",
        "{}: that person has been retconned from existence. Try again later.",
        '{}: No dice.',
        '{}: Author Not Found.',
        '{}: could not find a matching author.',
        '{}: author does not exist.']
    return random.choice(messages).format(user.lstrip('~'))


def page_not_found(user):
    messages = [
        "{}: I couldn't find anything like that. Sorry.",
        '{}: Page Not Found.'
        "{}: The future author of that page haven't wrote it yet. Try later.",
        "{}: You're better off reading something else.",
        "{}: Yesterday, in wiki cache, I saw a page that wasn't there. "
        "It didn't rhyme again today.",
        "{}: Your search query does not match any existing pages.",
        '{}: No such luck.',
        '{}: Maybe another time.']
    return random.choice(messages).format(user.lstrip('~'))


def banlist_updated(user):
    messages = [
        '{}: Banlist updated, boss.']
    return random.choice(messages).format(user.lstrip('~'))


def banlist_update_failed(user):
    messages = [
        "{}: I tried, but it doesn't look like it's working."]
    return random.choice(messages).format(user.lstrip('~'))


def profane_username(user):
    messages = [
        'kicking {user}: they have a filty mouth that could use some soap.',
        "{user} is just untasteful, and I don't want their ilk here.",
        'Was {user} a troll? It was probably a troll.']
    return random.choice(messages).format(user=user.lstrip('~'))


def user_in_banlist(user, banned):
    messages = [
        "{user} was kicked - they're {banned}. See, I can kick ass too!",
        '{user} (better known as {banned}) was exiled from this fine and pure kingdom.',
        '{user} was kicked and banned because they look like {banned} and their face smells.']
    return random.choice(messages).format(user=user, banned=banned)


def user_never_seen(user):
    messages = [
        '{user}: I never saw anyone by that name here.']
    return random.choice(messages).format(user=user.lstrip('~'))
