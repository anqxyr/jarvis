#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import googleapiclient.discovery
import locale
import sopel

###############################################################################


def setup(bot):
    bot.memory['google'] = googleapiclient.discovery.build(
        'customsearch', 'v1', developerKey=bot.config.google.apikey).cse()
    bot.memory['youtube'] = googleapiclient.discovery.build(
        'youtube', 'v3', developerKey=bot.config.google.apikey)
    locale.setlocale(locale.LC_ALL, '')


def configure(config):
    config.define_section('scp')


@sopel.module.commands('google', 'g')
def google(bot, tr):
    query = tr.group(2)
    results = bot.memory['google'].list(
        q=query, cx=bot.config.google.cseid, num=1).execute()
    if not results.get('items', None):
        bot.send('Nothing found.')
        return
    title = results['items'][0]['title']
    url = results['items'][0]['formattedUrl']
    snippet = results['items'][0]['snippet']
    bot.send('\x02{}\x02 ({}) - {}'.format(title, url, snippet))


@sopel.module.commands('gis')
def image_search(bot, tr):
    query = tr.group(2)
    results = bot.memory['google'].list(
        q=query, cx=bot.config.google.cseid,
        searchType='image', num=1, safe='high').execute()
    if not results.get('items', None):
        bot.send('Nothing found.')
        return
    url = results['items'][0]['link']
    bot.send(url)


@sopel.module.commands('youtube')
def youtube(bot, tr):
    query = tr.group(2)
    results = bot.memory['youtube'].search().list(
        q=query, maxResults=1, part='id',
        safeSearch='strict', type='video').execute()
    if not results.get('items', None):
        bot.send('Nothing found.')
        return
    video_id = results['items'][0]['id']['videoId']
    description = get_video_description(bot.memory['youtube'], video_id)
    bot.send('{} - http://youtube.com/watch?v={}'.format(
        description, video_id))


@sopel.module.rule(r'.*youtube\.com/watch\?v=([-_a-z0-9]+)')
@sopel.module.rule(r'.*youtu\.be/([-_a-z0-9]+)')
def youtube_lookup(bot, tr):
    video_id = tr.group(1)
    bot.send(get_video_description(bot.memory['youtube'], video_id))


def get_video_description(youtube, video_id):
    video_data = youtube.videos().list(
        part='id,contentDetails,snippet,statistics',
        id=video_id, maxResults=1).execute()
    video_data = video_data['items'][0]
    duration = video_data['contentDetails']['duration'][2:].lower()
    views = video_data['statistics']['viewCount']
    views = locale.format("%d", int(views), grouping=True)
    date = arrow.get(video_data['snippet']['publishedAt']).format('YYYY-MM-DD')
    return (
        '\x02{snippet[title]}\x02 - length \x02{duration}\x02 - '
        '{statistics[likeCount]}↑{statistics[dislikeCount]}↓ - '
        '\x02{views}\x02 views - '
        '\x02{snippet[channelTitle]}\x02 on \x02{date}\x02').format(
        duration=duration, views=views, date=date, **video_data)
