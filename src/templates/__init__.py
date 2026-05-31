"""
记忆模板功能模块
基于第一性原理：确定性、简洁性、可扩展性
"""

import os
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from collections import defaultdict


class MemoryTemplate:
    """记忆模板类"""

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        content_template: str = "",
        variables: Optional[List[str]] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.template_id = str(uuid.uuid4())
        self.name = name
        self.description = description or ""
        self.content_template = content_template
        self.variables = variables or []
        self.category = category or "general"
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.updated_at = time.time()
        self.usage_count = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "description": self.description,
            "content_template": self.content_template,
            "variables": self.variables,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "usage_count": self.usage_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryTemplate':
        template = cls(
            name=data["name"],
            description=data.get("description"),
            content_template=data.get("content_template", ""),
            variables=data.get("variables"),
            category=data.get("category"),
            tags=data.get("tags"),
            metadata=data.get("metadata")
        )
        template.template_id = data.get("template_id", template.template_id)
        template.created_at = data.get("created_at", time.time())
        template.updated_at = data.get("updated_at", time.time())
        template.usage_count = data.get("usage_count", 0)
        return template


class TemplateEngine:
    """模板引擎"""

    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """从模板中提取变量"""
        import re
        pattern = r'\{(\w+)\}'
        variables = re.findall(pattern, template)
        return list(set(variables))

    @staticmethod
    def render(template: str, variables: Dict[str, Any]) -> str:
        """渲染模板"""
        import re
        pattern = r'\{(\w+)\}'

        def replacer(match):
            var_name = match.group(1)
            return str(variables.get(var_name, match.group(0)))

        return re.sub(pattern, replacer, template)

    @staticmethod
    def validate(template: str, provided_vars: Dict[str, Any]) -> Dict[str, Any]:
        """验证模板变量"""
        required_vars = TemplateEngine.extract_variables(template)
        missing_vars = [v for v in required_vars if v not in provided_vars]

        return {
            "valid": len(missing_vars) == 0,
            "required": required_vars,
            "provided": list(provided_vars.keys()),
            "missing": missing_vars
        }


class MemoryTemplateManager:
    """记忆模板管理器"""

    def __init__(self, storage_path: str = "./data/templates.json"):
        self.storage_path = storage_path
        self.templates: Dict[str, MemoryTemplate] = {}

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        self._load()

    def create_template(
        self,
        name: str,
        content_template: str,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建模板"""
        if variables is None:
            variables = TemplateEngine.extract_variables(content_template)

        template = MemoryTemplate(
            name=name,
            description=description,
            content_template=content_template,
            variables=variables,
            category=category,
            tags=tags,
            metadata=metadata
        )

        self.templates[template.template_id] = template
        self._save()
        return template.template_id

    def get_template(self, template_id: str) -> Optional[MemoryTemplate]:
        """获取模板"""
        return self.templates.get(template_id)

    def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        content_template: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新模板"""
        template = self.templates.get(template_id)
        if not template:
            return False

        if name is not None:
            template.name = name
        if content_template is not None:
            template.content_template = content_template
            template.variables = TemplateEngine.extract_variables(content_template)
        if description is not None:
            template.description = description
        if category is not None:
            template.category = category
        if tags is not None:
            template.tags = tags
        if metadata is not None:
            template.metadata = metadata

        template.updated_at = time.time()
        self._save()
        return True

    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        if template_id in self.templates:
            del self.templates[template_id]
            self._save()
            return True
        return False

    def get_templates_by_category(self, category: str) -> List[MemoryTemplate]:
        """按类别获取模板"""
        return [
            t for t in self.templates.values()
            if t.category == category
        ]

    def get_templates_by_tag(self, tag: str) -> List[MemoryTemplate]:
        """按标签获取模板"""
        return [
            t for t in self.templates.values()
            if tag in t.tags
        ]

    def get_all_templates(self) -> List[MemoryTemplate]:
        """获取所有模板"""
        return list(self.templates.values())

    def search_templates(self, query: str) -> List[MemoryTemplate]:
        """搜索模板"""
        query_lower = query.lower()
        results = []

        for template in self.templates.values():
            if (query_lower in template.name.lower() or
                query_lower in template.description.lower() or
                query_lower in template.content_template.lower() or
                any(query_lower in tag.lower() for tag in template.tags)):
                results.append(template)

        return results

    def render_template(
        self,
        template_id: str,
        variables: Dict[str, Any]
    ) -> Optional[str]:
        """渲染模板"""
        template = self.templates.get(template_id)
        if not template:
            return None

        # 验证变量
        validation = TemplateEngine.validate(template.content_template, variables)
        if not validation["valid"]:
            raise ValueError(f"Missing variables: {validation['missing']}")

        # 渲染
        content = TemplateEngine.render(template.content_template, variables)

        # 更新使用统计
        template.usage_count += 1
        self._save()

        return content

    def increment_usage(self, template_id: str) -> bool:
        """增加使用计数"""
        template = self.templates.get(template_id)
        if template:
            template.usage_count += 1
            self._save()
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_templates = len(self.templates)
        total_usage = sum(t.usage_count for t in self.templates.values())

        categories = defaultdict(int)
        for t in self.templates.values():
            categories[t.category] += 1

        most_used = sorted(
            [(t.template_id, t.name, t.usage_count) for t in self.templates.values()],
            key=lambda x: x[2],
            reverse=True
        )[:10]

        return {
            "total_templates": total_templates,
            "total_usage": total_usage,
            "categories": dict(categories),
            "most_used_templates": most_used
        }

    def _save(self) -> None:
        """保存到文件"""
        data = {
            "version": "1.0",
            "saved_at": time.time(),
            "templates": {
                tid: template.to_dict()
                for tid, template in self.templates.items()
            }
        }

        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self) -> None:
        """从文件加载"""
        if not os.path.exists(self.storage_path):
            return

        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if "templates" in data:
                for tid, template_data in data["templates"].items():
                    self.templates[tid] = MemoryTemplate.from_dict(template_data)

        except Exception as e:
            print(f"加载模板数据失败: {e}")


