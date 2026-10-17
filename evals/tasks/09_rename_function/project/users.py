USERS = {1: "ada", 2: "grace", 3: "linus"}


def get_usr(user_id):
    """Look up a user by id. get_usr returns None for unknown ids."""
    return USERS.get(user_id)
