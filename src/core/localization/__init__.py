from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Optional


class Language(str, Enum):
    """Supported languages for localization."""
    ENGLISH = "en_US"
    INDONESIAN = "id_ID"


# Comprehensive localization cache
_LANGUAGE_CACHE: dict[Language, dict[str, str]] = {}

DEFAULT_LANGUAGE = Language.ENGLISH

# Mapping for region-agnostic codes and backward compatibility
LANGUAGE_MAPPING = {
    "en": Language.ENGLISH,
    "id": Language.INDONESIAN,
    "en_US": Language.ENGLISH,
    "id_ID": Language.INDONESIAN,
}


def _load_translations(language: Language) -> dict[str, str]:
    """
    Load translations from JSON file for the given language.
    """
    if language in _LANGUAGE_CACHE:
        return _LANGUAGE_CACHE[language]

    try:
        # Get the path to the i18n directory relative to this file
        current_dir = Path(__file__).parent
        file_path = current_dir / "i18n" / f"{language.value}.json"

        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                translations = json.load(f)
                _LANGUAGE_CACHE[language] = translations
                return translations
    except Exception as e:
        # Fallback to empty dict on error - use stderr to avoid protocol corruption
        import sys
        print(f"Error loading localization file for {language}: {e}", file=sys.stderr)
    
    return {}


def get_message(key: str, language: Language = DEFAULT_LANGUAGE) -> str:
    """
    Get localized message for a given key.
    
    Args:
        key: Message key to look up
        language: Target language (default: English)
        
    Returns:
        Localized message string, or English fallback, or key itself if not found
    """
    # Load target language translations
    translations = _load_translations(language)
    message = translations.get(key)
    
    # Fallback to English if not found in target language
    if message is None and language != DEFAULT_LANGUAGE:
        en_translations = _load_translations(DEFAULT_LANGUAGE)
        message = en_translations.get(key)
    
    return message if message is not None else key


def get_language_from_code(code: str) -> Language:
    """
    Get Language enum from string code.
    Supports short codes like 'en', 'id' and full codes like 'en_US', 'id_ID'.
    
    Args:
        code: Language code string
        
    Returns:
        Language enum value
    """
    return LANGUAGE_MAPPING.get(code, DEFAULT_LANGUAGE)


# Convenience exports
__all__ = [
    "Language",
    "DEFAULT_LANGUAGE",
    "get_message",
    "get_language_from_code",
]
