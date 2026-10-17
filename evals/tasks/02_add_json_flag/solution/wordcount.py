import argparse
import json


def count(text):
    return {"lines": len(text.splitlines()), "words": len(text.split()), "chars": len(text)}


def main():
    parser = argparse.ArgumentParser(description="Count lines, words and characters in a file.")
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true", help="print counts as JSON")
    args = parser.parse_args()
    with open(args.path) as f:
        counts = count(f.read())
    if args.json:
        print(json.dumps(counts))
        return
    print(f"lines: {counts['lines']}")
    print(f"words: {counts['words']}")
    print(f"chars: {counts['chars']}")


if __name__ == "__main__":
    main()
