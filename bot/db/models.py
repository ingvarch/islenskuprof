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


class TargetLanguage(Base):
    """
    TargetLanguage model for storing available languages for learning.
    """
    __tablename__ = "target_languages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(50), nullable=False)
    native_name = Column(String(50), nullable=False)

    def __init__(self, code, name, native_name):
        """
        Initialize a new target language.

        Args:
            code: ISO language code (e.g., 'de', 'is')
            name: Language name in English (e.g., 'German', 'Icelandic')
            native_name: Language name in native language (e.g., 'Deutsch', 'Islenska')
        """
        self.code = code
        self.name = name
        self.native_name = native_name

    def __repr__(self):
        return f"<TargetLanguage(code={self.code}, name={self.name})>"


class Topic(Base):
    """
    Topic model for storing content generation topics.
    """
    __tablename__ = "topic"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    language_code = Column(String(10), nullable=True, index=True)

    def __init__(self, name, language_code=None):
        """
        Initialize a new topic.

        Args:
            name: Topic name
            language_code: ISO language code (e.g., 'de', 'is')
        """
        self.name = name
        self.language_code = language_code

    def __repr__(self):
        """
        String representation of the topic.
        """
        return f"<Topic(id={self.id}, name={self.name}, lang={self.language_code})>"


class Name(Base):
    """
    Name model for storing people names for content generation.
    """
    __tablename__ = "names"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    language_code = Column(String(10), nullable=True, index=True)

    def __init__(self, first_name, last_name, language_code=None):
        """
        Initialize a new name.

        Args:
            first_name: Person's first name
            last_name: Person's last name
            language_code: ISO language code (e.g., 'de', 'is')
        """
        self.first_name = first_name
        self.last_name = last_name
        self.language_code = language_code

    def __repr__(self):
        """
        String representation of the name.
        """
        return f"<Name(id={self.id}, first_name={self.first_name}, last_name={self.last_name}, lang={self.language_code})>"


class Job(Base):
    """
    Job model for storing job information.
    """
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    workplace = Column(String, nullable=False)
    language_code = Column(String(10), nullable=True, index=True)

    def __init__(self, title, workplace, language_code=None):
        """
        Initialize a new job.

        Args:
            title: Job title
            workplace: Workplace name
            language_code: ISO language code (e.g., 'de', 'is')
        """
        self.title = title
        self.workplace = workplace
        self.language_code = language_code

    def __repr__(self):
        """
        String representation of the job.
        """
        return f"<Job(id={self.id}, title={self.title}, workplace={self.workplace}, lang={self.language_code})>"


class City(Base):
    """
    City model for storing city information.
    """
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    language_code = Column(String(10), nullable=True, index=True)

    def __init__(self, name, language_code=None):
        """
        Initialize a new city.

        Args:
            name: City name
            language_code: ISO language code (e.g., 'de', 'is')
        """
        self.name = name
        self.language_code = language_code

    def __repr__(self):
        """
        String representation of the city.
        """
        return f"<City(id={self.id}, name={self.name}, lang={self.language_code})>"


