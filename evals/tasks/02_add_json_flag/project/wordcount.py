import argparse


def count(text):
    return {"lines": len(text.splitlines()), "words": len(text.split()), "chars": len(text)}


def main():
    parser = argparse.ArgumentParser(description="Count lines, words and characters in a file.")
    parser.add_argument("path")
    args = parser.parse_args()
    with open(args.path) as f:
        counts = count(f.read())
    print(f"lines: {counts['lines']}")
    print(f"words: {counts['words']}")
    print(f"chars: {counts['chars']}")


if __name__ == "__main__":
    main()
