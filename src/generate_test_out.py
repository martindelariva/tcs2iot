#!/usr/bin/env python3
"""Generate a test output file by appending one source line per second.

Reads lines from a source capture file and appends them, one at a time with
a configurable interval, to an output file. This simulates a live feed that
processor.py (or tail_file.py) can follow.

Environment / defaults are container-friendly:
    SOURCE_FILE  default /data/captura-tcs-gps.txt
    OUT_FILE     default /data/test-out.txt
    INTERVAL     default 1.0 (seconds)

CLI flags override env vars.
"""
from __future__ import annotations

import argparse
import os
import time

SOURCE_PATH = os.getenv("SOURCE_FILE", "/data/captura-tcs-gps.txt")
OUT_PATH = os.getenv("OUT_FILE", "/data/test-out.txt")
INTERVAL = float(os.getenv("INTERVAL", "10.0"))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=INTERVAL)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--source", default=SOURCE_PATH)
    parser.add_argument("--out", default=OUT_PATH)
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Restart from the top when the source is exhausted.",
    )
    return parser.parse_args()


def feed_once(lines, out_path, interval):
    for i, line in enumerate(lines, start=1):
        if not line.endswith("\n"):
            line += "\n"
        with open(out_path, "a") as out:
            out.write(line)
            out.flush()
        print(f"[{i}/{len(lines)}] appended", flush=True)
        time.sleep(interval)


def main():
    args = parse_args()

    if args.reset and os.path.exists(args.out):
        open(args.out, "w").close()

    with open(args.source, "r") as src:
        lines = src.readlines()

    print(
        f"Appending {len(lines)} line(s) to {args.out} "
        f"every {args.interval}s (Ctrl-C to stop)...",
        flush=True,
    )

    try:
        feed_once(lines, args.out, args.interval)
        while args.loop:
            print("[generator] looping from top of source.", flush=True)
            feed_once(lines, args.out, args.interval)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
