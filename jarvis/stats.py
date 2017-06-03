#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import pyscp
import textwrap

from dominate import tags as dt

from . import core, lex, ext


###############################################################################
# Templates
###############################################################################


CHART = """
google.charts.setOnLoadCallback({name});

function {name}() {{
    var data = new google.visualization.arrayToDataTable([
{data}
        ]);

    var options = {options};

    var chart = new google.visualization.{class_name}(
        document.getElementById('{name}'));

    chart.draw(data, options);
}}
"""

USER = """
[[html]]
<base target="_parent" />
<style type="text/css">
@import url(http://scp-stats.wdfiles.com/local--theme/scp-stats/style.css);
</style>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js">
</script>

<script type="text/javascript">
google.charts.load('current', {{'packages':['table', 'corechart']}});
{summary_table}
{articles_chart}
{articles_table}
</script>

<div id="summary_table"></div>
<div id="articles_chart"></div>
<div style="clear: both;"></div>
<h4>Articles</h4>
<div id="articles_table"></div>
[[/html]]
"""

###############################################################################
# Helper Functions
###############################################################################


def html(tag, text, **kwargs):
    if 'cls' in kwargs:
        kwargs['class'] = kwargs.pop('cls')
    attrs = ' '.join('{}="{}"'.format(k, v) for k, v in kwargs.items())
    if attrs:
        attrs = ' ' + attrs
    return '<{tag}{attrs}>{text}</{tag}>'.format(
        tag=tag, text=text, attrs=attrs)

###############################################################################
# Chart Classes
###############################################################################


class Chart:

    def format_row(self, row, indent):
        row = ',\n'.join(map(repr, row))
        row = textwrap.indent(row, '    ')
        row = '[\n{}\n]'.format(row)
        return textwrap.indent(row, ' ' * indent)

    def render(self):
        data = ',\n'.join([self.format_row(r, 8) for r in self.data])
        return CHART.format(
            name=self.name,
            class_name=self.class_name,
            data=data,
            options=self.options)


class SummaryTable(Chart):

    def __init__(self, pages, name):
        self.name = 'summary_table'
        self.class_name = 'Table'

        self.populate(pages, name)

        self.options = {
            'sort': 'disable',
            'width': '100%'}

    def populate(self, pages, name):
        self.data = [
            ['Category', 'Page Count', 'Net Rating', 'Average'],
            ['Total', pages.count, pages.rating, pages.average]]
        for k, v in pages.split_page_type().items():
            self.data.append([k, v.count, v.rating, v.average])
        for k, v in pages.split_relation(name).items():
            self.data.append([k, v.count, v.rating, v.average])


class ArticlesChart(Chart):

    def __init__(self, pages, user):
        self.name = 'articles_chart'
        self.class_name = 'ColumnChart'

        self.user = user

        self.populate(pages)

        self.options = {
            'backgroundColor': '#e7e9dc',
            'chartArea': {
                'left': 0,
                'top': 0,
                'width': '100%',
                'height': '100%'},
            'hAxis': {'textPosition': 'none'},
            'vAxis': {
                'textPosition': 'none',
                'gridlines': {'color': '#e7e9dc'},
                'minValue': 0},
            'legend': {'position': 'none'},
            'height': 350,
            'tooltip': {'isHtml': 1}}

    def populate(self, pages):
        self.data = [[
            'Title',
            'Rating',
            {'role': 'tooltip', 'p': {'html': 'true'}},
            {'role': 'style'}]]

        for p in pages:
            if 'scp' in p.tags:
                color = 'color: #db4437'
            elif 'tale' in p.tags:
                color = 'color: #4285f4'
            else:
                color = 'color: #f4b400'

            date = p.metadata[self.user].date[:10] or '-'

            tooltip = dt.table(
                dt.tr(dt.td(p.title, colspan=2)),
                dt.tr(dt.td('Rating:'), dt.td(p.rating)),
                dt.tr(dt.td('Created:'), dt.td(date)),
                cls='articles_chart_tooltip')

            self.data.append([
                p.title,
                p.rating,
                tooltip.render(pretty=False),
                color])


class ArticlesTable(Chart):

    def __init__(self, pages, user):
        self.name = 'articles_table'
        self.class_name = 'Table'

        self.populate(pages, user)

        self.options = {
            'showRowNumber': 1,
            'allowHtml': 1,
            'sortColumn': 1,
            'sortAscending': 0,
            'width': '100%'}

    def populate(self, pages, user):
        self.data = ['Title Rating Tags Link Created Role'.split()]

        for p in pages:
            tags = [html('b', t) if t in 'scp tale hub admin author' else t
                    for t in p.tags]
            tags = ', '.join(sorted(tags))

            link = html('a', p.url.split('/')[-1], href=p.url)

            role = p.metadata[user].role
            role = html('span', role, cls='rel-' + role)

            date = p.metadata[user].date[:10]

            self.data.append([p.title, p.rating, tags, link, date, role])


###############################################################################


def update_user(name):
    wiki = pyscp.wikidot.Wiki('scp-stats')
    wiki.auth(core.config.wiki.name, core.config.wiki.password)
    p = wiki('user:' + name.lower())

    pages = sorted(
        core.pages.related(name),
        key=lambda x: (x.metadata[name].date, x.created))
    pages = ext.PageView(pages)

    if not pages.articles:
        return lex.not_found.author
    data = USER.format(
        summary_table=SummaryTable(pages.primary(name), name).render(),
        articles_chart=ArticlesChart(pages.articles, name).render(),
        articles_table=ArticlesTable(
            [p for p in pages if p.tags], name).render())

    try:
        p.create(data, title=name, comment='automated update')
    except RuntimeError:
        pass
    return p.url
