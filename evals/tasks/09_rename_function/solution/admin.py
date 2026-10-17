import users
from users import get_user as lookup


def is_admin(user_id):
    return users.get_user(user_id) == "ada" and lookup(user_id) is not None
