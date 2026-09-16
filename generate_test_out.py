#!/usr/bin/env python3
"""Generate a test output file by appending one source line per second.

Reads lines from data/captura-tcs-gps.txt and appends them, one at a time
with a 1-second interval, to data/test-out.txt. This simulates a live feed
that tail_file.py can follow.

Usage:
    python3 generate_test_out.py [--interval SECONDS] [--reset]
"""
import argparse
import os
import time

BASE_DIR = os.path.dirname(__file__)
SOURCE_PATH = os.path.join(BASE_DIR, "data", "captura-tcs-gps.txt")
OUT_PATH = os.path.join(BASE_DIR, "data", "test-out.txt")


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds to wait between appended lines (default: 1.0).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Truncate the output file before starting.",
    )
    parser.add_argument(
        "--source",
        default=SOURCE_PATH,
        help=f"Source file to read from (default: {SOURCE_PATH}).",
    )
    parser.add_argument(
        "--out",
        default=OUT_PATH,
        help=f"Output file to append to (default: {OUT_PATH}).",
    )
    return parser.parse_args()


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
        for i, line in enumerate(lines, start=1):
            if not line.endswith("\n"):
                line += "\n"
            with open(args.out, "a") as out:
                out.write(line)
                out.flush()
            print(f"[{i}/{len(lines)}] appended", flush=True)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
