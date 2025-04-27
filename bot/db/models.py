"""
Database models for the Telegram bot.
"""
import logging
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, SmallInteger, Boolean, Float
from sqlalchemy.orm import relationship
from bot.db.database import Base

# Get logger for this module
logger = logging.getLogger(__name__)


class Language(Base):
    """
    Language model for storing supported languages.
    """
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, nullable=False, unique=True, index=True)
    language = Column(String, nullable=False)

    def __init__(self, code, language):
        """
        Initialize a new language.

        Args:
            code: Language code (e.g., 'en', 'ru')
            language: Language name (e.g., 'English', 'Russian')
        """
        self.code = code
        self.language = language

    def __repr__(self):
        """
        String representation of the language.
        """
        return f"<Language(id={self.id}, code={self.code}, language={self.language})>"

class User(Base):
    """
    User model for storing Telegram user information.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    first_contact = Column(DateTime, default=datetime.utcnow)
    last_contact = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_premium = Column(Boolean, nullable=False, default=False)

    # Define relationship with UserSettings
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    # Access language through settings: user.settings.language

    def __init__(self, telegram_id, username=None, first_name=None, last_name=None, is_premium=False):
        """
        Initialize a new user.

        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            is_premium: Whether the user has Telegram Premium (default: False)
        """
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.is_premium = is_premium
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
        return f"<User(telegram_id={self.telegram_id}, username={self.username}, is_premium={self.is_premium})>"


class Topic(Base):
    """
    Topic model for storing content generation topics.
    """
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)

    def __init__(self, name):
        """
        Initialize a new topic.

        Args:
            name: Topic name
        """
        self.name = name

    def __repr__(self):
        """
        String representation of the topic.
        """
        return f"<Topic(id={self.id}, name={self.name})>"


class Name(Base):
    """
    Name model for storing people names for content generation.
    """
    __tablename__ = "names"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    def __init__(self, first_name, last_name):
        """
        Initialize a new name.

        Args:
            first_name: Person's first name
            last_name: Person's last name
        """
        self.first_name = first_name
        self.last_name = last_name

    def __repr__(self):
        """
        String representation of the name.
        """
        return f"<Name(id={self.id}, first_name={self.first_name}, last_name={self.last_name})>"


class Job(Base):
    """
    Job model for storing job information.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    workplace = Column(String, nullable=False)

    def __init__(self, title, workplace):
        """
        Initialize a new job.

        Args:
            title: Job title
            workplace: Workplace name
        """
        self.title = title
        self.workplace = workplace

    def __repr__(self):
        """
        String representation of the job.
        """
        return f"<Job(id={self.id}, title={self.title}, workplace={self.workplace})>"


class City(Base):
    """
    City model for storing city information.
    """
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)

    def __init__(self, name):
        """
        Initialize a new city.

        Args:
            name: City name
        """
        self.name = name

    def __repr__(self):
        """
        String representation of the city.
        """
        return f"<City(id={self.id}, name={self.name})>"


class Activity(Base):
    """
    Activity model for storing activity information.
    """
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity = Column(String, nullable=False)
    type = Column(String, nullable=False)

    def __init__(self, activity, type):
        """
        Initialize a new activity.

        Args:
            activity: Activity description
            type: Activity type
        """
        self.activity = activity
        self.type = type

    def __repr__(self):
        """
        String representation of the activity.
        """
        return f"<Activity(id={self.id}, activity={self.activity}, type={self.type})>"


