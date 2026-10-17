import re

_UNITS = [("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]


def parse_duration(text):
    """Convert a duration string to a number of seconds (int)."""
    cleaned = re.sub(r"\s+", "", text)
    if not cleaned:
        raise ValueError("empty duration")
    match = re.fullmatch(r"(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?", cleaned)
    if not match:
        raise ValueError(f"invalid duration: {text!r}")
    return sum(int(g) * mult for g, (_, mult) in zip(match.groups(), _UNITS) if g)
