"""
第37阶段测试：记忆系统多语言支持与国际化
遵循"图难于其易，为大于其细"原则
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.i18n import (
    Language,
    LanguageDetector,
    SimpleTranslator,
    I18nManager,
    MultilingualMemoryWrapper,
    MemoryTranslation,
    get_i18n_manager,
    _
)


def test_language_detector():
    """测试语言检测器"""
    print("\n=== 测试语言检测器")

    detector = LanguageDetector()

    # 测试中文检测
    text_zh = "你好，这是一段中文文本。谢谢！"
    lang, confidence = detector.detect(text_zh)
    assert lang in [Language.ZH_CN, Language.ZH_TW]
    print(f"✓ 中文检测: {lang.value}, 置信度: {confidence:.2f}")

    # 测试英文检测
    text_en = "Hello, this is an English text. Thank you!"
    lang, confidence = detector.detect(text_en)
    assert lang == Language.EN_US
    print(f"✓ 英文检测: {lang.value}, 置信度: {confidence:.2f}")

    # 测试日文检测
    text_ja = "こんにちは、これは日本語のテキストです。ありがとう！"
    lang, confidence = detector.detect(text_ja)
    assert lang == Language.JA_JP
    print(f"✓ 日文检测: {lang.value}, 置信度: {confidence:.2f}")

    # 测试韩语检测
    text_ko = "안녕하세요, 이것은 한국어 텍스트입니다. 감사합니다!"
    lang, confidence = detector.detect(text_ko)
    assert lang == Language.KO_KR
    print(f"✓ 韩语检测: {lang.value}, 置信度: {confidence:.2f}")

    # 测试获取语言名称
    for lang in Language:
        name = detector.get_language_name(lang)
        print(f"  {lang.value}: {name}")
    print("✓ 语言名称获取正常")

    print("✓ 语言检测器测试通过")


def test_simple_translator():
    """测试简单翻译器"""
    print("\n=== 测试简单翻译器")

    translator = SimpleTranslator()

    # 测试相同语言
    result = translator.translate("Hello", Language.EN_US, Language.EN_US)
    assert result.translated_text == "Hello"
    assert result.confidence == 1.0
    print("✓ 相同语言翻译正常")

    # 测试预定义翻译（中文→英文）
    result = translator.translate("你好", Language.ZH_CN, Language.EN_US)
    assert result.translated_text == "Hello"
    print(f"✓ 中文→英文翻译: 你好 → {result.translated_text}")

    # 测试预定义翻译（英文→中文）
    result = translator.translate("Hello", Language.EN_US, Language.ZH_CN)
    assert result.translated_text == "你好"
    print(f"✓ 英文→中文翻译: Hello → {result.translated_text}")

    # 测试预定义翻译（日文→英文）
    result = translator.translate("こんにちは", Language.JA_JP, Language.EN_US)
    assert result.translated_text == "Hello"
    print(f"✓ 日文→英文翻译: こんにちは → {result.translated_text}")

    # 测试词级翻译
    result = translator.translate("Hello Memory System", Language.EN_US, Language.ZH_CN)
    print(f"✓ 词级翻译: 'Hello Memory System' → '{result.translated_text}'")

    # 测试翻译缓存
    result1 = translator.translate("你好", Language.ZH_CN, Language.EN_US)
    result2 = translator.translate("你好", Language.ZH_CN, Language.EN_US)
    assert result1.translated_text == result2.translated_text
    print("✓ 翻译缓存功能正常")

    # 测试清空缓存
    translator.clear_cache()
    print("✓ 缓存清空功能正常")

    print("✓ 简单翻译器测试通过")


def test_i18n_manager():
    """测试国际化管理器"""
    print("\n=== 测试国际化管理器")

    # 创建管理器（默认英文）
    i18n = I18nManager(default_language=Language.EN_US)

    # 测试英文消息
    assert i18n.gettext("welcome") == "Welcome to the Memory System!"
    assert i18n.gettext("memory_added") == "Memory added successfully."
    print("✓ 英文消息获取正常")

    # 切换到中文
    i18n.set_language(Language.ZH_CN)
    assert i18n.gettext("welcome") == "欢迎使用记忆系统！"
    assert i18n.gettext("memory_added") == "记忆已成功添加。"
    print("✓ 中文消息获取正常")

    # 切换到日文
    i18n.set_language(Language.JA_JP)
    assert i18n.gettext("welcome") == "メモリーシステムへようこそ！"
    print("✓ 日文消息获取正常")

    # 测试消息格式化
    i18n.set_language(Language.EN_US)
    # 添加测试消息
    i18n.add_translation(Language.EN_US, "greeting", "Hello {name}!")
    assert i18n.gettext("greeting", name="Alice") == "Hello Alice!"
    print("✓ 消息格式化正常")

    # 测试添加自定义翻译
    i18n.add_translation(Language.ZH_CN, "custom_message", "这是自定义消息")
    i18n.set_language(Language.ZH_CN)
    assert i18n.gettext("custom_message") == "这是自定义消息"
    print("✓ 自定义翻译添加正常")

    # 测试语言检测
    lang, confidence = i18n.detect_language("这是中文")
    assert lang in [Language.ZH_CN, Language.ZH_TW]
    print(f"✓ 语言检测功能正常: {lang.value}")

    # 测试翻译功能
    i18n.set_language(Language.EN_US)
    translation = i18n.translate("你好")
    assert translation.translated_text == "Hello"
    print(f"✓ 翻译功能正常: 你好 → {translation.translated_text}")

    # 测试支持的语言列表
    supported = i18n.get_supported_languages()
    assert len(supported) > 0
    print(f"✓ 支持的语言: {len(supported)} 种")

    # 测试导出翻译
    json_export = i18n.export_translations(Language.ZH_CN)
    assert "welcome" in json_export
    print("✓ 翻译导出功能正常")

    print("✓ 国际化管理器测试通过")


def test_multilingual_memory_wrapper():
    """测试多语言记忆包装器"""
    print("\n=== 测试多语言记忆包装器")

    i18n = I18nManager(default_language=Language.EN_US)
    wrapper = MultilingualMemoryWrapper(i18n)

    # 测试添加中文记忆并自动翻译
    i18n.set_language(Language.ZH_CN)
    result = wrapper.add_multilingual_memory(
        text="这是一段重要的中文记忆内容",
        session_id="test_session_001",
        auto_translate=True
    )

    assert "original_text" in result
    assert "original_language" in result
    assert "translations" in result
    print("✓ 多语言记忆添加成功")
    print(f"  原文: {result['original_text']}")
    print(f"  原文语言: {result['original_language']}")
    print(f"  翻译数量: {len(result['translations'])}")

    for lang_code, trans in result['translations'].items():
        print(f"  {lang_code}: {trans['text']} (置信度: {trans['confidence']:.2f})")

    # 测试添加英文记忆
    i18n.set_language(Language.EN_US)
    result = wrapper.add_multilingual_memory(
        text="This is an important English memory",
        session_id="test_session_002",
        auto_translate=True,
        target_languages=[Language.ZH_CN, Language.JA_JP]
    )

    assert len(result['translations']) > 0
    print(f"✓ 指定目标语言翻译成功: {len(result['translations'])} 种翻译")

    print("✓ 多语言记忆包装器测试通过")


def test_global_instances():
    """测试全局单例"""
    print("\n=== 测试全局单例")

    # 获取全局i18n管理器
    manager1 = get_i18n_manager()
    manager2 = get_i18n_manager()
    assert manager1 is manager2
    print("✓ i18n管理器单例模式正常")

    # 测试便捷翻译函数
    manager1.set_language(Language.ZH_CN)
    manager1.add_translation(Language.ZH_CN, "test_key", "测试消息")
    assert _("test_key") == "测试消息"
    print("✓ 便捷翻译函数正常")

    print("✓ 全局单例测试通过")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("第37阶段测试：记忆系统多语言支持与国际化")
    print("遵循原则：图难于其易，为大于其细")
    print("=" * 60)

    try:
        test_language_detector()
        test_simple_translator()
        test_i18n_manager()
        test_multilingual_memory_wrapper()
        test_global_instances()

        print("\n" + "=" * 60)
        print("✓ 所有第37阶段测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
