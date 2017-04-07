#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow
import bs4
import googleapiclient.discovery
import googleapiclient.errors
import requests
import wikipedia as wiki
import functools

from . import core, parser, lex, tools, utils

###############################################################################


def indexed_cache(func):

    func = functools.lru_cache()(func)

    @functools.wraps(func)
    @utils.catch(IndexError, return_value=lex.input.bad_index)
    def inner(inp, *, index, **kwargs):
        results = func(**kwargs)
        if isinstance(results, list):
            tools.save_results(inp, range(len(results)), results.__getitem__)
            return results[index - 1 if index else 0]
        else:
            return results

    return inner


###############################################################################


def googleapi(api, version, method, _container='items', **kwargs):
    engine = googleapiclient.discovery.build(
        api, version, developerKey=core.config.google.apikey)
    if method:
        engine = getattr(engine, method)()
    try:
        return engine.list(**kwargs).execute().get(_container)
    except googleapiclient.errors.HttpError as e:
        if e.resp.status in (500, 503):
            return lex.google.heavy_load
        elif e.resp.status == 403:
            return lex.google.quota_exceeded
        else:
            raise e


@core.command
@core.alias('g')
@parser.google
@indexed_cache
def google(query):
    """Ask the wise and all-knowing Google."""
    results = googleapi(
        'customsearch', 'v1', 'cse',
        q=query, cx=core.config.google.cseid, num=10)

    if not results:
        return lex.google.not_found

    return [
        lex.google.result(
            index=idx + 1,
            total=len(results),
            title=r['title'],
            url=r['link'],
            text=r['snippet'])
        for idx, r in enumerate(results)]


@core.command
@parser.google
@indexed_cache
def gis(query):
    """Search for images."""
    results = googleapi(
        'customsearch', 'v1', 'cse',
        q=query, cx=core.config.google.cseid, searchType='image',
        num=10, safe='high')

    if not results:
        return lex.gis.not_found

    return [
        lex.gis.result(
            index=idx + 1,
            total=len(results),
            title=r['title'],
            url=r['link'])
        for idx, r in enumerate(results)]


@core.command
@core.alias('yt')
@parser.youtube
@indexed_cache
def youtube(query):
    """Search youtube for stuff."""
    results = googleapi(
        'youtube', 'v3', 'search',
        q=query, maxResults=10, part='id', type='video')

    if not results:
        return lex.youtube.not_found

    video_ids = [r['id']['videoId'] for r in results]
    return [
        lex.youtube.result(
            index=idx + 1,
            total=len(results),
            video_id=vid,
            **info)
        for idx, (vid, info) in
        enumerate(zip(video_ids, _youtube_info(*video_ids)))]


@core.rule(r'(?i).*youtube\.com/watch\?v=([-_a-z0-9]+)')
@core.rule(r'(?i).*youtu\.be/([-_a-z0-9]+)')
def youtube_lookup(inp):
    info = _youtube_info(inp.text)
    if not info:
        return lex.youtube.not_found
    return lex.youtube.result(**info[0])


def _youtube_info(*video_ids):
    results = googleapi(
        'youtube', 'v3', 'videos',
        part='contentDetails,snippet,statistics', id=','.join(video_ids))

    return [dict(
        title=r['snippet']['title'],
        duration=r['contentDetails']['duration'][2:].lower(),
        likes=r.get('statistics', {}).get('likeCount'),
        dislikes=r.get('statistics', {}).get('dislikeCount'),
        views=r.get('statistics', {}).get('viewCount'),
        channel=r['snippet']['channelTitle'],
        date=r['snippet']['publishedAt'][:10])
        for r in results]


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


@core.command
@parser.imdb
def imdb(inp, *, title, search, imdbid, year):
    """Look up information about a movie."""
    params = dict(t=title, s=search, i=imdbid, y=year, plot='short', r='json')
    params = {k: v for k, v in params.items() if v}
    response = requests.get('http://www.omdbapi.com/', params=params).json()
    data = {k.lower(): v for k, v in response.items()}

    if 'search' in data:
        results = data['search']

        tools.save_results(
            inp, [i['imdbID'] for i in results],
            lambda x: imdb._func(
                inp, title=None, search=None, imdbid=x, year=None))

        results = [(i['Title'], i['Year']) for i in results]
        results = ['{} ({})'.format(title, year) for title, year in results]
        return lex.options(options=results)

    if 'error' in data:
        return lex.imdb.not_found

    return lex.imdb.result(**data)


@core.rule(r'https?://twitter.com/[^/]+/status/([0-9]+)')
def twitter_lookup(inp):
    api = tools._get_twitter_api()

    tweet = api.get_status(inp.text)
    return lex.twitter_lookup(
        name=tweet.user.name, text=tweet.text.replace('\n', ' '),
        date=arrow.get(tweet.created_at).format('YYYY-MM-DD'),
        favorites=tweet.favorite_count)


@core.command
@core.alias('ddg')
@parser.duckduckgo
@indexed_cache
def duckduckgo(query):
    """Ask the ducks if they know anything about the topic."""
    response = requests.get(
        'https://duckduckgo.com/html/', params={'q': query})
    soup = bs4.BeautifulSoup(response.text, 'html.parser')
    results = soup(class_='web-result')

    return [
        lex.duckduckgo.result(
            index=idx + 1,
            total=len(results),
            title=r.find(class_='result__a').text,
            url=r.find(class_='result__a')['href'],
            text=r.find(class_='result__snippet').text)
        for idx, r in enumerate(results)]


def get_steam_game(steam_id, url=True):
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
        genres=genres, url=steam_id if url else None)


@core.rule(r'https?://store.steampowered.com/app/([0-9]+)')
def steam_lookup(inp):
    return get_steam_game(inp.text, url=False)


@core.command
@parser.steam
def steam(inp, title, _cache={}):
    """Find steam games by their title."""
    if not _cache:
        data = requests.get(
            'http://api.steampowered.com/ISteamApps/GetAppList/v0001/').json()
        data = data['applist']['apps']['app']
        data = {i['name'].lower(): i['appid'] for i in data}
        _cache.update(data)
    if title in _cache:
        return get_steam_game(_cache[title])
    for k, v in _cache.items():
        if title in k:
            return get_steam_game(v)
    return lex.steam.not_found


###############################################################################


@core.command
@core.alias('w')
@parser.websearch
def wikipedia(inp, *, query):
    """Get wikipedia page about the topic."""
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
@parser.dictionary
def dictionary(inp, *, query):
    """Look up dictionary definition of a word or a phrase."""
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
    """Show urban defitiontion of a word or a phrase."""
    url = 'http://api.urbandictionary.com/v0/define?term=' + query
    data = requests.get(url).json()
    if not data['list']:
        return lex.not_found.generic
    result = data['list'][0]
    return '{word}: {definition}'.format(**result)


@core.command
@parser.websearch
def tvtropes(inp, *, query):
    """Show laconic description of the trope, and a link to the full page."""
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
