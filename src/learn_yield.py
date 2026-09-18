#!/usr/bin/env python3
"""A hands-on tour of Python's `yield` / generators.

Run it and read the output alongside the code:

    python3 learn_yield.py

Each demo is self-contained and prints what happens step by step so you can
*see* the pause/resume behavior that makes generators different from normal
functions. The final demo mirrors the file-tailing pattern used in
processor.py's `follow()`.
"""
from __future__ import annotations

import time


def banner(title: str) -> None:
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ---------------------------------------------------------------------------
# 1. The core idea: yield pauses the function and hands back one value.
# ---------------------------------------------------------------------------
def count_up_to(n):
    """A generator: it produces 0, 1, ... n-1 one at a time.

    Notice there is no `return [list]`. Calling this does NOT run the body.
    It returns a *generator object*. The body only runs as you iterate.
    """
    i = 0
    while i < n:
        print(f"    (inside generator: about to yield {i})")
        yield i                     # hand back i, then FREEZE right here
        print(f"    (resumed after yield; i was {i})")
        i += 1


def demo_basics():
    banner("1. yield hands back one value at a time, then pauses")

    gen = count_up_to(3)
    print(f"Calling count_up_to(3) returned: {gen!r}")
    print("Nothing has run yet. Now we pull values with next():\n")

    print("next(gen) ->", next(gen))   # runs until first yield
    print("next(gen) ->", next(gen))   # resumes, runs to next yield
    print("next(gen) ->", next(gen))
    print("\nThe function's state (variable i, position in the loop) was")
    print("preserved between each next() call. That's the whole trick.")


# ---------------------------------------------------------------------------
# 2. A `for` loop is the normal way to drive a generator.
# ---------------------------------------------------------------------------
def demo_for_loop():
    banner("2. `for` drives the generator until it's exhausted")

    print("for value in count_up_to(3):")
    for value in count_up_to(3):
        print(f"  got {value}")
    print("\nWhen the generator function ends (falls off the bottom),")
    print("iteration stops automatically (StopIteration under the hood).")


# ---------------------------------------------------------------------------
# 3. Why bother? Laziness: values are produced on demand, not all up front.
# ---------------------------------------------------------------------------
def squares_list(n):
    """Eager: builds and returns the WHOLE list in memory before you use it."""
    result = []
    for i in range(n):
        result.append(i * i)
    return result


def squares_gen(n):
    """Lazy: produces one square at a time, only when asked."""
    for i in range(n):
        yield i * i


def demo_laziness():
    banner("3. Laziness: generators compute on demand")

    print("Eager list stores everything at once:")
    print("  squares_list(5) =", squares_list(5))

    print("\nLazy generator yields one at a time:")
    gen = squares_gen(5)
    print("  squares_gen(5)  =", gen, "(nothing computed yet)")
    print("  first two only  =", next(gen), next(gen))
    print("\nFor huge or infinite sequences the eager version would use too")
    print("much memory (or never finish). The generator stays cheap because")
    print("it only ever holds one value at a time.")


# ---------------------------------------------------------------------------
# 4. Infinite generators: impossible to return as a list, natural with yield.
# ---------------------------------------------------------------------------
def naturals():
    """An endless stream: 0, 1, 2, 3, ... forever. You could never return
    this as a list. With yield it's trivial and safe, because the caller
    decides when to stop pulling."""
    n = 0
    while True:
        yield n
        n += 1


def demo_infinite():
    banner("4. Infinite streams: yield makes 'never-ending' safe")

    print("Take just the first 5 from an INFINITE generator:")
    gen = naturals()
    first_five = []
    for value in gen:
        first_five.append(value)
        if len(first_five) == 5:
            break                    # WE decide when to stop
    print("  ->", first_five)
    print("\nThe generator would happily keep going forever; the consumer")
    print("controls how much of it actually runs.")


# ---------------------------------------------------------------------------
# 5. The real-world pattern: separate 'produce items' from 'handle items'.
#    This mirrors follow() in processor.py.
# ---------------------------------------------------------------------------
def read_events(events, delay=0.3):
    """Simulate a live feed. In processor.py this is follow(), reading a file
    that is being appended to. Here we just fake incoming lines with a delay.

    The generator's job: 'how do I get the next item.'
    """
    for event in events:
        time.sleep(delay)            # pretend we're waiting on I/O
        yield event                  # hand each line to the consumer as it arrives


def demo_producer_consumer():
    banner("5. Real pattern: generator produces, caller consumes")

    incoming = [
        "2026-09-14 00:00:04,79021,<<LIP-SHORT",
        "2026-09-14 00:00:34,79021,<<LIP-SHORT",
        "2026-09-14 00:01:04,79021,<<LIP-SHORT",
    ]

    print("Consumer loop (like main() calling follow()):\n")
    # The consumer only cares about 'what do I do with each item', not about
    # HOW the items are produced. That separation is why processor.py uses a
    # generator: follow() handles tailing/partial lines/rotation, and main()
    # just parses + publishes each line it receives.
    for i, line in enumerate(read_events(incoming), start=1):
        print(f"  received line {i}: {line}")
    print("\nEach line was handled the instant it 'arrived', not after")
    print("collecting them all. That's exactly the tail -f behavior.")


def main():
    demo_basics()
    demo_for_loop()
    demo_laziness()
    demo_infinite()
    demo_producer_consumer()

    banner("Recap")
    print(
        "- A function with `yield` is a GENERATOR; calling it returns a\n"
        "  generator object and runs no code yet.\n"
        "- `yield X` hands back X and FREEZES the function (locals, position,\n"
        "  open files) until the next value is requested.\n"
        "- `for` / next() drive it; it resumes right after the last yield.\n"
        "- Use it for: lazy/large/infinite sequences, streaming I/O, and\n"
        "  cleanly separating 'produce items' from 'consume items'.\n"
        "- processor.py's follow() is this exact pattern applied to a file."
    )


if __name__ == "__main__":
    main()
