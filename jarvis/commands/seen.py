#!/usr/bin/env python3

###############################################################################
# Module Imports
###############################################################################

import arrow

from jarvis import core, parser, lex, db


###############################################################################
# Parser
###############################################################################


@parser.parser
def prseen(pr):
    pr.add_argument(
        '--first', '-f',
        help="""Display the first recorded message said by the user.""")

    pr.add_argument(
        '--total', '-t',
        help="""Display the total number of messages said by the user.""")

    pr.add_argument(
        '--date', '-d',
        help="""Display exact date.""")

    pr.exclusive('first', 'total')

    pr.add_argument(
        'channel',
        re='#',
        nargs='?',
        help="""Switch to another channel.""")

    pr.add_argument(
        'user',
        type=str.lower,
        help='Username to look for.')

###############################################################################
# Command
###############################################################################


@core.command
@prseen
@core.crosschannel
def seen(inp, *, user, first, total, date):
    """Show the first message said by the user."""
    if user == core.config.irc.nick:
        return lex.seen.self

    query = db.Message.find(user=user, channel=inp.channel)
    if not query.exists():
        return lex.seen.never

    if total:
        total = query.count()
        time = arrow.get(arrow.now().format('YYYY-MM'), 'YYYY-MM')
        this_month = query.where(db.Message.time > time.timestamp).count()
        return lex.seen.total(
            user=user, total=total, this_month=this_month)

    seen = query.order_by(
        db.Message.time if first else db.Message.time.desc()).get()
    time = arrow.get(seen.time)
    time = time.humanize() if not date else 'on {0:YYYY-MM-DD}'.format(time)
    msg = lex.seen.first if first else lex.seen.last
    return msg(user=user, time=time, text=seen.text)
