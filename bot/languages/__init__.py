"""
Language configuration module.

This module provides a centralized way to load and access language configurations
based on the TARGET_LANGUAGE and TARGET_LANGUAGES environment variables.

TARGET_LANGUAGE: Single language code for content generation (e.g., 'is', 'de')
TARGET_LANGUAGES: Comma-separated list of languages for database seeding (e.g., 'is,de')
"""

import os
import logging
from typing import Optional, Dict, Type, List

from .base import LanguageConfig

logger = logging.getLogger(__name__)

# Registry of available language configurations
# Will be populated when language modules are imported
LANGUAGE_REGISTRY: Dict[str, Type[LanguageConfig]] = {}

# Cached configurations
_current_config: Optional[LanguageConfig] = None
_all_configs: Optional[List[LanguageConfig]] = None


def register_language(code: str):
    """
    Decorator to register a language configuration class.

    Args:
        code: ISO 639-1 language code (e.g., 'is', 'de')

    Returns:
        Decorator function
    """

    def decorator(cls: Type[LanguageConfig]):
        LANGUAGE_REGISTRY[code] = cls
        logger.debug(f"Registered language configuration: {code}")
        return cls

    return decorator


def get_language_config() -> LanguageConfig:
    """
    Get the current language configuration based on TARGET_LANGUAGE env var.

    The configuration is cached after first load for performance.

    Returns:
        LanguageConfig instance for the target language
    """
    global _current_config

    if _current_config is None:
        target_lang = os.environ.get("TARGET_LANGUAGE", "is").lower()

        # Import language modules to populate the registry
        _import_language_modules()

        if target_lang not in LANGUAGE_REGISTRY:
            available = ", ".join(LANGUAGE_REGISTRY.keys())
            logger.warning(
                f"Unknown TARGET_LANGUAGE: {target_lang}. "
                f"Available: {available}. Falling back to 'is' (Icelandic)."
            )
            target_lang = "is"

        _current_config = LANGUAGE_REGISTRY[target_lang]()
        logger.info(
            f"Loaded language configuration: {_current_config.name} "
            f"({_current_config.code})"
        )

    return _current_config


def reset_language_config():
    """
    Reset the cached language configurations.

    Useful for testing or when TARGET_LANGUAGE/TARGET_LANGUAGES changes at runtime.
    """
    global _current_config, _all_configs
    _current_config = None
    _all_configs = None
    logger.debug("Language configuration cache cleared")


def get_all_language_configs() -> List[LanguageConfig]:
    """
    Get all language configurations based on TARGET_LANGUAGES env var.

    Reads TARGET_LANGUAGES (comma-separated list) or falls back to TARGET_LANGUAGE.
    The configurations are cached after first load for performance.

    Returns:
        List of LanguageConfig instances for all target languages
    """
    global _all_configs

    if _all_configs is None:
        # First try TARGET_LANGUAGES (comma-separated list)
        target_langs_str = os.environ.get("TARGET_LANGUAGES", "")

        if target_langs_str:
            # Parse comma-separated list
            target_langs = [
                lang.strip().lower()
                for lang in target_langs_str.split(",")
                if lang.strip()
            ]
        else:
            # Fall back to single TARGET_LANGUAGE
            target_lang = os.environ.get("TARGET_LANGUAGE", "is").lower()
            target_langs = [target_lang]

        # Import language modules to populate the registry
        _import_language_modules()

        _all_configs = []
        for lang_code in target_langs:
            if lang_code in LANGUAGE_REGISTRY:
                config = LANGUAGE_REGISTRY[lang_code]()
                _all_configs.append(config)
                logger.info(
                    f"Loaded language configuration: {config.name} ({config.code})"
                )
            else:
                available = ", ".join(LANGUAGE_REGISTRY.keys())
                logger.warning(
                    f"Unknown language code: {lang_code}. "
                    f"Available: {available}. Skipping."
                )

        if not _all_configs:
            # Fallback to Icelandic if nothing loaded
            logger.warning("No valid languages found. Falling back to Icelandic.")
            _all_configs = [LANGUAGE_REGISTRY["is"]()]

    return _all_configs


def get_language_config_by_code(code: str) -> Optional[LanguageConfig]:
    """
    Get a specific language configuration by its code.

    Args:
        code: ISO 639-1 language code (e.g., 'is', 'de')

    Returns:
        LanguageConfig instance or None if not found
    """
    _import_language_modules()

    if code in LANGUAGE_REGISTRY:
        return LANGUAGE_REGISTRY[code]()
    return None


def _import_language_modules():
    """Import all language configuration modules to populate the registry."""
    # Import each language module - they will auto-register via decorator
    try:
        from . import icelandic  # noqa: F401
    except ImportError as e:
        logger.warning(f"Could not import Icelandic language module: {e}")

    try:
        from . import german  # noqa: F401
    except ImportError as e:
        logger.warning(f"Could not import German language module: {e}")


def get_available_languages() -> Dict[str, str]:
    """
    Get a dictionary of available language codes and names.

    Returns:
        Dict mapping language codes to language names
    """
    _import_language_modules()
    return {code: cls().name for code, cls in LANGUAGE_REGISTRY.items()}
