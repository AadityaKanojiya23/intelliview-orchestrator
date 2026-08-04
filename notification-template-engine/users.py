import logging

SUPPORTED_LOCALES = {"en", "hi", "te"}

logger = logging.getLogger(__name__)


class User:
    """
    Represents a user who receives notifications.
    """

    def __init__(self, name, email, locale):

        if not isinstance(name, str) or not name.strip():
            raise ValueError("User name cannot be empty.")

        if not isinstance(email, str) or "@" not in email:
            raise ValueError("Invalid email address.")

        if not isinstance(locale, str) or not locale.strip():
            raise ValueError("Locale cannot be empty.")

        self.name = name.strip()
        self.email = email.strip()

        locale = locale.strip()

        if locale not in SUPPORTED_LOCALES:
            logger.warning("Unsupported locale '%s'. Falling back to English.", locale)
            self.locale = "en"
        else:
            self.locale = locale

    def __str__(self):
        return (
            f"User("
            f"name='{self.name}', "
            f"email='{self.email}', "
            f"locale='{self.locale}')"
        )
