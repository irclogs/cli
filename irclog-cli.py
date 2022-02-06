#! /usr/bin/python

import requests
from requests.compat import urljoin

import pprint
import json
from datetime import datetime

global VERBOSE
IRCLOG_URL = "https://db.softver.org.mk/irclog/"


def print_message(doc):
    if VERBOSE:
        pprint.pprint(doc)
        return

    t = datetime.fromtimestamp(doc["timestamp"])
    tm = t.strftime("%H:%M:%S")
    dt = t.strftime("%Y-%m-%d")
    sender = doc["sender"]
    msg = doc.get("message", doc.get("notice"))
    print(f"{dt} {tm} {sender}: {msg}")


def get_backlog(channel, limit=100):
    url = urljoin(IRCLOG_URL, "_design/log/_view/channel")
    startkey = [channel, {}]
    endkey = [channel, 0]

    query = dict(
        update_seq="true",
        reduce="false",
        descending="true",
        limit=limit,
        include_docs="true",
        startkey=startkey,
        endkey=endkey,
    )
    req = requests.post(url, json=query)
    if not req.ok:
        req.raise_for_status()

    backlog = req.json()
    update_seq = backlog["update_seq"]

    def _gen():
        for row in sorted(backlog["rows"], key=lambda r: r["doc"]["timestamp"]):
            yield row["doc"]

    return update_seq, _gen()


def get_changes(channel, since):
    url = urljoin(IRCLOG_URL, "_changes")
    query = dict(
        feed="continuous",
        filter="_selector",
        heartbeat=30000,
        include_docs="true",
        since=since,
    )
    data = {"selector": {"channel": channel}}
    req = requests.post(url, params=query, json=data, stream=True, timeout=60)
    if not req.ok:
        req.raise_for_status()

    for row in req.iter_lines(chunk_size=None, decode_unicode=True):
        if row.strip():
            change = json.loads(row)
            doc = change["doc"]
            yield change["seq"], doc


def list_channels(_args):
    url = urljoin(IRCLOG_URL, "_design/log/_view/channel")
    query = {"group_level": 1}
    req = requests.post(url, json=query)
    if not req.ok:
        req.raise_for_status()

    for ch in req.json()["rows"]:
        print(ch["key"][0], ch["value"])


def search(args):
    needle = " ".join(args.needle)
    url = urljoin(IRCLOG_URL, "_find?include_docs=true")
    q = {
        "selector": {
            "channel": args.channel,
            "message": {"$regex": needle},
            # "timestamp": { "$gt" или "$lt": 1537798438 }
        },
        "fields": ["_id", "timestamp", "sender", "message", "channel"],
    }
    req = requests.post(url, json=q)
    if not req.ok:
        req.raise_for_status()

    for doc in req.json()["docs"]:
        print_message(doc)


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


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", "-v", action="count")
    subparsers = parser.add_subparsers(title="subcommands")

    s = subparsers.add_parser("search", help="search <channel> <text…>")
    s.add_argument("channel")
    s.add_argument("needle", metavar="text", nargs="+", help="text to search for")
    s.set_defaults(func=search)

    f = subparsers.add_parser(
        "follow", help="follow <channel> [backlog limit, default 100]"
    )
    f.add_argument("channel", help="channel to look at")
    f.add_argument("limit", default=100, nargs="?", type=int, help="limit backlog")
    f.set_defaults(func=follow)

    l = subparsers.add_parser("list", help="list all channels")
    l.set_defaults(func=list_channels)

    args = parser.parse_args()
    VERBOSE = args.verbose
    if "func" in args:
        args.func(args)
    else:
        parser.print_help()
