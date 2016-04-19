#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import bs4
import googleapiclient.discovery as googleapi
import requests
import warnings
import wikipedia

from . import lexicon, tools

###############################################################################


def google_search(apikey, cseid, inp):
    if not inp:
        return lexicon.input.missing
    google = googleapi.build('customsearch', 'v1', developerKey=apikey).cse()
    results = google.list(q=inp, cx=cseid, num=1).execute()
    if not results.get('items'):
        return lexicon.not_found.generic
    return '\x02{title}\x02 ({link}) - {snippet}'.format(
        **results['items'][0])


def google_image_search(apikey, cseid, inp):
    if not inp:
        return lexicon.input.missing
    google = googleapi.build('customsearch', 'v1', developerKey=apikey).cse()
    results = google.list(
        q=inp, cx=cseid, searchType='image', num=1, safe='high').execute()
    if not results.get('items'):
        return lexicon.not_found.generic
    return results['items'][0]['link']


def youtube_search(apikey, inp):
    if not inp:
        return lexicon.input.missing
    youtube = googleapi.build('youtube', 'v3', developerKey=apikey)
    results = youtube.search().list(
        q=inp, maxResults=1, part='id', type='video').execute()
    if not results.get('items'):
        return lexicon.not_found.generic
    vid = results['items'][0]['id']['videoId']
    info = youtube_video_info(apikey, vid)
    return '{} - http://youtube.com/watch?v={}'.format(info, vid)


def youtube_video_info(apikey, video_id):
    youtube = googleapi.build('youtube', 'v3', developerKey=apikey)
    vdata = youtube.videos().list(
        part='contentDetails,snippet,statistics',
        id=video_id, maxResults=1).execute()
    if not vdata.get('items'):
        return lexicon.not_found.generic
    vdata = vdata['items'][0]

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


def wikipedia_search(inp, key='global'):
    if not inp:
        return lexicon.input.missing
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            url = wikipedia.page(inp).url
            summary = wikipedia.summary(inp, sentences=1)
            return '{} - {}'.format(summary, url)
    except wikipedia.exceptions.PageError:
        return lexicon.not_found.generic
    except wikipedia.exceptions.DisambiguationError as e:
        tools.remember(e.options, key, lambda x: wikipedia_search(x, key))
        return tools.choose_input(e.options)


def dictionary_search(inp, key):
    if not inp:
        return lexicon.input.missing
    url = 'http://ninjawords.com/' + inp
    soup = bs4.BeautifulSoup(requests.get(url).text, 'lxml')
    word = soup.find(class_='word')
    if not word or not word.dl:
        return lexicon.not_found.generic
    output = ['\x02{}\x02 - '.format(word.dt.text)]
    for line in word.dl('dd'):
        if 'article' in line['class']:
            output.append('\x02{}\x02:'.format(line.text))
            idx = 1
        elif 'entry' in line['class']:
            text = line.find(class_='definition').text.strip().lstrip('°')
            output.append('{}. {}'.format(idx, text))
            idx += 1
        elif 'synonyms' in line['class']:
            strings = [i for i in line.stripped_strings if i != ','][1:]
            output.append('\x02Synonyms\x02: ' + ', '.join(strings) + '.')
    return ' '.join(output)


def urbandictionary_search(inp, key):
    if not inp:
        return lexicon.input.missing
    url = 'http://api.urbandictionary.com/v0/define?term=' + inp.strip()
    data = requests.get(url).json()
    if not data['list']:
        return lexicon.not_found.generic
    result = data['list'][0]
    return '{word}: {definition}'.format(**result)
