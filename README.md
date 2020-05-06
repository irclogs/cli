# `Irclog cli`
### a python cli app to view irclogs

The logs are stored in couchdb.

```
usage: irclog-cli.py [-h] [--verbose] {search,follow,list} ...

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v

subcommands:
  {search,follow,list}
    search              search <channel> <text…>
    follow              follow <channel> [backlog limit, default 100]
    list                list all channels
```

<details>
<summary>Depends on: `requests`</summary>

```
pip install -r requirements.txt
```
</details>
