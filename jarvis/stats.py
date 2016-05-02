#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pathlib
import pygal
import pyscp


from . import core, gviz


###############################################################################


def update_user(name):
    wiki = pyscp.wikidot.Wiki('scp-stats')
    wiki.auth(core.config['wiki']['name'], core.config['wiki']['pass'])
    p = wiki('user:' + name.lower())
    p.create(get_user(name), title=name, comment='automated update')
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
    table = gviz.Table('articles')

    table.add_column('Title')
    table.add_column('Rating', 'number')
    table.add_column('Tags')
    table.add_column('Link')
    table.add_column('Created')
    table.add_column('Relation')

    pages = [p for p in core.pages.related(name) if p.tags]
    for p in sorted(pages, key=lambda x: x.rating, reverse=True):
        tags = ['<b>{}</b>'.format(t) if t in 'scp tale hub admin author'
                else t for t in p.tags]
        tags = ', '.join(sorted(tags))
        link = '<a href={}>{}</a>'.format(p.url, p.url.split('/')[-1])
        relation = '<span class="rel-{0}">{0}</span>'.format(
            p.metadata[name][0])
        table.add_row(p.title, p.rating, tags, link, p.created[:10], relation)
    return table.render()


def plot_user_pages(name):
    pages = core.pages.related(name).articles
    plot = pygal.Bar(
        style=pygal.style.CleanStyle,
        show_x_labels=False,
        show_legend=False, show_y_guides=False,
        margin=0, width=800, height=400)

    pages = sorted(pages, key=lambda x: x.created)
    plot.x_labels = [p.created[:10] for p in pages]
    data = []
    for p in pages:
        if 'scp' in p.tags:
            color = '#DC0000'
        elif 'tale' in p.tags:
            color = '#4040DD'
        else:
            color = '#FF9900'
        data.append({'value': p.rating, 'label': p.title, 'color': color})
    plot.add('Rating', data)

    path = 'images/users/{}/'.format(name)
    try:
        pathlib.Path(path).mkdir(parents=True)
    except FileExistsError:
        pass
    plot.render_to_file(path + 'pages.svg')
    return '{}:8000/users/{}/pages.svg'.format(
        core.config['aws']['address'], name)


def get_plot(url, css_class):
    data = [
        '[[div id="iframe-plot-pages"]]',
        '[[html]]',
        '<div class="plot-pages">',
        '<embed type="image/svg+xml" src="{}"/>',
        '</div>',
        '[[/html]]',
        '[[/div]]']
    return '\n'.join(data).format(url)


def get_user(name):
    source = [
        get_plot(plot_user_pages(name), 'plot-pages'),
        user_summary(name),
        '~~~~',
        '++ Articles',
        '[[div id="iframe-articles"]]',
        '[[html]]',
        user_articles(name),
        '[[/html]]',
        '[[/div]]']
    return '\n'.join(source)
