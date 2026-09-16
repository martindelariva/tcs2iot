#!/usr/bin/env python3
"""Tail the test output file, parse each new line, and publish it to IoT Core.

Ties together:
    - tailing logic (follow a file, yield new lines)
    - parser.parse_to_json (raw line -> JSON)
    - iot_publisher.Publisher (JSON -> AWS IoT Core topic)

Environment:
    WATCH_FILE   File to tail (default: /data/test-out.txt)
    POLL_INTERVAL  Seconds between reads when idle (default: 0.25)
    plus all IOT_* vars consumed by iot_publisher.Publisher.
"""
from __future__ import annotations

import os
import time

from iot_publisher import Publisher
from parser import ParseError, parse_to_json

WATCH_FILE = os.getenv("WATCH_FILE", "/data/test-out.txt")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "0.25"))


def follow(path: str, poll_interval: float = 0.25):
    """Generator that yields each new line appended to `path`.

    Starts at the end of the file and handles the file not existing yet
    and truncation/rotation.
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
                    # Partial line; rewind and wait for the rest.
                    f.seek(-len(line), os.SEEK_CUR)
                    time.sleep(poll_interval)
                continue

            # No new data; check for truncation/rotation.
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


def main() -> None:
    publisher = Publisher()
    publisher.connect()

    print(f"[processor] tailing {WATCH_FILE} (Ctrl-C to stop)...", flush=True)
    try:
        for line in follow(WATCH_FILE, POLL_INTERVAL):
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
