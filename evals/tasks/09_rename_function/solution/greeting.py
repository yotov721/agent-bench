from users import get_user


def greet(user_id):
    name = get_user(user_id)  # get_user may return None
    return f"Hello, {name}!" if name else "Hello, stranger!"
