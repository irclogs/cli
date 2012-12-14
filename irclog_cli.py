#! /usr/bin/env python2
'''
Usage:

  irclog_cli.py <channel>

'''
from restkit import Resource
from datetime import datetime
import json, sys

irclog = Resource("https://irc.softver.org.mk/")

def print_message(doc):
    tm = datetime.fromtimestamp(doc['timestamp'])
    tm = tm.strftime('%H:%M:%S')
    out = "%s %s: %s" % (tm, doc['sender'], doc['message'])
    print(out)

def get_last_100(channel):
    startkey = '["%s",{}]' % channel
    endkey = '["%s",0]' % channel

    req = irclog.get("ddoc/_view/channel", update_seq='true', reduce='false', descending='true',
            limit=100, include_docs='true', startkey=startkey, endkey=endkey)

    last_100 = json.loads(req.body_string())
    def _gen():
        for row in reversed(last_100['rows']):
            yield row['doc']
    return last_100['update_seq'], _gen()

def get_changes(channel, since):

    req = irclog.get("api/_changes", feed='continuous', channel=channel, filter='log/channel',
            heartbeat=30000, include_docs='true', since=since)

    for row in req.body_stream():
        if row.strip():
            change = json.loads(row)
            doc = change['doc']
            yield doc

def list_channels():
    req = irclog.get('ddoc/_view/channel', group_level=1)
    doc = json.loads(req.body_string())
    for ch in doc['rows']:
        yield ch['key'][0], ch['value']

def main():
    try:
        channel = sys.argv[1]
    except:
        print(__doc__)
        exit(1)
    update_seq, msgs = get_last_100(channel)
    for msg in msgs:
        print_message(msg)
    for msg in get_changes(channel, update_seq):
        print_message(msg)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit(0)