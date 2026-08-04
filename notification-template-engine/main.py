from notification_service import send_notification
from notifier import ConsoleNotifier
from users import User


def main():

    users = [
        User("Vaishnavi", "vaish@gmail.com", "en"),
        User("Jaya", "jaya@gmail.com", "hi"),
        User("Anushka", "anushka@gmail.com", "te"),
    ]

    # Different notification events
    events = [
        "interview_scheduled",
        "interview_reminder",
        "interview_cancelled",
        "interview_completed",
    ]

    data = {"date": "10 July", "time": "5 PM"}
    notifier = ConsoleNotifier()

    for event in events:
        print("\n")
        print("=" * 60)
        print(f"EVENT : {event.upper()}")
        print("=" * 60)

        for user in users:
            try:
                message = send_notification(user, event, data)

                print("\n")
                print("-" * 40)

                notifier.deliver(user.email, message)

                print("-" * 40)

            except Exception as e:
                print(f"Error sending notification to {user.name}: {e}")


if __name__ == "__main__":
    main()