class Activity(Base):
    """
    Activity model for storing activity information.
    """
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    activity = Column(String, nullable=False)
    type = Column(String, nullable=False)
    language_code = Column(String(10), nullable=True, index=True)

    def __init__(self, activity, type, language_code=None):
        """
        Initialize a new activity.

        Args:
            activity: Activity description
            type: Activity type
            language_code: ISO language code (e.g., 'de', 'is')
        """
        self.activity = activity
        self.type = type
        self.language_code = language_code

    def __repr__(self):
        """
        String representation of the activity.
        """
        return f"<Activity(id={self.id}, activity={self.activity}, type={self.type}, lang={self.language_code})>"


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
    language_code = Column(String(10), nullable=True, index=True)

    # Define relationships
    name = relationship("Name")
    city = relationship("City")
    job = relationship("Job")

    def __init__(self, name_id, age, origin, job_id, children=None, weekend_activity=None, plan_activity=None, language_code=None):
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
            language_code: ISO language code (e.g., 'de', 'is')
        """
        self.name_id = name_id
        self.age = age
        self.origin = origin
        self.job_id = job_id
        self.children = children
        self.weekend_activity = weekend_activity
        self.plan_activity = plan_activity
        self.language_code = language_code

    def __repr__(self):
        """
        String representation of the person.
        """
        return f"<Person(id={self.id}, name_id={self.name_id}, age={self.age}, lang={self.language_code})>"


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
    target_language_id = Column(Integer, ForeignKey('target_languages.id'), nullable=True)
    last_section = Column(String, nullable=True)  # Can be 'listening' or 'reading'
    # VoxFX background effects: "off", "auto", or preset ID (e.g., "67841788096cecfe8b18b2d5")
    background_effects = Column(String, nullable=False, default="off")

    # Define relationships
    user = relationship("User", back_populates="settings")
    audio_speed = relationship("AudioSpeed")
    language = relationship("Language")
    language_level = relationship("LanguageLevel")
    target_language = relationship("TargetLanguage")

    def __init__(self, user_id, audio_speed_id, language_id=None, language_level_id=None, target_language_id=None, last_section=None, background_effects="off"):
        """
        Initialize new user settings.

        Args:
            user_id: ID of the user (foreign key to users table)
            audio_speed_id: ID of the audio speed (foreign key to audio_speeds table)
            language_id: ID of the UI language (foreign key to languages table)
            language_level_id: ID of the language level (foreign key to language_levels table)
            target_language_id: ID of the target language to learn (foreign key to target_languages table)
            last_section: Last section shown to the user ('listening' or 'reading')
            background_effects: VoxFX preset ("off", "auto", or preset ID)
        """
        self.user_id = user_id
        self.audio_speed_id = audio_speed_id
        self.language_id = language_id
        self.language_level_id = language_level_id
        self.target_language_id = target_language_id
        self.last_section = last_section
        self.background_effects = background_effects

    def __repr__(self):
        """
        String representation of the user settings.
        """
        return f"<UserSettings(id={self.id}, user_id={self.user_id}, target_lang={self.target_language_id})>"


# ============================================================================
# Pimsleur Method Models
# ============================================================================


class PimsleurLesson(Base):
    """
    PimsleurLesson model for storing Pimsleur-style audio lessons.
    """
    __tablename__ = "pimsleur_lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String(10), nullable=False, index=True)
    level = Column(String(5), nullable=False)  # A1, A2, B1
    lesson_number = Column(Integer, nullable=False)  # 1-30
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=False, default=1800)  # 30 min
    audio_file_path = Column(String(500), nullable=True)
    telegram_file_id = Column(String(255), nullable=True)  # Cached for fast delivery
    script_json = Column(String, nullable=False)  # JSON with segment structure
    vocabulary_json = Column(String, nullable=False)  # JSON with vocabulary list
    review_from_lessons = Column(String, nullable=True)  # JSON array of lesson IDs
    is_generated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vocabulary_items = relationship("PimsleurLessonVocabulary", back_populates="lesson")

    def __init__(self, language_code, level, lesson_number, title, script_json, vocabulary_json,
                 description=None, duration_seconds=1800, audio_file_path=None,
                 review_from_lessons=None, is_generated=False):
        self.language_code = language_code
        self.level = level
        self.lesson_number = lesson_number
        self.title = title
        self.description = description
        self.duration_seconds = duration_seconds
        self.audio_file_path = audio_file_path
        self.script_json = script_json
        self.vocabulary_json = vocabulary_json
        self.review_from_lessons = review_from_lessons
        self.is_generated = is_generated

    def __repr__(self):
        return f"<PimsleurLesson(id={self.id}, {self.level} L{self.lesson_number}: {self.title})>"


class PimsleurVocabulary(Base):
    """
    PimsleurVocabulary model for tracking vocabulary across lessons.
    """
    __tablename__ = "pimsleur_vocabulary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    language_code = Column(String(10), nullable=False, index=True)
    word_target = Column(String(255), nullable=False)  # Word in target language
    word_native = Column(String(255), nullable=False)  # Translation (e.g., English)
    phonetic = Column(String(255), nullable=True)  # Pronunciation guide
    word_type = Column(String(50), nullable=True)  # noun, verb, phrase, etc.
    cefr_level = Column(String(5), nullable=False)  # Level where introduced
    introduced_lesson_id = Column(Integer, ForeignKey('pimsleur_lessons.id', ondelete='SET NULL'), nullable=True)
    frequency_rank = Column(Integer, nullable=True)  # Common word ranking
    audio_file_path = Column(String(500), nullable=True)  # Individual word audio
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    introduced_lesson = relationship("PimsleurLesson")
    lesson_usages = relationship("PimsleurLessonVocabulary", back_populates="vocabulary")

    def __init__(self, language_code, word_target, word_native, cefr_level,
                 phonetic=None, word_type=None, introduced_lesson_id=None,
                 frequency_rank=None, audio_file_path=None):
        self.language_code = language_code
        self.word_target = word_target
        self.word_native = word_native
        self.cefr_level = cefr_level
        self.phonetic = phonetic
        self.word_type = word_type
        self.introduced_lesson_id = introduced_lesson_id
        self.frequency_rank = frequency_rank
        self.audio_file_path = audio_file_path

    def __repr__(self):
        return f"<PimsleurVocabulary({self.word_target} = {self.word_native})>"


class PimsleurLessonVocabulary(Base):
    """
    Junction table linking vocabulary to lessons with repetition schedules.
    """
    __tablename__ = "pimsleur_lesson_vocabulary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey('pimsleur_lessons.id', ondelete='CASCADE'), nullable=False)
    vocabulary_id = Column(Integer, ForeignKey('pimsleur_vocabulary.id', ondelete='CASCADE'), nullable=False)
    is_new = Column(Boolean, nullable=False, default=False)  # Introduced in this lesson
    repetition_count = Column(Integer, nullable=False, default=0)  # Times repeated
    intervals_json = Column(String, nullable=True)  # JSON array of second marks

    # Relationships
    lesson = relationship("PimsleurLesson", back_populates="vocabulary_items")
    vocabulary = relationship("PimsleurVocabulary", back_populates="lesson_usages")

    def __init__(self, lesson_id, vocabulary_id, is_new=False, repetition_count=0, intervals_json=None):
        self.lesson_id = lesson_id
        self.vocabulary_id = vocabulary_id
        self.is_new = is_new
        self.repetition_count = repetition_count
        self.intervals_json = intervals_json

    def __repr__(self):
        return f"<PimsleurLessonVocabulary(lesson={self.lesson_id}, vocab={self.vocabulary_id}, new={self.is_new})>"


class UserPimsleurProgress(Base):
    """
    Tracks user progress through Pimsleur lessons.
    """
    __tablename__ = "user_pimsleur_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    language_code = Column(String(10), nullable=False)
    level = Column(String(5), nullable=False, default='A1')
    lesson_number = Column(Integer, nullable=False, default=1)  # Current/next lesson
    completed_lessons = Column(String, nullable=True)  # JSON array of lesson IDs
    last_lesson_id = Column(Integer, ForeignKey('pimsleur_lessons.id', ondelete='SET NULL'), nullable=True)
    last_completed_at = Column(DateTime, nullable=True)
    streak_count = Column(Integer, nullable=False, default=0)
    total_time_seconds = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    last_lesson = relationship("PimsleurLesson")

    def __init__(self, user_id, language_code, level='A1', lesson_number=1):
        self.user_id = user_id
        self.language_code = language_code
        self.level = level
        self.lesson_number = lesson_number
        self.completed_lessons = '[]'  # Empty JSON array

    def __repr__(self):
        return f"<UserPimsleurProgress(user={self.user_id}, {self.level} L{self.lesson_number})>"


class PimsleurCustomLesson(Base):
    """
    User-generated custom Pimsleur lessons from provided text.
    """
    __tablename__ = "pimsleur_custom_lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    language_code = Column(String(10), nullable=False)
    title = Column(String(255), nullable=False)
    source_text = Column(String, nullable=False)  # User's original text
    script_json = Column(String, nullable=True)  # Generated script
    audio_file_path = Column(String(500), nullable=True)
    telegram_file_id = Column(String(255), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    vocabulary_json = Column(String, nullable=True)
    status = Column(String(50), nullable=False, default='pending')  # pending, generating, ready, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Wizard settings (added in migration 016)
    focus = Column(String(20), nullable=False, default='vocabulary')  # vocabulary, pronunciation, dialogue
    voice_preference = Column(String(10), nullable=False, default='both')  # female, male, both
    difficulty_level = Column(String(5), nullable=False, default='auto')  # A1, A2, B1, auto
    text_analysis_json = Column(String, nullable=True)  # Cached text analysis results
    error_message = Column(String(500), nullable=True)  # Error details for failed lessons
    generation_started_at = Column(DateTime, nullable=True)
    generation_completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User")

    def __init__(self, user_id, language_code, title, source_text,
                 focus='vocabulary', voice_preference='both', difficulty_level='auto',
                 text_analysis_json=None):
        self.user_id = user_id
        self.language_code = language_code
        self.title = title
        self.source_text = source_text
        self.status = 'pending'
        self.focus = focus
        self.voice_preference = voice_preference
        self.difficulty_level = difficulty_level
        self.text_analysis_json = text_analysis_json

    def __repr__(self):
        return f"<PimsleurCustomLesson(id={self.id}, user={self.user_id}, status={self.status})>"
