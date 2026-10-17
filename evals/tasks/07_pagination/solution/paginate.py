def total_pages(count, per_page):
    """Number of pages needed for `count` items (0 items -> 0 pages)."""
    return -(-count // per_page)


def paginate(items, page, per_page):
    """Items on 1-based `page`. Pages past the end give an empty list; page < 1 raises ValueError."""
    if page < 1:
        raise ValueError("page must be >= 1")
    start = (page - 1) * per_page
    return items[start : start + per_page]
