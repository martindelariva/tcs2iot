#!/usr/bin/env python3
"""Tail a daily-rotating log file, parse each new line, and publish to IoT Core.

The data source writes one file per day named like:

    DataLog_20260922.csv        (DataLog_YYYYMMDD.csv)

This processor tails the current (newest) file. When a newer file appears
(i.e. the day rolls over and the source starts a new file), it finishes
draining the old file, closes it, and switches to the new one -- continuing
to stream new lines from there. No lines are lost across the rollover.

Ties together:
    - follow_daily() : tailing logic across daily-rotating files
    - parser.parse_to_json : raw line -> JSON
    - iot_publisher.Publisher : JSON -> AWS IoT Core topic

Configuration (config.ini, env vars override):
    WATCH_DIR      Directory containing the rotating files (default: /data)
    FILE_PATTERN   Glob for the rotating files (default: DataLog_*.csv)
    POLL_INTERVAL  Seconds between reads when idle (default: 0.25)
    plus all IOT_* keys consumed by iot_publisher.Publisher.
"""
from __future__ import annotations

import glob
import os
import time

from config import CONFIG
from iot_publisher import Publisher
from parser import ParseError, parse_to_json

WATCH_DIR = CONFIG.watch_dir
FILE_PATTERN = CONFIG.file_pattern
POLL_INTERVAL = CONFIG.poll_interval


def current_file(watch_dir: str, pattern: str) -> str | None:
    """Return the path of the newest matching file, or None if none exist.

    Files are named DataLog_YYYYMMDD.csv. Because YYYYMMDD sorts the same
    lexicographically as chronologically, the max filename is the latest day.
    """
    matches = glob.glob(os.path.join(watch_dir, pattern))
    if not matches:
        return None
    # Sort by the filename (not full path) so the date component decides.
    return max(matches, key=os.path.basename)


def follow(path: str, poll_interval: float = 0.25):
    """Yield each new line appended to a single fixed file.

    Kept for the simple single-file case. Starts at the end of the file and
    handles the file not existing yet and truncation.
    """
    print(f"[processor] waiting for {path}...", flush=True)
    while not os.path.exists(path):
        time.sleep(poll_interval)

    f = open(path, "r")
    f.seek(0, os.SEEK_END)
    try:
        while True:
            line = f.readline()
            if line:
                if line.endswith("\n"):
                    yield line
                else:
                    f.seek(-len(line), os.SEEK_CUR)
                    time.sleep(poll_interval)
                continue

            try:
                if os.path.getsize(path) < f.tell():
                    f.seek(0, os.SEEK_SET)
            except FileNotFoundError:
                while not os.path.exists(path):
                    time.sleep(poll_interval)
                f.close()
                f = open(path, "r")
            time.sleep(poll_interval)
    finally:
        f.close()


def follow_daily(watch_dir: str, pattern: str, poll_interval: float = 0.25):
    """Yield each new line from the current daily-rotating file.

    Behavior:
      - Waits until at least one matching file exists.
      - Tails the newest file. For the very first file we open, we seek to
        the END (only new lines are of interest for a live feed).
      - When a NEWER file appears, we keep reading the current file until it
        is fully drained, then close it and switch to the new file. A freshly
        created next-day file is read from the BEGINNING so its opening lines
        are not missed.
      - Handles the current file being truncated/rewritten.
    """
    # Wait for the first file to show up.
    path = current_file(watch_dir, pattern)
    while path is None:
        print(
            f"[processor] no file matching {pattern} in {watch_dir} yet; "
            "waiting...",
            flush=True,
        )
        time.sleep(poll_interval)
        path = current_file(watch_dir, pattern)

    print(f"[processor] opening current file: {path}", flush=True)
    f = open(path, "r")
    # First file: only care about lines appended from now on.
    f.seek(0, os.SEEK_END)

    try:
        while True:
            line = f.readline()
            if line:
                if line.endswith("\n"):
                    yield line
                else:
                    # Partial line: rewind and wait for the writer to finish it.
                    f.seek(-len(line), os.SEEK_CUR)
                    time.sleep(poll_interval)
                continue

            # readline() returned "" -> we're caught up with the current file.
            # Only now do we consider rotating, so the old file is fully drained.
            newest = current_file(watch_dir, pattern)
            if newest is not None and os.path.basename(newest) != os.path.basename(path):
                print(
                    f"[processor] rotation detected: {os.path.basename(path)} "
                    f"-> {os.path.basename(newest)}. Switching.",
                    flush=True,
                )
                f.close()
                path = newest
                f = open(path, "r")
                # New day's file: read it from the start so we don't miss
                # the first lines written before we noticed it.
                continue

            # No rotation. Handle truncation/rewrite of the current file.
            try:
                if os.path.getsize(path) < f.tell():
                    print(
                        f"[processor] {os.path.basename(path)} shrank; "
                        "seeking to start.",
                        flush=True,
                    )
                    f.seek(0, os.SEEK_SET)
            except FileNotFoundError:
                # Current file vanished; wait for any matching file to appear.
                print(
                    f"[processor] current file {path} disappeared; waiting...",
                    flush=True,
                )
                f.close()
                path = None
                while path is None:
                    time.sleep(poll_interval)
                    path = current_file(watch_dir, pattern)
                f = open(path, "r")
                continue

            time.sleep(poll_interval)
    finally:
        f.close()


def main() -> None:
    publisher = Publisher()
    publisher.connect()

    print(
        f"[processor] watching {WATCH_DIR} for {FILE_PATTERN} "
        "(Ctrl-C to stop)...",
        flush=True,
    )
    try:
        for line in follow_daily(WATCH_DIR, FILE_PATTERN, POLL_INTERVAL):
            try:
                payload = parse_to_json(line)
            except ParseError as exc:
                print(f"[processor] skipping bad line: {exc}", flush=True)
                continue
            publisher.publish(payload)
    except KeyboardInterrupt:
        print("\n[processor] stopping.", flush=True)
    finally:
        publisher.disconnect()


if __name__ == "__main__":
    main()
