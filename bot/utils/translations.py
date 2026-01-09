"""
Translation utilities for the Telegram bot.
This module provides functions for translating messages based on the user's language preference.
"""

import logging
from typing import Dict, Optional

# Get logger for this module
logger = logging.getLogger(__name__)

# Dictionary of translations for different languages
# The first level key is the message ID
# The second level key is the language code
# The value is the translated message
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # Basic messages
    "welcome": {
        "en": "Hi, {first_name}! Welcome to the bot.",
        "ru": "Привет, {first_name}! Добро пожаловать в бота.",
    },
    "your_settings": {"en": "Your settings", "ru": "Ваши настройки"},
    "bot_language": {"en": "Bot Language", "ru": "Язык бота"},
    "learning_level": {"en": "Learning level", "ru": "Уровень обучения"},
    "voice_speed": {"en": "Voice speed", "ru": "Скорость голоса"},
    "target_language": {"en": "Target Language", "ru": "Изучаемый язык"},
    # Commands
    "available_commands": {"en": "Available commands", "ru": "Доступные команды"},
    "cmd_start": {
        "en": "Start interaction with the bot",
        "ru": "Начать взаимодействие с ботом",
    },
    "cmd_understanding": {
        "en": "Understanding Section (Listening and Reading)",
        "ru": "Раздел понимания (Аудирование и Чтение)",
    },
    "cmd_communication": {"en": "Communication Section", "ru": "Раздел коммуникации"},
    "cmd_settings": {"en": "Bot settings", "ru": "Настройки бота"},
    # Error messages
    "unknown_command": {
        "en": "Sorry I don't know that command. Type /start to see the list of available commands.",
        "ru": "Извините, я не знаю эту команду. Введите /start, чтобы увидеть список доступных команд.",
    },
    "error_occurred": {
        "en": "Sorry, an error occurred: {error}",
        "ru": "Извините, произошла ошибка: {error}",
    },
    # Settings messages
    "settings": {"en": "Settings:", "ru": "Настройки:"},
    "select_language": {
        "en": "Select your preferred language:",
        "ru": "Выберите предпочитаемый язык:",
    },
    "language_updated": {
        "en": "Language updated to {language}",
        "ru": "Язык изменен на {language}",
    },
    "no_languages": {"en": "No languages available", "ru": "Нет доступных языков"},
    "error_no_languages": {
        "en": "Error: No languages available. Please contact the administrator.",
        "ru": "Ошибка: Нет доступных языков. Пожалуйста, свяжитесь с администратором.",
    },
    # Audio speed settings
    "select_audio_speed": {
        "en": "Select audio playback speed:",
        "ru": "Выберите скорость воспроизведения аудио:",
    },
    "audio_speed_updated": {
        "en": "Audio speed updated to {speed}",
        "ru": "Скорость аудио изменена на {speed}",
    },
    # Language level settings
    "select_language_level": {
        "en": "Select your language proficiency level:",
        "ru": "Выберите уровень владения языком:",
    },
    "language_level_updated": {
        "en": "Language level updated to {level}",
        "ru": "Уровень языка изменен на {level}",
    },
    # Target language settings
    "select_target_language": {
        "en": "Select the language you want to learn:",
        "ru": "Выберите язык, который хотите изучать:",
    },
    "target_language_updated": {
        "en": "Target language updated to {lang_name}",
        "ru": "Изучаемый язык изменен на {lang_name}",
    },
    "error_no_target_languages": {
        "en": "Error: No target languages available. Please contact the administrator.",
        "ru": "Ошибка: Нет доступных языков для изучения. Пожалуйста, свяжитесь с администратором.",
    },
    # Section handlers messages
    "starting": {"en": "Starting...", "ru": "Запуск..."},
    "fetching_topic": {
        "en": "Fetching random topic...",
        "ru": "Получение случайной темы...",
    },
    "generating_content": {
        "en": "Generating content about {topic}...",
        "ru": "Создание контента о {topic}...",
    },
    "extracting_dialogue": {
        "en": "Extracting dialogue from content...",
        "ru": "Извлечение диалога из контента...",
    },
    "starting_audio": {
        "en": "Starting audio generation...",
        "ru": "Начало генерации аудио...",
    },
    "merging_audio": {
        "en": "Merging individual audio files...",
        "ru": "Объединение отдельных аудиофайлов...",
    },
    "fetching_person": {
        "en": "Fetching random person data...",
        "ru": "Получение данных случайного человека...",
    },
    "fetching_communication": {
        "en": "Fetching communication data...",
        "ru": "Получение данных коммуникации...",
    },
    "write_paragraph": {
        "en": "Write a short paragraph in {target_language} describing this image.",
        "ru": "Напишите короткий абзац на {target_language} языке, описывающий это изображение.",
    },
    # Processing status messages
    "already_processing": {
        "en": "I'm already processing your request. Please wait until it's completed.",
        "ru": "Я уже обрабатываю ваш запрос. Пожалуйста, подождите до его завершения.",
    },
    # Background effects settings
    "background_effects": {"en": "Background Effects", "ru": "Фоновые эффекты"},
    "select_background_effect": {
        "en": "Select background effect:",
        "ru": "Выберите фоновый эффект:",
    },
    "background_effects_updated": {
        "en": "Background effect: {status}",
        "ru": "Фоновый эффект: {status}",
    },
    "bg_effects_auto": {"en": "Auto (by CEFR level)", "ru": "Авто (по уровню CEFR)"},
    "bg_effects_off": {"en": "Off", "ru": "Выключено"},
    "bg_preset_train_station": {"en": "Train Station", "ru": "Вокзал"},
    "bg_preset_airport": {"en": "Airport Announcement", "ru": "Аэропорт"},
    "bg_preset_subway": {"en": "Subway Train Inside", "ru": "В метро"},
    "bg_preset_poor_signal": {"en": "Poor Signal", "ru": "Плохой сигнал"},
    "bg_preset_coffee_shop": {"en": "Coffee Shop", "ru": "Кофейня"},
    "bg_preset_shopping_mall": {"en": "Shopping Mall", "ru": "Торговый центр"},
    "enabled": {"en": "enabled", "ru": "включены"},
    "disabled": {"en": "disabled", "ru": "выключены"},
}


