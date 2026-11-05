"""Report time spent on the project from logs/activity.log and git commits.

Log line format:  YYYY-MM-DD HH:MM[:SS] <kind> [summary]
  kind: msg (a message from the user), pause, resume.
  Legacy kind "user-message" is treated as msg.

Rules:
  - Events (log entries and commits) closer than GAP_MIN minutes share a block.
  - Block time = last event - first event, with MIN_BLOCK_MIN as a floor.
  - A "pause" closes the block at that time (no floor); the next event starts
    a new block even if the gap is short.
"""
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

GAP_MIN = 60
MIN_BLOCK_MIN = 5
ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "logs" / "activity.log"


def parse_ts(text):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def read_log():
    events = []
    if not LOG.exists():
        return events
    for line in LOG.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=3)
        if len(parts) < 3:
            continue
        ts = parse_ts(" ".join(parts[:2]))
        if ts is None:
            continue
        kind = "msg" if parts[2] == "user-message" else parts[2]
        events.append((ts, kind))
    return events


def read_commits():
    out = subprocess.run(
        ["git", "log", "--date=format-local:%Y-%m-%d %H:%M:%S", "--pretty=%ad"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return [(parse_ts(l), "commit") for l in out.splitlines() if l.strip()]


def build_blocks(events):
    """Return list of (start, end) blocks."""
    blocks = []
    start = last = None
    for ts, kind in sorted(events, key=lambda e: e[0]):
        if start is not None and ts - last > timedelta(minutes=GAP_MIN):
            blocks.append((start, last)); start = None
        if kind == "pause":
            if start is not None:
                blocks.append((start, ts)); start = None
            continue
        if start is None:
            start = ts
        last = ts
    if start is not None:
        blocks.append((start, last))
    return blocks


def duration(block):
    s, e = block
    return max(e - s, timedelta(minutes=MIN_BLOCK_MIN))


def main():
    blocks = build_blocks(read_log() + read_commits())
    per_day = defaultdict(timedelta)
    for b in blocks:
        per_day[b[0].date()] += duration(b)
    per_week = defaultdict(timedelta)
    for day, d in per_day.items():
        iso = day.isocalendar()
        per_week[(iso[0], iso[1])] += d

    fmt = lambda d: f"{int(d.total_seconds() // 3600)}h{int(d.total_seconds() % 3600 // 60):02d}"
    print("Per day")
    for day in sorted(per_day):
        print(f"  {day} {fmt(per_day[day])}")
    print("Per week")
    for (y, w) in sorted(per_week):
        print(f"  {y}-W{w:02d} {fmt(per_week[(y, w)])}")
    if per_day:
        avg = sum(per_day.values(), timedelta()) / len(per_day)
        print(f"Average per active day: {fmt(avg)} ({len(per_day)} days)")
    print(f"Blocks: {len(blocks)} (gap {GAP_MIN} min, floor {MIN_BLOCK_MIN} min)")


if __name__ == "__main__":
    sys.exit(main())
