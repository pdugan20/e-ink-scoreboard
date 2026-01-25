#!/usr/bin/env python3
"""Check for emojis in files."""
import re
import sys

EMOJI_PATTERN = re.compile(
    "["
    "\U0001f300-\U0001f9ff"  # Emoticons
    "\U00002600-\U000027bf"  # Miscellaneous Symbols
    "\U0001f1e0-\U0001f1ff"  # Flags
    "✅❌⚠️📝🎉⭐🚀💡🔧📊🤖✓"  # Common emojis
    "]",
    flags=re.UNICODE,
)


def check_file(filename):
    """Check a single file for emojis."""
    try:
        with open(filename, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if EMOJI_PATTERN.search(line):
                    print(f"{filename}:{i}: Found emoji in line: {line.strip()}")
                    return False
    except UnicodeDecodeError:
        # Skip binary files
        return True
    return True


def main():
    files = sys.argv[1:]
    failed = []
    for filename in files:
        if not check_file(filename):
            failed.append(filename)

    if failed:
        print("\nEmojis found in files. Please use plain text alternatives:")
        print("  ✅ → [DONE] or 'Success' or just remove")
        print("  ❌ → [FAIL] or 'Error' or just remove")
        print("  ⚠️ → [WARN] or 'Warning' or just remove")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
