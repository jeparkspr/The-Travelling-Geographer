#!/usr/bin/env python3
"""Bump the build version in build-info.json and append to CHANGELOG.md.

Usage:
    python bump-version.py "Short description of changes"
    python bump-version.py "First change" "Second change" "Third change"

Version format: YYYY.MM.DD.# where # resets to 1 each new day.
"""

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BUILD_INFO = ROOT / "frontend" / "public" / "build-info.json"
CHANGELOG = ROOT / "CHANGELOG.md"


def main():
    if len(sys.argv) < 2:
        print("Usage: python bump-version.py \"Description of changes\" [\"More changes\" ...]")
        sys.exit(1)

    descriptions = sys.argv[1:]
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    today_prefix = today.strftime("%Y.%m.%d")

    # Read current build info
    if BUILD_INFO.exists():
        with open(BUILD_INFO) as f:
            info = json.load(f)
    else:
        info = {"version": "", "date": "", "buildNumber": 0}

    # Determine build number
    if info.get("date") == today_str:
        build_num = info.get("buildNumber", 0) + 1
    else:
        build_num = 1

    version = f"{today_prefix}.{build_num}"

    # Write build-info.json
    new_info = {
        "version": version,
        "date": today_str,
        "buildNumber": build_num,
    }
    with open(BUILD_INFO, "w") as f:
        json.dump(new_info, f, indent=2)
        f.write("\n")

    # Append to CHANGELOG.md
    if not CHANGELOG.exists():
        CHANGELOG.write_text("# Changelog\n\nAll notable changes to The Travelling Geographer.\n\n---\n\n")

    existing = CHANGELOG.read_text()

    # Build the new entry
    entry_lines = [f"## {version}\n"]
    for desc in descriptions:
        entry_lines.append(f"- {desc}")
    entry_lines.append("")  # blank line after entry
    entry = "\n".join(entry_lines)

    # Insert after the --- separator (or at the end if no separator)
    marker = "---\n\n"
    if marker in existing:
        parts = existing.split(marker, 1)
        new_content = parts[0] + marker + entry + "\n" + parts[1]
    else:
        new_content = existing + "\n" + entry

    CHANGELOG.write_text(new_content)

    print(f"Version bumped to {version}")
    for desc in descriptions:
        print(f"  - {desc}")


if __name__ == "__main__":
    main()
