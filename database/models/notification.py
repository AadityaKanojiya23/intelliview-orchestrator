"""Notification ORM model."""

from sqlalchemy import Column, DateTime, Integer, String, Text

from database.models._base import Base, utcnow


class Notification(Base):
    """User notification"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)
    read = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, default=utcnow)

    def __repr__(self):
        return (
            f"<Notification(id={self.id}, user_id='{self.user_id}', read={self.read})>"
        )
