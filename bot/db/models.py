"""
Database models for the Telegram bot.
"""
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from bot.db.database import Base

# Get logger for this module
logger = logging.getLogger(__name__)

class User(Base):
    """
    User model for storing Telegram user information.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    first_contact = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, telegram_id, username=None, first_name=None, last_name=None):
        """
        Initialize a new user.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
        """
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.first_contact = datetime.utcnow()
        self.last_contact = datetime.utcnow()

    def update_last_contact(self):
        """
        Update the last_contact timestamp.
        """
        self.last_contact = datetime.utcnow()

    def __repr__(self):
        """
        String representation of the user.
        """
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"
