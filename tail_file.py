#!/usr/bin/env python3
"""Tail a file and print every new line appended to it.

Usage:
    python3 tail_file.py [path]

Defaults to tailing data/test-out.txt if no path is given.
"""
import os
import sys
import time

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "data", "test-out.txt")


def tail(path, poll_interval=0.25):
    """Follow a file, printing each new line as it is appended.

    Starts at the end of the file so only newly appended lines are shown.
    Handles the file not existing yet and file truncation/rotation.
    """
    print(f"Tailing {path} (Ctrl-C to stop)...", flush=True)

    # Wait for the file to exist.
    while not os.path.exists(path):
        time.sleep(poll_interval)

    with open(path, "r") as f:
        # Start at the end so we only see new lines.
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                # Print without adding an extra newline; keep partial lines intact.
                print(line, end="", flush=True)
                continue

            # No new data. Detect truncation (file got smaller / rotated).
            try:
                if os.path.getsize(path) < f.tell():
                    f.seek(0, os.SEEK_SET)
            except FileNotFoundError:
                # File was removed; wait for it to reappear.
                while not os.path.exists(path):
                    time.sleep(poll_interval)
                f = open(path, "r")  # noqa: PLW2901
            time.sleep(poll_interval)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    try:
        tail(path)
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)


if __name__ == "__main__":
    main()
