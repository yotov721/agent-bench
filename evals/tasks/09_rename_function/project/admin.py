import users
from users import get_usr as lookup


def is_admin(user_id):
    return users.get_usr(user_id) == "ada" and lookup(user_id) is not None
