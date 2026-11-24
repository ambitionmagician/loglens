#!/usr/bin/env python3
"""LogLens - Summarize log files at a glance.

Examples:
    $ loglens.py /var/log/syslog
    $ cat /var/log/app.log | loglens.py --top 5
"""

import argparse
import re
import sys
from collections import Counter
from datetime import datetime

LEVELS = ['TRACE', 'DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL']
LEVEL_MAP = {
    'TRACE': 'TRACE', 'DEBUG': 'DEBUG', 'INFO': 'INFO',
    'WARN': 'WARN', 'WARNING': 'WARN',
    'ERROR': 'ERROR', 'FATAL': 'FATAL', 'CRITICAL': 'FATAL'
}
LEVEL_PATTERN = re.compile(r'\b(' + '|'.join(LEVELS) + r')\b', re.IGNORECASE)
TIMESTAMP_PATTERN = re.compile(
    r'^\s*(?:'
    r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)|'
    r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})'
    r')\s*'
)
NORMALIZE_PATTERN = re.compile(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)|'
                               r'(0x[0-9a-fA-F]+)|(\d+)|([A-Fa-f0-9]{8,})')


def parse_args():
    parser = argparse.ArgumentParser(description='Summarize log file')
    parser.add_argument('FILE', nargs='?', default='-', help='Log file (default: stdin)')
    parser.add_argument('--top', type=int, default=10, help='Top N errors to show')
    parser.add_argument('--levels-only', action='store_true', help='Print only level table')
    return parser.parse_args()


def parse_timestamp(line):
    match = TIMESTAMP_PATTERN.match(line)
    if not match:
        return None
    ts_str = match.group(1) or match.group(2)
    for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%S.%f%z',
                '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f']:
        try:
            return datetime.strptime(ts_str.replace('T', ' ').split('.')[0] if '.' in ts_str else ts_str, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except ValueError:
        pass
    return None


def normalize_message(line):
    line = TIMESTAMP_PATTERN.sub('', line)
    line = NORMALIZE_PATTERN.sub('#', line)
    return line.strip()


def detect_level(line):
    match = LEVEL_PATTERN.search(line)
    if match:
        return LEVEL_MAP.get(match.group(1).upper(), 'OTHER')
    return 'OTHER'


def process_lines(lines):
    level_counts = Counter()
    error_messages = Counter()
    timestamps = []
    line_count = 0

    for line in lines:
        line = line.rstrip('\n\r')
        if not line:
            continue
        line_count += 1
        level = detect_level(line)
        level_counts[level] += 1
        if level in ('ERROR', 'FATAL'):
            norm_msg = normalize_message(line)
            error_messages[norm_msg] += 1
        ts = parse_timestamp(line)
        if ts:
            timestamps.append(ts)

    return level_counts, error_messages, timestamps, line_count


def format_time_span(timestamps):
    if not timestamps:
        return 'N/A'
    timestamps.sort()
    start = timestamps[0].strftime('%Y-%m-%d %H:%M:%S')
    end = timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')
    return f'{start} -- {end}'


def print_report(level_counts, error_messages, timestamps, line_count, top_n, levels_only):
    if line_count == 0:
        print('Empty input', file=sys.stderr)
        sys.exit(2)

    print('=' * 60)
    print('LOGLENS SUMMARY')
    print('=' * 60)
    print()

    print('LEVEL COUNTS')
    print('-' * 40)
    total = sum(level_counts.values())
    for level in LEVELS + ['OTHER']:
        count = level_counts.get(level, 0)
        pct = (count / total * 100) if total else 0
        print(f'{level:10} {count:8} ({pct:5.1f}%)')
    print(f'{"TOTAL":10} {total:8}')
    print()

    if levels_only:
        return

    print('TIME SPAN')
    print('-' * 40)
    print(format_time_span(timestamps))
    print()

    print(f'TOP {top_n} ERRORS')
    print('-' * 40)
    for msg, count in error_messages.most_common(top_n):
        display_msg = msg[:50] + '...' if len(msg) > 50 else msg
        print(f'[{count:5}] {display_msg}')
    if not error_messages:
        print('No errors found.')
    print()

    print('=' * 60)


def main():
    args = parse_args()

    if args.FILE == '-':
        lines = sys.stdin
    else:
        try:
            lines = open(args.FILE, 'r', encoding='utf-8', errors='replace')
        except FileNotFoundError:
            print(f'File not found: {args.FILE}', file=sys.stderr)
            sys.exit(1)

    try:
        level_counts, error_messages, timestamps, line_count = process_lines(lines)
    finally:
        if lines is not sys.stdin:
            lines.close()

    print_report(level_counts, error_messages, timestamps, line_count, args.top, args.levels_only)


if __name__ == '__main__':
    main()
