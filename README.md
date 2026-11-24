# loglens

Summarizes a log file at a glance: how many lines at each level, the
most repeated errors with the noise stripped out, and the time span the
log covers. For the first five minutes of "what happened last night?"

## Quickstart

```
python3 loglens.py app.log
journalctl -u myservice | python3 loglens.py --top 5
```

## Usage

```
loglens.py [FILE] [--top N] [--levels-only]
```

Reads stdin when FILE is omitted or `-`. Levels are detected
case-insensitively (TRACE, DEBUG, INFO, WARN/WARNING, ERROR,
FATAL/CRITICAL; anything else counts as OTHER). Error messages are
normalized — timestamps, hex ids, and numbers become `#` — so the same
failure at different times groups into one line with a count.

## Examples

```
$ python3 loglens.py app.log
LEVEL COUNTS
INFO              2 ( 40.0%)
WARN              1 ( 20.0%)
ERROR             2 ( 40.0%)

TOP 10 ERRORS
[    2] ERROR disk # full on node #
```

## Configuration

None — all options are command-line flags.

## Limitations

- Level detection is keyword-based; exotic formats may land in OTHER.
- Time-span detection covers ISO-like and `YYYY-MM-DD HH:MM:SS`
  prefixes at the start of a line.

## License

MIT — see `LICENSE`.

By Dr. Brent Allen Jensen, Radical Blueprinting Research.

## Support this work

If this tool saved you time, you can support more open work like it:

- **BTC:** `15McijPo79Zx58NGyEf2PvaPtGqGmpztWn`
- **ETH:** `0x8C25164E9234E6A30b8E44485B79c5cE8419cF2B`

Thank you.
