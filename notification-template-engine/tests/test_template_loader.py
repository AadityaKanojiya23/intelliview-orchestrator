from notification_service import send_notification
from users import User


TEST_DATA = {
    "date": "10 July",
    "time": "5 PM",
}


def test_unsupported_locale_falls_back_to_english():
    user = User("Alex", "alex@gmail.com", "fr")

    assert user.locale == "en"

    message = send_notification(user, "interview_scheduled", TEST_DATA)

    assert "Hello Alex" in message
