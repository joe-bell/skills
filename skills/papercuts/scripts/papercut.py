#!/usr/bin/env python3
"""Append one papercut to the current repository's friction log.

Usage:
    python3 papercut.py "what got in the way" [--category C] [--file PATH]
    python3 papercut.py --status

Writes one JSON object per line to .papercuts/<branch>.jsonl at the
repository root. One file per branch keeps parallel worktrees from
conflicting. The script never creates .papercuts/: a repository opts in by
having the directory (see SKILL.md, section 1).
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

LOG_DIR = ".papercuts"


def git(*args):
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def log_name():
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch:
        branch = "detached-" + (git("rev-parse", "--short", "HEAD") or "unknown")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", branch).strip("-.")
    return (slug or "unknown") + ".jsonl"


def mode(root):
    """Return 'shared', 'local' or None for the repository at root."""
    if not os.path.isdir(os.path.join(root, LOG_DIR)):
        return None
    probe = os.path.join(LOG_DIR, log_name())
    ignored = subprocess.run(
        ["git", "-C", root, "check-ignore", "-q", probe], check=False
    ).returncode == 0
    return "local" if ignored else "shared"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("note", nargs="?", help="one line: what got in the way")
    parser.add_argument("--category", help="e.g. docs, tooling, tests, agent-config")
    parser.add_argument("--file", help="repo-relative path the papercut is about")
    parser.add_argument(
        "--status", action="store_true", help="say whether logging is on here"
    )
    args = parser.parse_args()

    root = git("rev-parse", "--show-toplevel")
    if not root:
        sys.exit("papercut: not inside a git repository")
    state = mode(root)

    if args.status:
        if state is None:
            print(f"off: no {LOG_DIR}/ directory in {root}")
        else:
            path = os.path.join(root, LOG_DIR, log_name())
            print(f"{state}: logging to {path}")
        return

    note = " ".join((args.note or "").split())
    if not note:
        parser.error("a note is required")
    if state is None:
        sys.exit(f"papercut: logging is off here (no {LOG_DIR}/ directory)")

    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "note": note,
    }
    if args.category:
        entry["category"] = args.category
    if args.file:
        entry["file"] = args.file
    agent = os.environ.get("PAPERCUT_AGENT")
    if agent:
        entry["agent"] = agent

    path = os.path.join(root, LOG_DIR, log_name())
    with open(path, "a", encoding="utf-8") as log:
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
        log.write(line + "\n")
    print(f"logged ({state}): {os.path.relpath(path, root)}")


if __name__ == "__main__":
    main()
