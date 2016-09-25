#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import bs4
import googleapiclient.discovery
import requests
import wikipedia as wiki

from . import core, parser, lex, tools

###############################################################################


def googleapi(api, version, method, _container='items', **kwargs):
    engine = googleapiclient.discovery.build(
        api, version, developerKey=core.config.google.apikey)
    if method:
        engine = getattr(engine, method)()
    return engine.list(**kwargs).execute().get(_container)


@core.command
@core.alias('g')
@parser.websearch
def google(inp, *, query):
    results = googleapi(
        'customsearch', 'v1', 'cse',
        q=query, cx=core.config.google.cseid, num=1)

    if not results:
        return lex.google.not_found

    res = results[0]
    return lex.google.result(
        title=res['title'], url=res['link'], text=res['snippet'])


@core.command
@parser.websearch
def gis(inp, *, query):
    results = googleapi(
        'customsearch', 'v1', 'cse',
        q=query, cx=core.config.google.cseid, searchType='image',
        num=1, safe='high')

    if not results:
        return lex.gis.not_found

    return lex.gis.result(url=results[0]['link'])


@core.command
@core.alias('yt')
@parser.websearch
def youtube(inp, *, query):
    results = googleapi(
        'youtube', 'v3', 'search',
        q=query, maxResults=1, part='id', type='video')

    if not results:
        return lex.youtube.not_found

    video_id = results[0]['id']['videoId']
    return lex.youtube.result(video_id=video_id, **_youtube_info(video_id))


@core.rule(r'(?i).*youtube\.com/watch\?v=([-_a-z0-9]+)')
@core.rule(r'(?i).*youtu\.be/([-_a-z0-9]+)')
def youtube_lookup(inp):
    return lex.youtube.result(**_youtube_info(inp.text))


def _youtube_info(video_id):
    results = googleapi(
        'youtube', 'v3', 'videos',
        part='contentDetails,snippet,statistics', id=video_id, maxResults=1)

    if not results:
        return lex.youtube.not_found

    res = results[0]
    return dict(
        title=res['snippet']['title'],
        duration=res['contentDetails']['duration'][2:].lower(),
        likes=res['statistics'].get('likeCount'),
        dislikes=res['statistics'].get('dislikeCount'),
        views=res['statistics']['viewCount'],
        channel=res['snippet']['channelTitle'],
        date=res['snippet']['publishedAt'][:10])


###############################################################################


@core.command
@parser.translate
def translate(inp, *, lang, query):
    """Powered by Yandex.Translate (http://translate.yandex.com/)."""
    response = requests.get(
        'https://translate.yandex.net/api/v1.5/tr.json/translate',
        params=dict(key=core.config.yandex, lang=lang, text=query))
    if response.status_code != 200:
        reason = response.json()['message']
        return lex.translate.error(reason=reason)
    return lex.translate.result(**response.json())

###############################################################################


@core.command
@core.alias('w')
@parser.websearch
def wikipedia(inp, *, query):
    try:
        page = wiki.page(query)
    except wiki.exceptions.PageError:
        return lex.wikipedia.not_found
    except wiki.exceptions.DisambiguationError as e:
        tools.save_results(inp, e.options, lambda x: wikipedia(inp, query=x))
        return lex.options(options=e.options)

    return lex.wikipedia.result(
        title=page.title, url=page.url, text=page.content)


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
