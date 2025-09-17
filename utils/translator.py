"""
Translation system for Tame-the-Time application.
Provides JSON-based internationalization with fallback support.
"""

import json
import os
from typing import Dict, Any, Optional
from utils.logging import log_debug, log_error, log_info


class Translator:
    """Manages translations and language switching for the application."""
    
    def __init__(self, language: str = 'en', locales_dir: str = None):
        """
        Initialize the translator.
        
        Args:
            language: Language code (e.g., 'en', 'es', 'fr')
            locales_dir: Directory containing translation files
        """
        self.language = language
        self.fallback_language = 'en'
        
        # Determine locales directory
        if locales_dir is None:
            # Default to locales/ directory relative to project root
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            self.locales_dir = os.path.join(project_root, 'locales')
        else:
            self.locales_dir = locales_dir
        
        self.translations = {}
        self.fallback_translations = {}
        
        # Load translations
        self._load_translations()
    
    def _load_translations(self):
        """Load translation files for current and fallback languages."""
        # Load fallback language (English)
        if self.fallback_language != self.language:
            self.fallback_translations = self._load_language_file(self.fallback_language)
        
        # Load current language
        self.translations = self._load_language_file(self.language)
        
        # If current language failed to load and it's not the fallback, use fallback
        if not self.translations and self.language != self.fallback_language:
            log_error(f"Failed to load language '{self.language}', falling back to '{self.fallback_language}'")
            self.translations = self.fallback_translations.copy()
            self.language = self.fallback_language
    
    def _load_language_file(self, language: str) -> Dict[str, Any]:
        """
        Load a specific language file.
        
        Args:
            language: Language code to load
            
        Returns:
            Dictionary containing translations, empty dict if load fails
        """
        file_path = os.path.join(self.locales_dir, f"{language}.json")
        
        if not os.path.exists(file_path):
            log_debug(f"Translation file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                translations = json.load(f)
                log_info(f"Loaded translations for language: {language}")
                return translations
        except (json.JSONDecodeError, IOError) as e:
            log_error(f"Failed to load translation file {file_path}: {e}")
            return {}
    
    def t(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.
        
        Args:
            key: Translation key in dot notation (e.g., 'window.main_title')
            **kwargs: Format parameters for string formatting
            
        Returns:
            Translated string, or the key itself if translation not found
        """
        # Try to get translation from current language
        translation = self._get_nested_value(self.translations, key)
        
        # Fall back to fallback language if not found
        if translation is None and self.fallback_translations:
            translation = self._get_nested_value(self.fallback_translations, key)
        
        # If still not found, return the key itself as fallback
        if translation is None:
            log_debug(f"Translation not found for key: {key}")
            return key
        
        # Apply string formatting if parameters provided
        if kwargs:
            try:
                return translation.format(**kwargs)
            except (KeyError, ValueError) as e:
                log_error(f"Failed to format translation '{key}' with params {kwargs}: {e}")
                return translation
        
        return translation
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Optional[str]:
        """
        Get a value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to search in
            key: Dot-separated key (e.g., 'window.main_title')
            
        Returns:
            Value if found, None otherwise
        """
        keys = key.split('.')
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        
        return current if isinstance(current, str) else None
    
    def set_language(self, language: str) -> bool:
        """
        Change the current language.
        
        Args:
            language: New language code
            
        Returns:
            True if language was successfully changed, False otherwise
        """
        if language == self.language:
            return True
        
        # Try to load the new language
        new_translations = self._load_language_file(language)
        if not new_translations:
            log_error(f"Failed to change language to '{language}' - file not found or invalid")
            return False
        
        # Update current language and translations
        self.language = language
        self.translations = new_translations
        log_info(f"Language changed to: {language}")
        return True
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get list of available languages.
        
        Returns:
            Dictionary mapping language codes to display names
        """
        available = {}
        
        if not os.path.exists(self.locales_dir):
            return available
        
        try:
            for filename in os.listdir(self.locales_dir):
                if filename.endswith('.json'):
                    lang_code = filename[:-5]  # Remove .json extension
                    
                    # Try to get language display name from the file
                    lang_file = os.path.join(self.locales_dir, filename)
                    try:
                        with open(lang_file, 'r', encoding='utf-8') as f:
                            lang_data = json.load(f)
                            display_name = lang_data.get('_meta', {}).get('display_name', lang_code.upper())
                            available[lang_code] = display_name
                    except (json.JSONDecodeError, IOError):
                        # If we can't read the file, just use the code
                        available[lang_code] = lang_code.upper()
        except OSError as e:
            log_error(f"Failed to scan locales directory: {e}")
        
        return available
    
    def get_current_language(self) -> str:
        """Get the current language code."""
        return self.language


# Global translator instance
_translator = None


def init_translator(language: str = 'en', locales_dir: str = None) -> Translator:
    """
    Initialize the global translator instance.
    
    Args:
        language: Initial language code
        locales_dir: Directory containing translation files
        
    Returns:
        Translator instance
    """
    global _translator
    _translator = Translator(language, locales_dir)
    return _translator


def get_translator() -> Translator:
    """
    Get the global translator instance.
    
    Returns:
        Translator instance, creates default if not initialized
    """
    global _translator
    if _translator is None:
        _translator = Translator()
    return _translator


def t(key: str, **kwargs) -> str:
    """
    Convenience function for translation.
    
    Args:
        key: Translation key
        **kwargs: Format parameters
        
    Returns:
        Translated string
    """
    return get_translator().t(key, **kwargs)


def set_language(language: str) -> bool:
    """
    Convenience function to change language.
    
    Args:
        language: New language code
        
    Returns:
        True if successful, False otherwise
    """
    return get_translator().set_language(language)


def get_available_languages() -> Dict[str, str]:
    """
    Convenience function to get available languages.
    
    Returns:
        Dictionary mapping language codes to display names
    """
    return get_translator().get_available_languages()
