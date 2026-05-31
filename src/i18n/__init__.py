"""
记忆系统多语言支持与国际化
基于第一性原理：包容性、准确性、可扩展性
"""
import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class Language(Enum):
    """支持的语言"""
    ZH_CN = "zh-CN"  # 简体中文
    ZH_TW = "zh-TW"  # 繁体中文
    EN_US = "en-US"  # 英语（美国）
    EN_GB = "en-GB"  # 英语（英国）
    JA_JP = "ja-JP"  # 日语
    KO_KR = "ko-KR"  # 韩语
    FR_FR = "fr-FR"  # 法语
    DE_DE = "de-DE"  # 德语
    ES_ES = "es-ES"  # 西班牙语
    PT_BR = "pt-BR"  # 葡萄牙语（巴西）
    RU_RU = "ru-RU"  # 俄语
    AR_SA = "ar-SA"  # 阿拉伯语


@dataclass
class MemoryTranslation:
    """记忆翻译结果"""
    original_text: str
    original_language: Language
    translated_text: str
    target_language: Language
    confidence: float
    translation_method: str
    translated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TranslationCache:
    """翻译缓存"""
    translations: Dict[str, MemoryTranslation] = field(default_factory=dict)
    max_cache_size: int = 1000

    def get(self, key: str) -> Optional[MemoryTranslation]:
        """获取缓存的翻译"""
        return self.translations.get(key)

    def put(self, key: str, translation: MemoryTranslation) -> None:
        """添加翻译到缓存"""
        if len(self.translations) >= self.max_cache_size:
            # 移除最旧的条目
            oldest_key = next(iter(self.translations.keys()))
            del self.translations[oldest_key]
        self.translations[key] = translation

    def clear(self) -> None:
        """清空缓存"""
        self.translations.clear()


class LanguageDetector:
    """语言检测器"""

    # 简单的语言特征字典（实际项目中应使用更专业的库）
    _LANGUAGE_PATTERNS = {
        Language.ZH_CN: [
            r'[\u4e00-\u9fff]',  # 汉字
            r'你好|谢谢|再见',  # 常见中文词
        ],
        Language.ZH_TW: [
            r'[\u4e00-\u9fff]',
            r'你好|謝謝|再見',
        ],
        Language.EN_US: [
            r'[a-zA-Z]',
            r'the|and|is|are',
        ],
        Language.JA_JP: [
            r'[\u3040-\u30ff\u31f0-\u31ff\u4e00-\u9fff]',
            r'こんにちは|ありがとう|さようなら',
        ],
        Language.KO_KR: [
            r'[\uac00-\ud7af]',
            r'안녕하세요|감사합니다|안녕히 가세요',
        ],
        Language.FR_FR: [
            r'[a-zA-Zéèêëàâäôöùûüç]',
            r'bonjour|merci|au revoir',
        ],
    }

    _LANGUAGE_NAMES = {
        Language.ZH_CN: "简体中文",
        Language.ZH_TW: "繁体中文",
        Language.EN_US: "English (US)",
        Language.EN_GB: "English (UK)",
        Language.JA_JP: "日本語",
        Language.KO_KR: "한국어",
        Language.FR_FR: "Français",
        Language.DE_DE: "Deutsch",
        Language.ES_ES: "Español",
        Language.PT_BR: "Português",
        Language.RU_RU: "Русский",
        Language.AR_SA: "العربية",
    }

    def __init__(self):
        self._cache = TranslationCache(max_cache_size=500)

    def detect(self, text: str) -> Tuple[Language, float]:
        """检测文本语言"""
        if not text or len(text.strip()) == 0:
            return Language.EN_US, 0.5

        # 检查缓存
        cache_key = f"detect_{text[:50]}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached.original_language, cached.confidence

        scores = defaultdict(float)

        # 基于特征模式评分
        for lang, patterns in self._LANGUAGE_PATTERNS.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                if matches > 0:
                    scores[lang] += matches * 0.1

        # 字符分析
        char_scores = self._analyze_characters(text)
        for lang, score in char_scores.items():
            scores[lang] += score

        # 找出最高分的语言
        if scores:
            best_lang = max(scores.keys(), key=lambda k: scores[k])
            best_score = scores[best_lang]

            # 标准化置信度
            total_score = sum(scores.values())
            confidence = best_score / total_score if total_score > 0 else 0.5

            # 缓存结果
            dummy_translation = MemoryTranslation(
                original_text=text,
                original_language=best_lang,
                translated_text=text,
                target_language=best_lang,
                confidence=confidence,
                translation_method="detection_cache"
            )
            self._cache.put(cache_key, dummy_translation)

            return best_lang, min(confidence, 1.0)

        return Language.EN_US, 0.5

    def _analyze_characters(self, text: str) -> Dict[Language, float]:
        """分析文本字符特征"""
        scores = defaultdict(float)

        total_chars = len(text)
        if total_chars == 0:
            return scores

        # 统计汉字
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        if chinese_chars / total_chars > 0.3:
            scores[Language.ZH_CN] += 0.5
            scores[Language.ZH_TW] += 0.5

        # 统计平假名/片假名
        japanese_chars = len(re.findall(r'[\u3040-\u30ff\u31f0-\u31ff]', text))
        if japanese_chars / total_chars > 0.2:
            scores[Language.JA_JP] += 0.5

        # 统计韩语字符
        korean_chars = len(re.findall(r'[\uac00-\ud7af]', text))
        if korean_chars / total_chars > 0.2:
            scores[Language.KO_KR] += 0.5

        return scores

    def get_language_name(self, lang: Language) -> str:
        """获取语言名称"""
        return self._LANGUAGE_NAMES.get(lang, lang.value)


