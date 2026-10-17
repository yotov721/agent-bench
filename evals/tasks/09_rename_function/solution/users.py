USERS = {1: "ada", 2: "grace", 3: "linus"}


def get_user(user_id):
    """Look up a user by id. get_user returns None for unknown ids."""
    return USERS.get(user_id)
