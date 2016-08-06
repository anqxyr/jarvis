#!/usr/bin/env python3
"""Bot Commands related to or interactin with the scp-wiki."""

###############################################################################
# Module Imports
###############################################################################

import arrow
import random as rand
import re

from . import core, ext, parser, lex, stats, tools

###############################################################################
# Internal Methods
###############################################################################


def show_page(page, rating=True):
    attribution = page.build_attribution_string(
        templates=lex.show_page.templates._raw,
        group_templates=lex.show_page.group_templates._raw)
    out = lex.show_page.summary if rating else lex.show_page.nr_summary
    return out(page=page, attribution=attribution)


###############################################################################
# Find And Lookup Functions
###############################################################################


def show_search_results(inp, results):
    """Process page search results."""
    if not results:
        return lex.not_found.page
    elif len(results) == 1:
        return show_page(results[0])
    else:
        tools.save_results(inp, results, show_page)
        results = [p.title for p in results]
        head, tail = results[:3], results[3:]
        output = ', '.join('\x02{}\x02'.format(i) for i in head)
        if tail:
            output += ' and {} more...'.format(len(tail))
        return output


def show_search_summary(inp, results):
    if not results:
        return lex.not_found.page
    pages = ext.PageView(results).sorted('created')
    return lex.summary.search(
        count=pages.count,
        authors=len(pages.authors),
        rating=pages.rating,
        average=pages.average,
        first=arrow.get(pages[0].created).humanize(),
        last=arrow.get(pages[-1].created).humanize(),
        top_title=pages.sorted('rating')[-1].title,
        top_rating=pages.sorted('rating')[-1].rating)


def author_search(inp, func):
    """Find author via partial name, and process results."""
    text = (inp.text or inp.user).lower()
    authors = {i for p in core.pages for i in p.metadata}
    results = sorted(i for i in authors if text in i.lower())
    if not results:
        return lex.not_found.author
    elif len(results) == 1:
        return func(results[0])
    else:
        tools.save_results(inp, results, func)
        return tools.choose_input(results)


def find_pages(
        pages, *, partial, exclude, strict,
        tags, author, rating, created, fullname):
    if tags:
        pages = pages.tags(tags)
    if rating:
        pages = pages.with_rating(rating)
    if created:
        pages = pages.created(created)

    if author:
        pages = [
            p for p in pages if any(author in a.lower() for a in p.metadata)]
    if fullname:
        pages = [p for p in pages if p.title.lower() == fullname]
        return pages[0]

    results = []
    for p in pages:
        words = p.title.lower().split()
        words = {''.join(filter(str.isalnum, w)) for w in words}

        if exclude and words & set(exclude):
            continue
        if strict and not words >= set(strict):
            continue
        if partial and not all(i in p.title.lower() for i in partial):
            continue

        results.append(p)

    return results


@parser.search
def _page_search_base(inp, pages, *, summary, **kwargs):
    if not inp.text:
        return lex.input.incorrect
    func = show_search_summary if summary else show_search_results
    return func(inp, find_pages(pages, **kwargs))


@core.command
def search(inp):
    return _page_search_base(inp, core.pages)


@core.command
def tale(inp):
    return _page_search_base(inp, core.pages.tags('tale'))


@core.command
def wanderers_library(inp):
    return _page_search_base(inp, core.wlpages)


@core.command
def tags(inp):
    return show_search_results(inp, core.pages.tags(inp.text))


@core.command
def name_lookup(inp):
    pages = [p for p in core.pages if p.url.split('/')[-1] == inp.text.lower()]
    return show_search_results(inp, pages)


@core.command
def author(inp):
    return author_search(inp, author_summary)


@core.command
def author_details(inp):
    return author_search(inp, stats.update_user)


###############################################################################
# Output Generation Functions
###############################################################################


def search_results(results):
    """Display search results."""
    results = [p.title for p in results]
    head, tail = results[:3], results[3:]
    output = ', '.join('\x02{}\x02'.format(i) for i in head)
    if tail:
        output += ' and {} more...'.format(len(tail))
    return output


def author_summary(name):
    """Compose author summary."""
    pages = core.pages.related(name)
    url = pages.tags('author')[0].url if pages.tags('author') else None
    url = ' ({})'.format(url) if url else ''
    pages = pages.articles
    if not pages:
        return lex.not_found.author
    template = '\x02{1.count}\x02 {0}'.format
    tags = ', '.join(template(*i) for i in pages.split_page_type().items())
    rels = ', '.join(template(*i) for i in pages.split_relation(name).items())
    last = sorted(pages, key=lambda x: x.created, reverse=True)[0]
    return lex.summary.author(
        name=name, url=url, pages=pages, rels=rels, tags=tags,
        primary=pages.primary(name), last=last)


###############################################################################
# Errors
###############################################################################


