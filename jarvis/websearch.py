#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import bs4
import googleapiclient.discovery as googleapi
import requests
import warnings
import wikipedia as wiki

from . import core, parser, lex, tools

###############################################################################


@core.command
@core.alias('g')
@parser.websearch
def google(inp, *, query):
    google = googleapi.build(
        'customsearch',
        'v1',
        developerKey=core.config.google.apikey).cse()
    results = google.list(
        q=query,
        cx=core.config.google.cseid,
        num=1).execute()
    if not results.get('items'):
        return lex.not_found.generic
    return '\x02{title}\x02 ({link}) - {snippet}'.format(
        **results['items'][0])


@core.command
@parser.websearch
def gis(inp, *, query):
    google = googleapi.build(
        'customsearch',
        'v1',
        developerKey=core.config.google.apikey).cse()
    results = google.list(
        q=query,
        cx=core.config.google.cseid,
        searchType='image',
        num=1,
        safe='high').execute()
    if not results.get('items'):
        return lex.not_found.generic
    return results['items'][0]['link']


@core.command
@core.alias('yt')
@parser.websearch
def youtube(inp, *, query):
    youtube = googleapi.build(
        'youtube',
        'v3',
        developerKey=core.config.google.apikey)
    results = youtube.search().list(
        q=query,
        maxResults=1,
        part='id',
        type='video').execute()
    if not results.get('items'):
        return lex.not_found.generic
    vid = results['items'][0]['id']['videoId']
    info = get_youtube_video_info(vid)
    return '{} - http://youtube.com/watch?v={}'.format(info, vid)


@core.rule(r'(?i).*youtube\.com/watch\?v=([-_a-z0-9]+)')
@core.rule(r'(?i).*youtu\.be/([-_a-z0-9]+)')
def youtube_lookup(inp):
    return get_youtube_video_info(inp.text)


def get_youtube_video_info(video_id=None):
    youtube = googleapi.build(
        'youtube',
        'v3',
        developerKey=core.config.google.apikey)
    vdata = youtube.videos().list(
        part='contentDetails,snippet,statistics',
        id=video_id,
        maxResults=1).execute()
    if not vdata.get('items'):
        return lex.not_found.generic
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


@core.command
@core.alias('w')
@parser.websearch
def wikipedia(inp, *, query):
    print(query)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            url = wiki.page(query).url
            summary = wiki.summary(query, sentences=1)
            summary = summary[:360]
            return '{} - {}'.format(summary, url)
    except wiki.exceptions.PageError:
        return lex.not_found.generic
    except wiki.exceptions.DisambiguationError as e:
        print(e.options)
        tools.save_results(
            inp, e.options, lambda x: wikipedia(inp, query=x))
        return tools.choose_input(e.options)


@core.command
@core.alias('define')
@parser.websearch
def dictionary(inp, *, query):
    url = 'http://ninjawords.com/' + query
    soup = bs4.BeautifulSoup(requests.get(url).text, 'lxml')
    word = soup.find(class_='word')
    if not word or not word.dl:
        return lex.not_found.generic
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


@core.command
@parser.websearch
def urbandictionary(inp, *, query):
    url = 'http://api.urbandictionary.com/v0/define?term=' + query
    data = requests.get(url).json()
    if not data['list']:
        return lex.not_found.generic
    result = data['list'][0]
    return '{word}: {definition}'.format(**result)


@core.command
@parser.websearch
def tvtropes(inp, *, query):
    query = query.title().replace(' ', '')
    baseurl = 'http://tvtropes.org/{}/' + query
    url = baseurl.format('Laconic')
    soup = bs4.BeautifulSoup(requests.get(url).text, 'lxml')
    text = soup.find(class_='page-content').find('hr')
    if text is None:
        return lex.tvtropes.not_found
    text = reversed(list(text.previous_siblings))
    text = [i.text if hasattr(i, 'text') else i for i in text]
    text = [str(i).strip() for i in text]
    return '{} {}'.format(' '.join(text), baseurl.format('Main'))
