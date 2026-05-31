"""
文本清理插件 - 预处理器插件示例
清理记忆内容中的多余空格和特殊字符
"""

import re
from src.plugins import (
    BasePlugin,
    PreprocessorPlugin,
    PluginInfo,
    PluginType
)


class TextCleanerPlugin(PreprocessorPlugin):
    """文本清理插件"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.remove_extra_spaces = config.get("remove_extra_spaces", True)
        self.normalize_unicode = config.get("normalize_unicode", True)
        self.custom_replacements = config.get("custom_replacements", {})
    
    def get_info(self) -> PluginInfo:
        return PluginInfo(
            plugin_id="text_cleaner",
            name="Text Cleaner",
            version="1.0.0",
            description="Cleans and normalizes text content",
            plugin_type=PluginType.PREPROCESSOR,
            author="Memory System",
            config={
                "remove_extra_spaces": True,
                "normalize_unicode": True,
                "custom_replacements": {}
            }
        )
    
    def process(self, text: str) -> str:
        """处理文本"""
        if not text:
            return text
        
        processed = text
        
        # 应用自定义替换
        for old, new in self.custom_replacements.items():
            processed = processed.replace(old, new)
        
        # 移除多余空格
        if self.remove_extra_spaces:
            processed = re.sub(r'\s+', ' ', processed)
            processed = processed.strip()
        
        return processed
    
    def execute(self, context: dict) -> any:
        """执行插件"""
        text = context.get("text", "")
        return self.process(text)
