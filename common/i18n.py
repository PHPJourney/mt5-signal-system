"""
TradeMind MT5 - Internationalization (i18n) Module
Multi-language support for GUI application
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional


class I18nManager:
    """Internationalization manager for TradeMind MT5"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        self.lang_dir = self.base_dir / "lang"
        self.current_language = "zh_CN"  # Default to Simplified Chinese
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Load available languages
        self.available_languages = self._detect_languages()
        
        # Load default language
        self.load_language(self.current_language)
    
    def _detect_languages(self) -> Dict[str, str]:
        """Detect available language files"""
        languages = {}
        
        if not self.lang_dir.exists():
            return languages
        
        # Map language codes to display names
        lang_mapping = {
            "Chinese": "zh_CN",
            "English": "en_US"
        }
        
        for nsh_file in self.lang_dir.glob("*.nsh"):
            lang_name = nsh_file.stem
            if lang_name in lang_mapping:
                languages[lang_mapping[lang_name]] = lang_name
        
        return languages
    
    def load_language(self, lang_code: str) -> bool:
        """Load translations for specified language"""
        if lang_code not in self.available_languages:
            return False
        
        lang_file_name = self.available_languages[lang_code]
        lang_file = self.lang_dir / f"{lang_file_name}.json"
        
        # Try to load JSON translation file first
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                self.current_language = lang_code
                return True
            except Exception as e:
                print(f"Error loading JSON language file: {e}")
        
        # Fallback: Parse NSH file (simplified approach)
        nsh_file = self.lang_dir / f"{lang_file_name}.nsh"
        if nsh_file.exists():
            self._parse_nsh_file(nsh_file, lang_code)
            self.current_language = lang_code
            return True
        
        return False
    
    def _parse_nsh_file(self, nsh_file: Path, lang_code: str):
        """Parse NSH language file and extract translations"""
        translations = {}
        
        try:
            with open(nsh_file, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('LangString'):
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            key = parts[1]
                            # Extract the string value (remove quotes)
                            value = parts[3].strip('"')
                            # Handle escape sequences
                            value = value.replace('\\n', '\n')
                            value = value.replace('\\r\\n', '\n')
                            translations[key] = value
            
            self.translations[lang_code] = translations
        except Exception as e:
            print(f"Error parsing NSH file {nsh_file}: {e}")
    
    def get_text(self, key: str, default: Optional[str] = None) -> str:
        """Get translated text by key"""
        if self.current_language in self.translations:
            return self.translations[self.current_language].get(key, default or key)
        return default or key
    
    def set_language(self, lang_code: str) -> bool:
        """Set current language"""
        if self.load_language(lang_code):
            return True
        return False
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages"""
        return {
            "zh_CN": "简体中文",
            "en_US": "English"
        }


# Global i18n instance
_i18n_instance: Optional[I18nManager] = None


def get_i18n() -> I18nManager:
    """Get global i18n instance"""
    global _i18n_instance
    if _i18n_instance is None:
        _i18n_instance = I18nManager()
    return _i18n_instance


def init_i18n(base_dir: Optional[Path] = None) -> I18nManager:
    """Initialize global i18n instance"""
    global _i18n_instance
    _i18n_instance = I18nManager(base_dir)
    return _i18n_instance


def _(key: str, default: Optional[str] = None) -> str:
    """Shorthand for get_text"""
    return get_i18n().get_text(key, default)