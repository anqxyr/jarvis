#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################


###############################################################################


TABLE = """
<style type="text/css">
@import url(http://scp-stats.wdfiles.com/local--theme/scp-stats/style.css);
</style>
<script type="text/javascript" src="https://www.gstatic.com/charts/loader.js">
</script>
<script type="text/javascript">
    google.charts.load('current', {{'packages':['table']}});
    google.charts.setOnLoadCallback(drawTable);

    function drawTable() {{
        var data = new google.visualization.DataTable();
        {columns}
        data.addRows([
            {rows}
        ]);

        var table = new google.visualization.Table(
            document.getElementById('{name}'));

        table.draw(data, {{
            showRowNumber: true, allowHtml: true,
            width: '100%', height: '100%'}});
    }}
</script>
<div id="{name}"></div>
"""

###############################################################################


class Table:

    def __init__(self, name):
        self.name = name
        self.columns = []
        self.rows = []

    def add_column(self, name, coltype='string'):
        self.columns.append((name, coltype))

    def add_row(self, *values):
        self.rows.append(list(values))

    def render(self):
        columns = '\n        '.join('data.addColumn({}, {});'.format(
            repr(b), repr(a)) for a, b in self.columns)
        rows = ',\n            '.join(map(repr, self.rows))
        return TABLE.format(columns=columns, rows=rows, name=self.name)
