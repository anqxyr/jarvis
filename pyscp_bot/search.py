#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import googleapiclient.discovery as googleapi
import wikipedia
import warnings

from . import lexicon

###############################################################################


def google_search(apikey, cseid, inp):
    google = googleapi.build('customsearch', 'v1', developerKey=apikey).cse()
    results = google.list(q=inp, cx=cseid, num=1).execute()
    if not results.get('items'):
        return lexicon.no_results_found()
    return '\x02{title}\x02 ({formattedUrl}) - {snippet}'.format(
        **results['items'][0])


def google_image_search(apikey, cseid, inp):
    google = googleapi.build('customsearch', 'v1', developerKey=apikey).cse()
    results = google.list(
        q=inp, cx=cseid, searchType='image', num=1, safe='high').execute()
    if not results.get('items'):
        return lexicon.no_results_found()
    return results['items'][0]['link']


def youtube_search(apikey, inp):
    youtube = googleapi.build('youtube', 'v3', developerKey=apikey)
    results = youtube.search().list(
        q=inp, maxResults=1, part='id', type='video').execute()
    if not results.get('items'):
        return lexicon.no_results_found()
    vid = results['items'][0]['id']['videoId']
    info = youtube_video_info(apikey, vid)
    return '{} - http://youtube.com/watch?v={}'.format(info, vid)


def youtube_video_info(apikey, video_id):
    youtube = googleapi.build('youtube', 'v3', developerKey=apikey)
    vdata = youtube.videos().list(
        part='contentDetails,snippet,statistics',
        id=video_id, maxResults=1).execute()['items'][0]

    template = ' '.join("""
    \x02{snippet[title]}\x02 - length \x02{duration}\x02 -
    {likes} {views} \x02{snippet[channelTitle]}\x02 on
    \x02{snippet[publishedAt]:.10}\x02""".split())

    duration = vdata['contentDetails']['duration'][2:].lower()
    likes, views = '', ''
    if 'likeCount' in vdata['statistics']:
        likes = '{likeCount}↑{dislikeCount}↓ -'.format(**vdata['statistics'])
    if 'viewCount' in vdata['statistics']:
        views = '\x02{:,}\x02 views -'.format(
            int(vdata['statistics']['viewCount']))

    return template.format(
        duration=duration, likes=likes, views=views, **vdata)


###############################################################################


def wikipedia_search(inp):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            url = wikipedia.page(inp).url
            summary = wikipedia.summary(inp, sentences=1)
            return '{} - \x02{}\x02'.format(summary, url)
    except wikipedia.exceptions.PageError:
        return lexicon.no_results_found()
    except wikipedia.exceptions.DisambiguationError as e:
        return lexicon.multiple_results(e.options[:5])
