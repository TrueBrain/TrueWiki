from ..user_session import (
    get_user_method,
    get_user_methods,
)
from ..wrapper import wrap_page


def view(user) -> str:
    login_methods = []
    for method_name in get_user_methods():
        method = get_user_method(method_name)
        login_methods.append(f'<button type="submit" name="{method_name}">{method.get_description()}</button>')

    templates = {
        "login_methods": "\n".join(login_methods),
    }
    variables = {
        "display_name": user.display_name if user else "",
    }

    return wrap_page("Login", "Login", variables, templates)