class Person(Base):
    """
    Person model for storing person information.
    """
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name_id = Column(Integer, ForeignKey('names.id'), nullable=False)
    age = Column(Integer, nullable=False)
    origin = Column(Integer, ForeignKey('cities.id'), nullable=False)
    job_id = Column(Integer, ForeignKey('jobs.id'), nullable=False)
    children = Column(SmallInteger, nullable=True)
    weekend_activity = Column(String, nullable=True)
    plan_activity = Column(String, nullable=True)

    # Define relationships
    name = relationship("Name")
    city = relationship("City")
    job = relationship("Job")

    def __init__(self, name_id, age, origin, job_id, children=None, weekend_activity=None, plan_activity=None):
        """
        Initialize a new person.

        Args:
            name_id: ID of the person's name (foreign key to names table)
            age: Person's age
            origin: ID of the person's origin city (foreign key to cities table)
            job_id: ID of the person's job (foreign key to jobs table)
            children: Number of children (optional)
            weekend_activity: Weekend activity description (optional)
            plan_activity: Planned activity description (optional)
        """
        self.name_id = name_id
        self.age = age
        self.origin = origin
        self.job_id = job_id
        self.children = children
        self.weekend_activity = weekend_activity
        self.plan_activity = plan_activity

    def __repr__(self):
        """
        String representation of the person.
        """
        return f"<Person(id={self.id}, name_id={self.name_id}, age={self.age})>"


class Communication(Base):
    """
    Communication model for storing communication information.
    """
    __tablename__ = "communication"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey('topic.id'), nullable=False)
    image_url = Column(String, nullable=False)
    description = Column(String, nullable=False)

    # Define relationship
    topic = relationship("Topic")

    def __init__(self, topic_id, image_url, description):
        """
        Initialize a new communication entry.

        Args:
            topic_id: ID of the topic (foreign key to topic table)
            image_url: URL or path to the image
            description: Description of the image
        """
        self.topic_id = topic_id
        self.image_url = image_url
        self.description = description

    def __repr__(self):
        """
        String representation of the communication.
        """
        return f"<Communication(id={self.id}, topic_id={self.topic_id})>"


class AudioSpeed(Base):
    """
    AudioSpeed model for storing audio playback speed options.
    """
    __tablename__ = "audio_speeds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    speed = Column(Float, nullable=False)
    description = Column(String, nullable=True)

    def __init__(self, speed, description=None):
        """
        Initialize a new audio speed.

        Args:
            speed: Playback speed factor (e.g., 0.5, 1.0, 1.5)
            description: Description of the speed (e.g., "Slow", "Normal", "Fast")
        """
        self.speed = speed
        self.description = description

    def __repr__(self):
        """
        String representation of the audio speed.
        """
        return f"<AudioSpeed(id={self.id}, speed={self.speed}, description={self.description})>"


class LanguageLevel(Base):
    """
    LanguageLevel model for storing language proficiency levels.
    """
    __tablename__ = "language_levels"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String, nullable=False, unique=True)

    def __init__(self, level):
        """
        Initialize a new language level.

        Args:
            level: Language proficiency level (e.g., 'A1', 'B2', 'C1')
        """
        self.level = level

    def __repr__(self):
        """
        String representation of the language level.
        """
        return f"<LanguageLevel(id={self.id}, level={self.level})>"


class UserSettings(Base):
    """
    UserSettings model for storing user preferences.
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    audio_speed_id = Column(Integer, ForeignKey('audio_speeds.id'), nullable=False)
    language_id = Column(Integer, ForeignKey('languages.id'), nullable=True)
    language_level_id = Column(Integer, ForeignKey('language_levels.id'), nullable=True)

    # Define relationships
    user = relationship("User", back_populates="settings")
    audio_speed = relationship("AudioSpeed")
    language = relationship("Language")
    language_level = relationship("LanguageLevel")

    def __init__(self, user_id, audio_speed_id, language_id=None, language_level_id=None):
        """
        Initialize new user settings.

        Args:
            user_id: ID of the user (foreign key to users table)
            audio_speed_id: ID of the audio speed (foreign key to audio_speeds table)
            language_id: ID of the language (foreign key to languages table)
            language_level_id: ID of the language level (foreign key to language_levels table)
        """
        self.user_id = user_id
        self.audio_speed_id = audio_speed_id
        self.language_id = language_id
        self.language_level_id = language_level_id

    def __repr__(self):
        """
        String representation of the user settings.
        """
        return f"<UserSettings(id={self.id}, user_id={self.user_id}, audio_speed_id={self.audio_speed_id}, language_id={self.language_id})>"