class SimpleTranslator:
    """简单翻译器（基础实现）"""

    # 预定义的常用翻译对
    _COMMON_TRANSLATIONS = {
        (Language.ZH_CN, Language.EN_US): {
            "你好": "Hello",
            "谢谢": "Thank you",
            "再见": "Goodbye",
            "记忆": "Memory",
            "系统": "System",
            "重要": "Important",
        },
        (Language.EN_US, Language.ZH_CN): {
            "Hello": "你好",
            "Thank you": "谢谢",
            "Goodbye": "再见",
            "Memory": "记忆",
            "System": "系统",
            "Important": "重要",
        },
        (Language.JA_JP, Language.EN_US): {
            "こんにちは": "Hello",
            "ありがとう": "Thank you",
            "さようなら": "Goodbye",
        },
    }

    def __init__(self):
        self._cache = TranslationCache()

    def translate(
        self,
        text: str,
        source_lang: Language,
        target_lang: Language
    ) -> MemoryTranslation:
        """翻译文本"""
        if source_lang == target_lang:
            return MemoryTranslation(
                original_text=text,
                original_language=source_lang,
                translated_text=text,
                target_language=target_lang,
                confidence=1.0,
                translation_method="same_language"
            )

        # 检查缓存
        cache_key = f"{source_lang.value}_{target_lang.value}_{text}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # 查找预定义翻译
        translation_pair = (source_lang, target_lang)
        if translation_pair in self._COMMON_TRANSLATIONS:
            translations = self._COMMON_TRANSLATIONS[translation_pair]
            if text in translations:
                result = MemoryTranslation(
                    original_text=text,
                    original_language=source_lang,
                    translated_text=translations[text],
                    target_language=target_lang,
                    confidence=0.8,
                    translation_method="predefined"
                )
                self._cache.put(cache_key, result)
                return result

        # 简单的词级替换翻译
        translated = self._word_level_translate(text, source_lang, target_lang)

        result = MemoryTranslation(
            original_text=text,
            original_language=source_lang,
            translated_text=translated,
            target_language=target_lang,
            confidence=0.5,
            translation_method="simple_word_level"
        )

        self._cache.put(cache_key, result)
        return result

    def _word_level_translate(
        self,
        text: str,
        source_lang: Language,
        target_lang: Language
    ) -> str:
        """词级翻译（简单实现）"""
        translation_pair = (source_lang, target_lang)
        if translation_pair not in self._COMMON_TRANSLATIONS:
            return text

        translations = self._COMMON_TRANSLATIONS[translation_pair]
        words = text.split()

        translated_words = []
        for word in words:
            # 去除标点
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word in translations:
                translated_words.append(translations[clean_word])
            else:
                translated_words.append(word)

        return ' '.join(translated_words)

    def clear_cache(self) -> None:
        """清空翻译缓存"""
        self._cache.clear()