def errors_orphaned():
    urls = [p.url for p in core.pages]
    urls.extend([p.url for p in core.wiki.list_pages(
        name='scp-*', created_at='last 3 hours')])
    pages = [k for k in core.wiki.titles() if k not in urls]
    return map(core.wiki, pages)


def errors_untagged():
    return core.wiki.list_pages(tags='-')


def errors_untitled():
    pages = core.pages.tags('scp').pages
    pages.extend(core.wiki.list_pages(name='scp-*', created_at='last 3 hours'))
    pages = [p for p in pages if p.url not in core.wiki.titles()]
    pages = [p for p in pages if 'scp-1848' not in p.url]
    return pages


def errors_deleted():
    return core.wiki.list_pages(category='deleted')


def errors_vote():
    return core.wiki.list_pages(
        tags='-in-deletion -archived -author',
        rating='<-10', created_at='older than 24 hours')


@core.multiline
@core.require(channel=core.config.irc.sssc)
@core.command
def errors(inp):
    all_pages = []

    for name in ['untagged', 'untitled', 'deleted', 'vote', 'orphaned']:
        pages = list(eval('errors_' + name)())
        if not pages:
            continue
        all_pages.extend(pages)
        pages = [p.url.split('/')[-1] for p in pages]
        pages = map('\x02{}\x02'.format, sorted(pages))
        yield getattr(lex.errors, name)(pages=', '.join(pages))

    if not all_pages:
        yield lex.errors.none
    else:
        tools.save_results(inp, all_pages, show_page)
        yield lex.errors.done


@core.command
@core.cooldown(1200)
@core.multiline
def cleantitles(inp):
    yield lex.cleantitles.start

    pages = [
        'scp-series', 'scp-series-2', 'scp-series-3',
        'joke-scps', 'scp-ex', 'archived-scps']
    wiki = core.pyscp.wikidot.Wiki('scp-wiki')
    wiki.auth(core.config.wiki.name, core.config.wiki.password)
    orphaned = [p.url.split('/')[-1] for p in errors_orphaned()]

    def clean_line(line, purge):
        pattern = r'^\* \[\[\[([^\]]+)\]\]\] - .+$'
        parsed = re.match(pattern, line)
        if not parsed:
            return line
        name = parsed.group(1)
        if name.lower() not in orphaned:
            return line
        if not purge:
            return '* [[[{}]]] - [ACCESS DENIED]'.format(name)

    for page in map(wiki, pages):
        source = page.source.split('\n')
        purge = 'scp-series' not in page.url
        source = [clean_line(i, purge) for i in source]
        source = [i for i in source if i is not None]
        source = '\n'.join(source)
        if source != page.source:
            page.edit(source, comment='clean titles')

    yield lex.cleantitles.end


###############################################################################
# Misc
###############################################################################


@core.command
@parser.random
def random(inp, **kwargs):
    pages = find_pages(core.pages, **kwargs) if inp.text else core.pages
    if pages:
        return show_page(rand.choice(pages))
    else:
        return lex.not_found.page


@core.command
@core.cooldown(120)
@core.multiline
def lastcreated(inp, cooldown={}, **kwargs):
    kwargs = dict(
        body='title created_by created_at rating',
        order='created_at desc',
        limit=3)
    pages = core.wiki.list_pages(**kwargs)
    return [show_page(p, rating=False) for p in pages]


@core.command
@parser.unused
def unused(inp, *, random, last, count, prime, palindrome, divisible):
    numbers = range(2, 3000)

    if prime:
        numbers = [i for i in numbers if all(i % k for k in range(2, i))]
    if palindrome:
        numbers = [
            i for i in numbers if str(i).zfill(3) == str(i).zfill(3)[::-1]]
    if divisible:
        numbers = [i for i in numbers if i % divisible == 0]

    slots = ['scp-{:03d}'.format(i) for i in numbers]
    used_slots = {p._body['fullname'] for p in core.pages.tags('scp')}
    unused_slots = [i for i in slots if i not in used_slots]

    if not unused_slots:
        return lex.not_found.unused

    if count:
        return lex.unused.count(count=len(unused_slots))

    if random:
        result = rand.choice(unused_slots)
    elif last:
        result = unused_slots[-1]
    else:
        result = unused_slots[0]

    return 'http://www.scp-wiki.net/' + result


@core.command
def staff(inp, staff={}):
    if not inp.text:
        return 'http://www.scp-wiki.net/meet-the-staff'

    cats = {'Admin': 1, 'Mod': 2, 'Staff': 3}

    if not staff:
        for key in cats:
            staff[key] = {}

        soup = core.wiki('meet-the-staff')._soup
        for k, v in cats.items():
            for i in soup(class_='content-panel')[v]('p'):
                staff[k][i.strong.text.lower()] = i.text

    for cat in cats:
        for k, v in staff[cat].items():
            if inp.text.lower() in k:
                return '[{}] {}'.format(cat, v)

    return lex.not_found.staff
