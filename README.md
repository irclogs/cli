# `Irclog cli`
### a python cli app to view irclogs

The logs are stored in couchdb.

```
usage: irclog-cli.py [-h] [--verbose] {search,follow,dump,list} ...

options:
  -h, --help            show this help message and exit
  --verbose, -v

subcommands:
  {search,follow,dump,list}
    search              search <channel> <text…>
    follow              follow <channel> [backlog limit, default 100]
    dump                dump <channel> <file>
    list                list all channels
```

<details>
<summary>Depends on: `requests`</summary>

```
pip install -r requirements.txt
```
</details>

### Dump channel history with curl and jq

```
CHANNEL=xyz
curl "https://db.softver.org.mk/irclog/_changes?include_docs=true&filter=_selector" \
    -H "Content-Type: application/json" \
    -d '{"selector": {"channel": "'$CHANNEL'"}}' > dump.json
```

The dump is a json object, that has a `results` field which is a list of changes items. Each change has the `doc` field. Let's remove the changes items, we're only interested in the `doc`: `jq '.results|=map(.doc)'`.

To get get just the results list: `jq '.results|=map(.doc) | .results'`.

The changes are not always delivered in order, so let's sort the list by the timestamp: 
```
jq '.results|=(map(.doc)|sort_by(.timestamp))| .results' < dump.json
```

Next time you dump, you can use the `last_seq` field in the dump, so you don't download everything.

```
LAST_SEQ=`jq '.last_seq' < dump.json`
CHANNEL=xyz
curl "https://db.softver.org.mk/irclog/_changes?include_docs=true&filter=_selector&since=$LAST_SEQ" \
    -H "Content-Type: application/json" \
    -d '{"selector": {"channel": "'$CHANNEL'"}}' > dump2.json
```