class I18nManager:
    """国际化管理器"""

    # 默认消息字典
    _MESSAGES = {
        Language.ZH_CN: {
            "welcome": "欢迎使用记忆系统！",
            "memory_added": "记忆已成功添加。",
            "memory_not_found": "未找到指定的记忆。",
            "search_results": "搜索结果：",
            "backup_success": "备份成功！",
            "backup_failed": "备份失败。",
            "summary": "摘要：",
            "no_translation": "暂无翻译。",
            "language_detected": "检测到语言：",
            "confirm": "确认",
            "cancel": "取消",
            "save": "保存",
            "delete": "删除",
            "edit": "编辑",
            "search": "搜索",
        },
        Language.EN_US: {
            "welcome": "Welcome to the Memory System!",
            "memory_added": "Memory added successfully.",
            "memory_not_found": "Memory not found.",
            "search_results": "Search results:",
            "backup_success": "Backup successful!",
            "backup_failed": "Backup failed.",
            "summary": "Summary:",
            "no_translation": "No translation available.",
            "language_detected": "Language detected:",
            "confirm": "Confirm",
            "cancel": "Cancel",
            "save": "Save",
            "delete": "Delete",
            "edit": "Edit",
            "search": "Search",
        },
        Language.JA_JP: {
            "welcome": "メモリーシステムへようこそ！",
            "memory_added": "メモリーが正常に追加されました。",
            "memory_not_found": "指定されたメモリーが見つかりません。",
            "search_results": "検索結果：",
            "backup_success": "バックアップ成功！",
            "backup_failed": "バックアップ失敗。",
            "summary": "要約：",
            "no_translation": "翻訳はありません。",
            "language_detected": "検出された言語：",
            "confirm": "確認",
            "cancel": "キャンセル",
            "save": "保存",
            "delete": "削除",
            "edit": "編集",
            "search": "検索",
        },
    }

    def __init__(self, default_language: Language = Language.EN_US):
        self.default_language = default_language
        self.current_language = default_language
        self._language_detector = LanguageDetector()
        self._translator = SimpleTranslator()
        self._custom_messages: Dict[Language, Dict[str, str]] = defaultdict(dict)

    def set_language(self, lang: Language) -> None:
        """设置当前语言"""
        self.current_language = lang
        logger.info(f"Language set to {lang.value}")

    def gettext(self, key: str, **kwargs) -> str:
        """获取翻译消息"""
        # 尝试当前语言
        if self.current_language in self._MESSAGES:
            if key in self._MESSAGES[self.current_language]:
                text = self._MESSAGES[self.current_language][key]
                return self._format_message(text, **kwargs)

        # 尝试自定义消息
        if self.current_language in self._custom_messages:
            if key in self._custom_messages[self.current_language]:
                text = self._custom_messages[self.current_language][key]
                return self._format_message(text, **kwargs)

        # 回退到默认语言
        if self.default_language in self._MESSAGES:
            if key in self._MESSAGES[self.default_language]:
                text = self._MESSAGES[self.default_language][key]
                return self._format_message(text, **kwargs)

        # 返回键名作为最后选项
        return key

    def _format_message(self, text: str, **kwargs) -> str:
        """格式化消息字符串"""
        try:
            return text.format(**kwargs)
        except KeyError:
            return text

    def add_translation(self, lang: Language, key: str, translation: str) -> None:
        """添加自定义翻译"""
        self._custom_messages[lang][key] = translation

    def detect_language(self, text: str) -> Tuple[Language, float]:
        """检测文本语言"""
        return self._language_detector.detect(text)

    def translate(
        self,
        text: str,
        source_lang: Optional[Language] = None,
        target_lang: Optional[Language] = None
    ) -> MemoryTranslation:
        """翻译文本"""
        if target_lang is None:
            target_lang = self.current_language

        if source_lang is None:
            source_lang, _ = self._language_detector.detect(text)

        return self._translator.translate(text, source_lang, target_lang)

    def get_supported_languages(self) -> List[Language]:
        """获取支持的语言列表"""
        return list(Language)

    def get_language_name(self, lang: Language) -> str:
        """获取语言名称"""
        return self._language_detector.get_language_name(lang)

    def export_translations(self, lang: Language) -> str:
        """导出翻译为JSON"""
        all_messages = {}

        # 合并默认和自定义消息
        if lang in self._MESSAGES:
            all_messages.update(self._MESSAGES[lang])
        if lang in self._custom_messages:
            all_messages.update(self._custom_messages[lang])

        return json.dumps(all_messages, ensure_ascii=False, indent=2)


class MultilingualMemoryWrapper:
    """多语言记忆包装器"""

    def __init__(self, i18n_manager: I18nManager):
        self.i18n = i18n_manager
        self._memory_translations: Dict[str, Dict[str, MemoryTranslation]] = defaultdict(dict)

    def add_multilingual_memory(
        self,
        text: str,
        session_id: str,
        auto_translate: bool = True,
        target_languages: Optional[List[Language]] = None
    ) -> Dict[str, Any]:
        """添加多语言记忆"""
        # 检测原文语言
        detected_lang, confidence = self.i18n.detect_language(text)

        # 基础信息
        result = {
            "original_text": text,
            "original_language": detected_lang.value,
            "detection_confidence": confidence,
            "translations": {},
        }

        # 自动翻译
        if auto_translate:
            if target_languages is None:
                # 默认翻译为当前语言和英语
                target_languages = [self.i18n.current_language, Language.EN_US]

            for target_lang in target_languages:
                if target_lang != detected_lang:
                    translation = self.i18n.translate(text, detected_lang, target_lang)
                    result["translations"][target_lang.value] = {
                        "text": translation.translated_text,
                        "confidence": translation.confidence,
                        "method": translation.translation_method,
                    }
                    # 存储翻译
                    key = f"{session_id}_{len(self._memory_translations)}"
                    self._memory_translations[key][target_lang.value] = translation

        return result


# 全局单例
_global_i18n_manager: Optional[I18nManager] = None


def get_i18n_manager(default_language: Language = Language.EN_US) -> I18nManager:
    """获取国际化管理器单例"""
    global _global_i18n_manager
    if _global_i18n_manager is None:
        _global_i18n_manager = I18nManager(default_language)
    return _global_i18n_manager


def _(text: str, **kwargs) -> str:
    """便捷翻译函数"""
    manager = get_i18n_manager()
    return manager.gettext(text, **kwargs)
