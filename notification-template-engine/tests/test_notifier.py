import pytest
from notifier import ConsoleNotifier, Notifier


def test_notifier_interface_cannot_be_instantiated():
    with pytest.raises(TypeError):
        Notifier()


def test_console_notifier_delivers_message(capsys):
    notifier = ConsoleNotifier()

    notifier.deliver("alex@gmail.com", "Hello Alex")

    output = capsys.readouterr().out

    assert "alex@gmail.com" in output
    assert "Hello Alex" in output


def test_console_notifier_rejects_empty_recipient():
    notifier = ConsoleNotifier()

    with pytest.raises(ValueError, match="Recipient cannot be empty"):
        notifier.deliver("", "Hello Alex")


def test_console_notifier_rejects_empty_message():
    notifier = ConsoleNotifier()

    with pytest.raises(ValueError, match="Message cannot be empty"):
        notifier.deliver("alex@gmail.com", "")
