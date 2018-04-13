#! /usr/bin/python

import requests
from requests.compat import urljoin

import json
from datetime import datetime

IRCLOG_URL = 'https://irc.softver.org.mk/'

def print_message(doc):
    tm = datetime.fromtimestamp(doc['timestamp'])
    tm = tm.strftime('%H:%M:%S')
    print("%s %s: %s" % (tm, doc['sender'], doc['message']))

def get_backlog(channel, limit=100):
    url = urljoin(IRCLOG_URL, '/ddoc/_view/channel')
    startkey = '["%s",{}]' % channel
    endkey = '["%s",0]' % channel

    params = dict(update_seq='true', reduce='false', descending='true',
            limit=limit, include_docs='true', startkey=startkey, endkey=endkey)
    req = requests.get(url, params=params)

    backlog = req.json()
    def _gen():
        for row in sorted(backlog['rows'], key=lambda r: r['doc']['timestamp']):
            yield row['doc']
    return backlog['update_seq'], _gen()

def get_changes(channel, since):
    url = urljoin(IRCLOG_URL, '/api/_changes')
    params = dict(feed='continuous', filter='_selector',
            heartbeat=30000, include_docs='true', since=since)
    data = { 'selector': {'channel':channel}}
    req = requests.post(url, params=params, json=data, stream=True, timeout=60)

    for row in req.iter_lines(chunk_size=None, decode_unicode=True):
        if row.strip():
            change = json.loads(row)
            doc = change['doc']
            yield change['seq'], doc

def list_channels(_args):
    url = urljoin(IRCLOG_URL, '/ddoc/_view/channel')
    req = requests.get(url, params = {'group_level':1})
    for ch in req.json()['rows']:
        print(ch['key'][0], ch['value'])

def search(args):
    needle = ' '.join(args.needle)
    url = urljoin(IRCLOG_URL, '/_search')
    q = {'query': {'bool': {'must': [
                {'match': {'channel': args.channel}},
                {'match': {'message': needle }}
        ]}}}
    r = requests.post(url, json=q)
    for hit in r.json()['hits']['hits']:
        print_message(hit['_source'])

def follow(args):
    update_seq, msgs = get_backlog(args.channel, limit=args.limit)
    for msg in msgs:
        print_message(msg)
    loop(args.channel, update_seq)

def loop(channel, update_seq):
    done = False
    while not done:
        try:
            for seq, msg in get_changes(channel, update_seq):
                print_message(msg)
                update_seq = seq
        except KeyboardInterrupt:
            print()
            done = True
        except requests.exceptions.ConnectionError:
            pass



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands')

    s = subparsers.add_parser('search', help='search <channel> <text…>')
    s.add_argument('channel')
    s.add_argument('needle', metavar='text', nargs='+', help='text to search for')
    s.set_defaults(func=search)

    f = subparsers.add_parser('follow', help='follow <channel> [backlog limit, default 100]')
    f.add_argument('channel', help='channel to look at')
    f.add_argument('limit', default=100, nargs='?', type=int, help='limit backlog')
    f.set_defaults(func=follow)

    l = subparsers.add_parser('list', help='list all channels')
    l.set_defaults(func=list_channels)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
