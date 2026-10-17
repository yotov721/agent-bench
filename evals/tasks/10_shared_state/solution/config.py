import copy

DEFAULTS = {
    "debug": False,
    "retries": 3,
    "paths": {"cache": "/tmp/cache", "logs": ["/var/log/app"]},
}


def load_config(overrides=None):
    """Return the default settings with `overrides` (a flat dict of top-level keys) applied on top."""
    config = copy.deepcopy(DEFAULTS)
    if overrides:
        config.update(copy.deepcopy(overrides))
    return config