def get_flag_emoji(language_code: str) -> str:
    """
    Get the flag emoji for a language code.

    Args:
        language_code: Language code (e.g., 'en', 'ru')

    Returns:
        str: Flag emoji for the language
    """
    # Map of language codes to flag emojis
    flags = {
        "en": "🇬🇧",  # English - UK flag
        "ru": "🇷🇺",  # Russian
        "is": "🇮🇸",  # Icelandic
        "es": "🇪🇸",  # Spanish
        "fr": "🇫🇷",  # French
        "de": "🇩🇪",  # German
        "it": "🇮🇹",  # Italian
        "ja": "🇯🇵",  # Japanese
        "ko": "🇰🇷",  # Korean
        "zh": "🇨🇳",  # Chinese
        "ar": "🇸🇦",  # Arabic
        "hi": "🇮🇳",  # Hindi
        "pt": "🇵🇹",  # Portuguese
        "nl": "🇳🇱",  # Dutch
        "pl": "🇵🇱",  # Polish
        "sv": "🇸🇪",  # Swedish
        "tr": "🇹🇷",  # Turkish
        "uk": "🇺🇦",  # Ukrainian
        "vi": "🇻🇳",  # Vietnamese
        "th": "🇹🇭",  # Thai
    }

    return flags.get(
        language_code.lower(), "🌐"
    )  # Default to globe emoji if language not found


def get_translation(message_id: str, language: Optional[str] = None, **kwargs) -> str:
    """
    Get a translated message based on the user's language preference.

    Args:
        message_id: ID of the message to translate
        language: Language to translate to (e.g., 'English', 'Russian')
        **kwargs: Format parameters for the translated message

    Returns:
        str: Translated message
    """
    # Default to English if language is not provided or not found
    language_code = "en"

    # Convert language name to language code
    if language:
        language_lower = language.lower()
        if language_lower == "english":
            language_code = "en"
        elif language_lower == "russian":
            language_code = "ru"
        # Add more language mappings as needed

    # Get the translations for the message ID
    message_translations = TRANSLATIONS.get(message_id, {})

    # Get the translation for the language code, or fall back to English
    translation = message_translations.get(
        language_code, message_translations.get("en", f"[{message_id}]")
    )

    # Format the translation with the provided parameters
    try:
        return translation.format(**kwargs)
    except KeyError as e:
        logger.error(f"Missing format parameter in translation: {e}")
        return translation
    except Exception as e:
        logger.error(f"Error formatting translation: {e}")
        return translation
