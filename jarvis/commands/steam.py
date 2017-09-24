#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import requests

from jarvis import core, parser, lex

###############################################################################
# Globals
###############################################################################

CACHE = {}


###############################################################################
# Parser
###############################################################################

@parser.parser
def prsteam(pr):
    pr.add_argument(
        'title',
        nargs='+',
        action='join',
        type=str.lower,
        help="""Title of the game to search for.""")


###############################################################################
# Command
###############################################################################


def get_game(steam_id, include_url=True):
    data = requests.get(
        'https://store.steampowered.com/api/appdetails',
        params={'appids': steam_id}).json()[str(steam_id)]
    if 'data' not in data:
        return lex.steam.not_found
    data = data['data']
    name = data['name']
    description = data['short_description']
    if 'price_overview' in data:
        price = int(data['price_overview']['final']) / 100
    else:
        price = None
    genres = [i['description'] for i in data.get('genres', [])]
    return lex.steam.result(
        name=name, description=description, price=price,
        genres=genres, url=steam_id if include_url else None)


@core.rule(r'https?://store.steampowered.com/app/([0-9]+)')
def lookup(inp):
    return get_game(inp.text, include_url=False)


@core.command
@prsteam
def steam(inp, title):
    """Find steam games by their title."""
    global CACHE

    if not CACHE:
        data = requests.get(
            'http://api.steampowered.com/ISteamApps/GetAppList/v0001/').json()
        data = data['applist']['apps']['app']
        data = {i['name'].lower(): i['appid'] for i in data}
        CACHE.update(data)

    if title in CACHE:
        return get_game(CACHE[title])

    for k, v in CACHE.items():
        if title in k:
            return get_game(v)

    return lex.steam.not_found
