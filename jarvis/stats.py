#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pyscp

from . import core

###############################################################################


def update_user(name):
    wiki = pyscp.wikidot.Wiki('scp-stats')
    wiki.auth(core.config['wiki']['name'], core.config['wiki']['pass'])
    p = wiki('user:' + name.lower())
    p.create(name, get_user(name), 'automated update')
    return p.url

###############################################################################


def user_summary(name):
    row = '||{0}||{1.count}||{1.rating}||{1.average}||'.format
    primary = core.pages.primary(name)
    tags = [row(*i) for i in primary.split_page_type().items()]
    rels = [row(*i) for i in core.pages.articles.split_relation(name).items()]
    return '\n'.join([
        '[[div class="stats"]]',
        '||~ Category||~ Page Count||~ Net Rating||~ Average||',
        row('Total', primary),
        '||||||||~ ||', '\n'.join(tags),
        '||||||||~ ||', '\n'.join(rels),
        '[[/div]]'])


def user_articles(name):
    row = '||{0.title}||{0.rating:+d}||{1}||{2}||{0.created:.10}||{3}||'
    articles = [
        '[[div class="articles"]]',
        '||~ Title||~ Rating||~ Tags||~ Link||~ Created||~ Relation||']
    pages = [p for p in core.pages.related(name) if p.tags]
    for p in sorted(pages, key=lambda x: x.rating, reverse=True):
        tags = ', '.join(sorted(p.tags)) or ' '
        link = '[[[{}|{}]]]'.format(p.url, p.url.split('/')[-1])
        relation = p.metadata[name][0]
        articles.append(row.format(p, tags, link, relation))
    articles.append('[[/div]]')
    return '\n'.join(articles)


def get_user(name):
    source = [
        user_summary(name),
        '~~~~',
        '++ Articles',
        user_articles(name)]
    return '\n'.join(source)
