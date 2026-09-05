#!/usr/bin/env python3
"""
Directive Intent Classifier (Legacy Compatibility Wrapper)
Lightweight wrapper redirecting to extract_contract.py for unified specification extraction.
"""

import sys
import json
import argparse

# Windows console UTF-8 support
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass

from extract_contract import classify_text

classify_intent = classify_text


def main():
    parser = argparse.ArgumentParser(description="Directive Intent Classifier (Legacy Compatibility Wrapper)")
    parser.add_argument("--text", type=str, default="", help="Text to inspect")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    result = classify_text(args.text)
    if args.json:
        sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        return 0

    print("=================================================================")
    print("🔍 [Directive Intent Classification Result (Legacy Wrapper)]")
    print("=================================================================")
    print(f"• 입력 텍스트    : \"{result['text']}\"")
    print(f"• 1차 대분류     : {result['primary_intent']}")
    print(f"• 2차 소분류     : {result['sub_intent'] or 'N/A'}")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
