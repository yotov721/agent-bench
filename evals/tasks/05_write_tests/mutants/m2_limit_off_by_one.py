import re


def slugify(text):
    """Lowercase, replace runs of non-alphanumerics with single '-', strip leading/trailing '-'."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def truncate(text, limit, suffix="..."):
    """Return text unchanged if len(text) < limit, else cut so the result (with suffix) is exactly `limit` chars."""
    if len(text) < limit:
        return text
    return text[: limit - len(suffix)] + suffix


def wrap_words(text, width):
    """Greedy word wrap: return a list of lines, each at most `width` chars (a longer single word gets its own line)."""
    lines, current = [], ""
    for word in text.split():
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines
