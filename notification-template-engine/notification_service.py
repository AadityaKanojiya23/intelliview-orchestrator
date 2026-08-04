import logging
import re
from html import escape

from template_loader import load_template

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def render_template(template, values):
    """
    Replaces placeholders dynamically.
    Raises an error if a required placeholder value is missing.
    """

    placeholders = re.findall(r"\{\{(.*?)\}\}", template)

    for placeholder in placeholders:
        key = placeholder.strip()

        if key not in values:
            raise ValueError(f"Missing value for placeholder '{key}'.")

        template = template.replace("{{" + key + "}}", str(values[key]))

    return template


def send_notification(user, event, data, format="txt"):
    """
    Generates and returns a localized notification message.
    Rendering is kept separate from delivery.
    """

    if user is None:
        raise ValueError("User cannot be None.")

    if not isinstance(data, dict):
        raise ValueError("Notification data must be a dictionary.")

    template = load_template(user.locale, event, format=format)

    placeholders = {
        placeholder.strip() for placeholder in re.findall(r"\{\{(.*?)\}\}", template)
    }

    required_fields = placeholders - {"name"}

    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValueError(
                f"Missing required field '{field}' "
                f"for event '{event}' while sending "
                f"notification to user '{user.name}'."
            )

    values = {"name": user.name, **data}

    if format == "html":
        values = {key: escape(str(value)) for key, value in values.items()}

    message = render_template(template, values)

    logging.info(f"Notification generated for {user.name}")

    return message