class EnhancedMemoryWithTemplates:
    """
    增强的记忆系统（带模板功能）
    装饰器模式实现
    """

    def __init__(self, memory_system):
        self.memory_system = memory_system
        self.template_manager = MemoryTemplateManager()
        self._register_default_templates()

    def _register_default_templates(self):
        """注册默认模板"""
        default_templates = [
            {
                "name": "会议记录",
                "category": "工作",
                "content_template": """会议主题：{title}
日期：{date}
参会人员：{participants}
会议要点：
1. {point1}
2. {point2}
3. {point3}
待办事项：{action_items}""",
                "description": "标准会议记录模板",
                "tags": ["会议", "工作", "记录"]
            },
            {
                "name": "项目启动",
                "category": "工作",
                "content_template": """项目名称：{project_name}
项目经理：{manager}
开始日期：{start_date}
目标：{goal}
关键里程碑：
- {milestone1} ({date1})
- {milestone2} ({date2})
团队成员：{team_members}""",
                "description": "项目启动文档模板",
                "tags": ["项目", "工作", "启动"]
            },
            {
                "name": "学习笔记",
                "category": "学习",
                "content_template": """主题：{topic}
学习日期：{date}
关键概念：
{concepts}
我的理解：
{understanding}
实践应用：
{application}
下一步学习计划：{next_steps}""",
                "description": "个人学习笔记模板",
                "tags": ["学习", "笔记", "知识"]
            },
            {
                "name": "代码审查",
                "category": "技术",
                "content_template": """审查对象：{file_name}
审查日期：{date}
审查人：{reviewer}
代码变更：{changes}
发现的问题：
{issues}
建议：{suggestions}
审查结论：{conclusion}""",
                "description": "代码审查记录模板",
                "tags": ["代码", "审查", "技术"]
            }
        ]

        for template_data in default_templates:
            self.template_manager.create_template(
                name=template_data["name"],
                content_template=template_data["content_template"],
                description=template_data.get("description"),
                category=template_data.get("category"),
                tags=template_data.get("tags"),
                metadata=template_data.get("metadata")
            )

    def create_template(
        self,
        name: str,
        content_template: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """创建模板"""
        return self.template_manager.create_template(
            name=name,
            content_template=content_template,
            description=description,
            category=category,
            tags=tags
        )

    def use_template(
        self,
        template_id: str,
        variables: Dict[str, Any],
        task_id: str = "default",
        memory_level: Optional[str] = None
    ) -> Optional[str]:
        """使用模板创建记忆"""
        # 渲染模板
        content = self.template_manager.render_template(template_id, variables)
        if not content:
            return None

        # 创建记忆
        memory_id = self.memory_system.add(content, task_id, memory_level)

        # 更新使用统计
        self.template_manager.increment_usage(template_id)

        return memory_id

    def get_template(self, template_id: str) -> Optional[MemoryTemplate]:
        """获取模板"""
        return self.template_manager.get_template(template_id)

    def get_all_templates(self) -> List[MemoryTemplate]:
        """获取所有模板"""
        return self.template_manager.get_all_templates()

    def search_templates(self, query: str) -> List[MemoryTemplate]:
        """搜索模板"""
        return self.template_manager.search_templates(query)

    def get_template_statistics(self) -> Dict[str, Any]:
        """获取模板统计"""
        return self.template_manager.get_statistics()
