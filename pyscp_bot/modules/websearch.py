#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import sopel
import pyscp_bot as jarvis

###############################################################################


@sopel.module.commands('google', 'g')
def google_search(bot, tr):
    g = bot.config.google
    bot.send(jarvis.search.google_search(g.apikey, g.cseid, tr.group(2)))


@sopel.module.commands('gis')
def google_image_search(bot, tr):
    g = bot.config.google
    bot.send(jarvis.search.google_image_search(g.apikey, g.cseid, tr.group(2)))


@sopel.module.commands('youtube')
def youtube_search(bot, tr):
    g = bot.config.google
    bot.send(jarvis.search.youtube_search(g.apikey, tr.group(2)))


@sopel.module.rule(r'.*youtube\.com/watch\?v=([-_a-z0-9]+)')
@sopel.module.rule(r'.*youtu\.be/([-_a-z0-9]+)')
def youtube_lookup(bot, tr):
    g = bot.config.google
    bot.send(jarvis.search.youtube_video_info(g.apikey, tr.group(1)))


@sopel.module.commands('wikipedia')
def wikipedia_search(bot, tr):
    bot.send(jarvis.search.wikipedia_search(tr.group(2)))


@sopel.module.commands('definition', 'define', 'dictionary')
def dictionary_search(bot, tr):
    bot.send(jarvis.search.dictionary_search(tr.group(2))
