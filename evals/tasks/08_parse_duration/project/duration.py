def parse_duration(text):
    """Convert a duration string to a number of seconds (int).

    Units: d (days), h (hours), m (minutes), s (seconds). Units may be combined and
    surrounded by whitespace, e.g. "1h30m" -> 5400, " 2d 4h " -> 187200, "45s" -> 45.
    Each unit may appear at most once and must be in order d, h, m, s.
    Raise ValueError for an empty string, unknown units, a missing number or unit,
    repeated units, or units out of order (e.g. "5x", "h", "10", "1m1h", "1h1h").
    """
    raise NotImplementedError
