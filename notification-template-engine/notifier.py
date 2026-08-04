from abc import ABC, abstractmethod


class Notifier(ABC):
    """Abstract interface for notification delivery channels."""

    @abstractmethod
    def deliver(self, recipient, message):
        """Deliver a rendered notification message."""
        raise NotImplementedError


class ConsoleNotifier(Notifier):
    """Delivers notifications by printing them to the console."""

    def deliver(self, recipient, message):
        if not isinstance(recipient, str) or not recipient.strip():
            raise ValueError("Recipient cannot be empty.")

        if not isinstance(message, str) or not message.strip():
            raise ValueError("Message cannot be empty.")

        print(f"Notification for {recipient}")
        print(message)
