from notification_service import send_notification
from users import User


TEST_DATA = {
    "date": "10 July",
    "time": "5 PM",
}


def test_english_notification():
    user = User("Vaishnavi", "vaish@gmail.com", "en")
    message = send_notification(user, "interview_scheduled", TEST_DATA)

    assert "Hello Vaishnavi" in message


def test_hindi_notification():
    user = User("Jaya", "jaya@gmail.com", "hi")
    message = send_notification(user, "interview_scheduled", TEST_DATA)

    assert "नमस्ते Jaya" in message


def test_telugu_notification():
    user = User("Anushka", "anu@gmail.com", "te")
    message = send_notification(user, "interview_scheduled", TEST_DATA)

    assert "హలో Anushka" in message


def test_placeholder_replacement():
    user = User("Vaishnavi", "vaish@gmail.com", "en")
    message = send_notification(user, "interview_scheduled", TEST_DATA)

    assert "10 July" in message
    assert "5 PM" in message
    assert "{{name}}" not in message
    assert "{{date}}" not in message
    assert "{{time}}" not in message
