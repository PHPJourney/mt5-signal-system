"""
TradeMind MT5 - Internationalization (i18n) Module
Multi-language support for GUI application
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Optional


def get_resource_path(relative_path: str) -> Path:
    """
    获取资源文件的绝对路径
    支持 PyInstaller 打包后的内部资源访问
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller 打包后的临时目录
        base_path = Path(sys._MEIPASS)
    else:
        # 开发环境
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path


class I18nManager:
    """Internationalization manager for TradeMind MT5"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent.parent
        # 使用资源路径获取语言目录（支持 PyInstaller）
        self.lang_dir = get_resource_path("lang")
        self.current_language = "zh_CN"  # Default to Simplified Chinese
        self.translations: Dict[str, Dict[str, str]] = {}
        
        # Debug: Print paths
        print(f"[i18n] base_dir: {self.base_dir}")
        print(f"[i18n] lang_dir: {self.lang_dir}")
        print(f"[i18n] frozen: {getattr(sys, 'frozen', False)}")
        if getattr(sys, 'frozen', False):
            print(f"[i18n] _MEIPASS: {sys._MEIPASS}")
        
        # Load available languages
        self.available_languages = self._detect_languages()
        print(f"[i18n] Available languages: {self.available_languages}")
        
        # Load default language
        success = self.load_language(self.current_language)
        print(f"[i18n] Load language '{self.current_language}': {'SUCCESS' if success else 'FAILED'}")
        if success:
            print(f"[i18n] Loaded {len(self.translations.get(self.current_language, {}))} translation keys")
    
    def _detect_languages(self) -> Dict[str, str]:
        """Detect available language files"""
        languages = {}
        
        if not self.lang_dir.exists():
            print(f"Warning: Language directory not found: {self.lang_dir}")
            return languages
        
        # Map language codes to display names
        lang_mapping = {
            "Chinese": "zh_CN",
            "English": "en_US"
        }
        
        # Look for JSON files
        for json_file in self.lang_dir.glob("*.json"):
            lang_name = json_file.stem
            if lang_name in lang_mapping:
                languages[lang_mapping[lang_name]] = lang_name
        
        if not languages:
            print(f"Warning: No language files found in {self.lang_dir}")
        
        return languages
    
    def load_language(self, lang_code: str) -> bool:
        """Load translations for specified language"""
        if lang_code not in self.available_languages:
            print(f"Warning: Language '{lang_code}' not available")
            return False
        
        lang_file_name = self.available_languages[lang_code]
        lang_file = self.lang_dir / f"{lang_file_name}.json"
        
        # Load JSON translation file
        if lang_file.exists():
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                self.current_language = lang_code
                print(f"Loaded language: {lang_code} ({len(self.translations[lang_code])} keys)")
                return True
            except Exception as e:
                print(f"Error loading JSON language file: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"Error: Language file not found: {lang_file}")
        return False
    
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