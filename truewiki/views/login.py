import html

from ..user_session import (
    get_user_method,
    get_user_methods,
)
from ..wrapper import wrap_page


def view(user, location: str = None) -> str:
    login_methods = []
    for method_name in get_user_methods():
        method = get_user_method(method_name)
        login_methods.append(f'<button type="submit" name="{method_name}">{method.get_description()}</button>')

    templates = {
        "login_methods": "\n".join(login_methods),
    }
    variables = {
        "display_name": user.display_name if user else "",
        "user_settings_url": user.get_settings_url() if user else "",
        "location": html.escape(location.split("|")[0]) if location else "",
    }

    return wrap_page("Login", "Login", variables, templates)
