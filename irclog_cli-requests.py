#! /usr/bin/env python3
'''
Usage:

  irclog_cli.py <channel>

'''
import requests
import json, sys
from datetime import datetime


def print_message(doc):
    tm = datetime.fromtimestamp(doc['timestamp'])
    tm = tm.strftime('%H:%M:%S')
    print("%s %s: %s" % (tm, doc['sender'], doc['message']))

def get_last_100(channel, limit=100):
    startkey = '["%s",{}]' % channel
    endkey = '["%s",0]' % channel

    params = dict(update_seq='true', reduce='false', descending='true',
            limit=limit, include_docs='true', startkey=startkey, endkey=endkey)
    req = requests.get("https://irc.softver.org.mk/ddoc/_view/channel", params=params)

    last_100 = json.loads(req.text)
    def _gen():
        for row in reversed(last_100['rows']):
            yield row['doc']
    return last_100['update_seq'], _gen()

def get_changes(channel, since):
    params = dict(feed='continuous', channel=channel, filter='log/channel',
            heartbeat=30000, include_docs='true', since=since)
    req = requests.get("https://irc.softver.org.mk/api/_changes", params=params, stream=True, timeout=60)

    for row in req.iter_lines(chunk_size=1, decode_unicode=True):
        if row.strip():
            change = json.loads(row)
            doc = change['doc']
            yield doc

def list_channels():
    req = requests.get("https://irc.softver.org.mk/ddoc/_view/channel", params = {group_level:1})
    doc = json.loads(req.text)
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
