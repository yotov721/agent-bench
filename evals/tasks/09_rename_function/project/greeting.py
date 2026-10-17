from users import get_usr


def greet(user_id):
    name = get_usr(user_id)  # get_usr may return None
    return f"Hello, {name}!" if name else "Hello, stranger!"
