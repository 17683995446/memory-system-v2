"""
记忆系统移动端适配模块
基于第一性原理：用户体验优先，性能优化为本
"""

import time
import json
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class DeviceType(Enum):
    """设备类型"""
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"


class Orientation(Enum):
    """屏幕方向"""
    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    UNKNOWN = "unknown"


class Breakpoint(Enum):
    """响应式断点"""
    XS = 320   # 超小屏幕
    SM = 576   # 小屏幕
    MD = 768   # 中等屏幕
    LG = 992   # 大屏幕
    XL = 1200  # 超大屏幕
    XXL = 1600 # 超超大屏幕


class GestureType(Enum):
    """手势类型"""
    TAP = "tap"
    DOUBLE_TAP = "double_tap"
    LONG_PRESS = "long_press"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    PINCH_IN = "pinch_in"
    PINCH_OUT = "pinch_out"


@dataclass
class DeviceInfo:
    """设备信息"""
    device_type: DeviceType
    orientation: Orientation
    width: int
    height: int
    pixel_ratio: float = 1.0
    is_touch: bool = True
    browser: str = ""
    os: str = ""
    supports_webgl: bool = False
    supports_service_worker: bool = False


@dataclass
class GestureEvent:
    """手势事件"""
    type: GestureType
    start_x: float
    start_y: float
    end_x: float
    end_y: float
    timestamp: float
    duration: float
    velocity: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponsiveLayout:
    """响应式布局配置"""
    name: str
    breakpoint: Breakpoint
    columns: int
    gutter: int
    margin: int
    font_size: float
    component_sizes: Dict[str, Tuple[int, int]]


class ResponsiveLayoutManager:
    """响应式布局管理器"""

    def __init__(self):
        self.current_layout: Optional[ResponsiveLayout] = None
        self.layouts: Dict[Breakpoint, ResponsiveLayout] = {}
        self._initialize_default_layouts()
        self.listeners: List[Callable] = []

    def _initialize_default_layouts(self):
        """初始化默认布局配置"""
        # 超小屏幕布局（手机竖屏）
        self.layouts[Breakpoint.XS] = ResponsiveLayout(
            name="xs",
            breakpoint=Breakpoint.XS,
            columns=4,
            gutter=8,
            margin=12,
            font_size=14.0,
            component_sizes={
                "memory_card": (1, 1),
                "toolbar": (4, 1),
                "sidebar": (0, 0),  # 隐藏
                "search_bar": (4, 1),
            }
        )

        # 小屏幕布局（手机横屏）
        self.layouts[Breakpoint.SM] = ResponsiveLayout(
            name="sm",
            breakpoint=Breakpoint.SM,
            columns=6,
            gutter=12,
            margin=16,
            font_size=15.0,
            component_sizes={
                "memory_card": (2, 1),
                "toolbar": (6, 1),
                "sidebar": (0, 0),
                "search_bar": (6, 1),
            }
        )

        # 中等屏幕布局（平板竖屏）
        self.layouts[Breakpoint.MD] = ResponsiveLayout(
            name="md",
            breakpoint=Breakpoint.MD,
            columns=8,
            gutter=16,
            margin=20,
            font_size=15.5,
            component_sizes={
                "memory_card": (2, 1),
                "toolbar": (8, 1),
                "sidebar": (2, 8),
                "search_bar": (6, 1),
            }
        )

        # 大屏幕布局（平板横屏）
        self.layouts[Breakpoint.LG] = ResponsiveLayout(
            name="lg",
            breakpoint=Breakpoint.LG,
            columns=12,
            gutter=20,
            margin=24,
            font_size=16.0,
            component_sizes={
                "memory_card": (3, 1),
                "toolbar": (12, 1),
                "sidebar": (3, 12),
                "search_bar": (8, 1),
            }
        )

        # 超大屏幕布局（桌面）
        self.layouts[Breakpoint.XL] = ResponsiveLayout(
            name="xl",
            breakpoint=Breakpoint.XL,
            columns=12,
            gutter=24,
            margin=32,
            font_size=16.5,
            component_sizes={
                "memory_card": (4, 1),
                "toolbar": (12, 1),
                "sidebar": (3, 12),
                "search_bar": (6, 1),
            }
        )

    def get_breakpoint(self, width: int) -> Breakpoint:
        """根据宽度获取断点"""
        if width < Breakpoint.XS.value:
            return Breakpoint.XS
        elif width < Breakpoint.SM.value:
            return Breakpoint.SM
        elif width < Breakpoint.MD.value:
            return Breakpoint.MD
        elif width < Breakpoint.LG.value:
            return Breakpoint.LG
        elif width < Breakpoint.XL.value:
            return Breakpoint.XL
        else:
            return Breakpoint.XXL

    def update_layout(self, width: int, height: int = 0) -> ResponsiveLayout:
        """更新布局配置"""
        breakpoint = self.get_breakpoint(width)
        new_layout = self.layouts.get(breakpoint)

        if new_layout and new_layout != self.current_layout:
            self.current_layout = new_layout
            self._notify_listeners(new_layout)

        return self.current_layout or self.layouts[Breakpoint.MD]

    def add_listener(self, callback: Callable):
        """添加布局变化监听器"""
        self.listeners.append(callback)

    def remove_listener(self, callback: Callable):
        """移除监听器"""
        if callback in self.listeners:
            self.listeners.remove(callback)

    def _notify_listeners(self, layout: ResponsiveLayout):
        """通知监听器"""
        for listener in self.listeners:
            try:
                listener(layout)
            except Exception:
                pass

    def get_css_variables(self) -> Dict[str, str]:
        """获取CSS变量"""
        if not self.current_layout:
            self.update_layout(768)

        layout = self.current_layout
        return {
            "--columns": str(layout.columns),
            "--gutter": f"{layout.gutter}px",
            "--margin": f"{layout.margin}px",
            "--font-size": f"{layout.font_size}px",
            "--breakpoint": layout.name,
        }


class TouchGestureRecognizer:
    """触摸手势识别器"""

    def __init__(self):
        self.gesture_listeners: Dict[GestureType, List[Callable]] = defaultdict(list)
        self.active_touches: Dict[int, Dict[str, float]] = {}
        self.last_tap_time: float = 0
        self.tap_threshold: float = 200  # 双击时间阈值
        self.long_press_threshold: float = 500  # 长按阈值
        self.swipe_threshold: float = 50  # 滑动阈值
        self.pinch_threshold: float = 0.1  # 捏合阈值

    def add_gesture_listener(self, gesture_type: GestureType, callback: Callable):
        """添加手势监听器"""
        self.gesture_listeners[gesture_type].append(callback)

    def remove_gesture_listener(self, gesture_type: GestureType, callback: Callable):
        """移除手势监听器"""
        if gesture_type in self.gesture_listeners:
            if callback in self.gesture_listeners[gesture_type]:
                self.gesture_listeners[gesture_type].remove(callback)

    def on_touch_start(self, touch_id: int, x: float, y: float):
        """触摸开始"""
        self.active_touches[touch_id] = {
            "start_x": x,
            "start_y": y,
            "current_x": x,
            "current_y": y,
            "start_time": time.time()
        }

    def on_touch_move(self, touch_id: int, x: float, y: float):
        """触摸移动"""
        if touch_id in self.active_touches:
            self.active_touches[touch_id]["current_x"] = x
            self.active_touches[touch_id]["current_y"] = y

    def on_touch_end(self, touch_id: int, x: float, y: float):
        """触摸结束"""
        if touch_id not in self.active_touches:
            return

        touch_data = self.active_touches.pop(touch_id)
        gesture = self._recognize_gesture(touch_data, x, y)

        if gesture:
            self._emit_gesture(gesture)

    def _recognize_gesture(self, touch_data: Dict, end_x: float, end_y: float) -> Optional[GestureEvent]:
        """识别手势"""
        start_x = touch_data["start_x"]
        start_y = touch_data["start_y"]
        start_time = touch_data["start_time"]
        duration = time.time() - start_time

        delta_x = end_x - start_x
        delta_y = end_y - start_y
        distance = (delta_x ** 2 + delta_y ** 2) ** 0.5
        velocity = distance / duration if duration > 0 else 0

        # 检测是否为点击
        if distance < self.swipe_threshold:
            current_time = time.time()
            if current_time - self.last_tap_time < self.tap_threshold:
                self.last_tap_time = current_time
                return GestureEvent(
                    type=GestureType.DOUBLE_TAP,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    timestamp=current_time,
                    duration=duration,
                    velocity=velocity
                )
            else:
                if duration > self.long_press_threshold:
                    return GestureEvent(
                        type=GestureType.LONG_PRESS,
                        start_x=start_x,
                        start_y=start_y,
                        end_x=end_x,
                        end_y=end_y,
                        timestamp=current_time,
                        duration=duration,
                        velocity=velocity
                    )
                else:
                    self.last_tap_time = current_time
                    return GestureEvent(
                        type=GestureType.TAP,
                        start_x=start_x,
                        start_y=start_y,
                        end_x=end_x,
                        end_y=end_y,
                        timestamp=current_time,
                        duration=duration,
                        velocity=velocity
                    )

        # 检测滑动方向
        if abs(delta_x) > abs(delta_y):
            if delta_x > self.swipe_threshold:
                return GestureEvent(
                    type=GestureType.SWIPE_RIGHT,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    timestamp=time.time(),
                    duration=duration,
                    velocity=velocity
                )
            elif delta_x < -self.swipe_threshold:
                return GestureEvent(
                    type=GestureType.SWIPE_LEFT,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    timestamp=time.time(),
                    duration=duration,
                    velocity=velocity
                )
        else:
            if delta_y > self.swipe_threshold:
                return GestureEvent(
                    type=GestureType.SWIPE_DOWN,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    timestamp=time.time(),
                    duration=duration,
                    velocity=velocity
                )
            elif delta_y < -self.swipe_threshold:
                return GestureEvent(
                    type=GestureType.SWIPE_UP,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                    timestamp=time.time(),
                    duration=duration,
                    velocity=velocity
                )

        return None

    def _emit_gesture(self, gesture: GestureEvent):
        """触发手势事件"""
        listeners = self.gesture_listeners.get(gesture.type, [])
        for listener in listeners:
            try:
                listener(gesture)
            except Exception:
                pass


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self):
        self.lazy_load_images = True
        self.debounce_delay = 250
        self.throttle_delay = 100
        self.max_cache_size = 100
        self.image_quality = 0.8
        self.enable_virtualization = True
        self.cache: Dict[str, Any] = {}
        self.debounce_timers: Dict[str, float] = {}

    def debounce(self, func: Callable, delay: int = None) -> Callable:
        """防抖装饰器"""
        delay = delay or self.debounce_delay

        def wrapper(*args, **kwargs):
            key = f"{func.__name__}_{args}_{kwargs}"
            current_time = time.time()

            if key in self.debounce_timers:
                last_call = self.debounce_timers[key]
                if current_time - last_call < delay / 1000:
                    return

            self.debounce_timers[key] = current_time
            return func(*args, **kwargs)

        return wrapper

    def throttle(self, func: Callable, delay: int = None) -> Callable:
        """节流装饰器"""
        delay = delay or self.throttle_delay
        last_call = {"time": 0}

        def wrapper(*args, **kwargs):
            current_time = time.time()
            if current_time - last_call["time"] >= delay / 1000:
                last_call["time"] = current_time
                return func(*args, **kwargs)

        return wrapper

    def lazy_load(self, items: List[Any], batch_size: int = 10) -> Callable:
        """懒加载生成器"""
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]

    def optimize_image(self, image_data: bytes, target_size: int = 800) -> bytes:
        """图片优化（简化版）"""
        # 这里应该是实际的图片压缩逻辑
        # 目前返回原始数据，实际应用中需要 PIL 等库
        return image_data

    def cache_result(self, key: str, value: Any):
        """缓存结果"""
        if len(self.cache) >= self.max_cache_size:
            # 简单的 FIFO 淘汰
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def get_cached(self, key: str, max_age: int = 3600) -> Optional[Any]:
        """获取缓存"""
        if key in self.cache:
            cached = self.cache[key]
            if time.time() - cached["timestamp"] < max_age:
                return cached["value"]
            else:
                del self.cache[key]
        return None


class OfflineSupport:
    """离线支持管理器"""

    def __init__(self):
        self.is_online = True
        self.pending_operations: List[Dict[str, Any]] = []
        self.cache_strategy = "cache-first"
        self.offline_listeners: List[Callable] = []
        self.online_listeners: List[Callable] = []
        self.storage = {}

    def set_online_status(self, is_online: bool):
        """设置在线状态"""
        if self.is_online != is_online:
            self.is_online = is_online
            if is_online:
                self._sync_pending_operations()
                self._notify_listeners(self.online_listeners)
            else:
                self._notify_listeners(self.offline_listeners)

    def add_offline_listener(self, callback: Callable):
        """添加离线监听器"""
        self.offline_listeners.append(callback)

    def add_online_listener(self, callback: Callable):
        """添加在线监听器"""
        self.online_listeners.append(callback)

    def queue_operation(self, operation: Dict[str, Any]):
        """队列化操作（用于离线时）"""
        if not self.is_online:
            self.pending_operations.append(operation)
        return self.is_online

    def get_pending_count(self) -> int:
        """获取待同步操作数"""
        return len(self.pending_operations)

    def _sync_pending_operations(self):
        """同步待处理操作"""
        synced = 0
        while self.pending_operations:
            operation = self.pending_operations.pop(0)
            try:
                # 这里应该是实际的同步逻辑
                synced += 1
            except Exception:
                # 同步失败，放回队列
                self.pending_operations.insert(0, operation)
                break

        return synced

    def _notify_listeners(self, listeners: List[Callable]):
        """通知监听器"""
        for listener in listeners:
            try:
                listener(self.is_online)
            except Exception:
                pass

    def save_to_local_storage(self, key: str, value: Any):
        """保存到本地存储"""
        try:
            self.storage[key] = json.dumps(value)
        except Exception:
            pass

    def load_from_local_storage(self, key: str) -> Optional[Any]:
        """从本地存储加载"""
        try:
            if key in self.storage:
                return json.loads(self.storage[key])
        except Exception:
            pass
        return None


class MobileAdaptationSystem:
    """移动端适配综合系统"""

    def __init__(self):
        self.device_info: Optional[DeviceInfo] = None
        self.responsive_layout = ResponsiveLayoutManager()
        self.gesture_recognizer = TouchGestureRecognizer()
        self.performance_optimizer = PerformanceOptimizer()
        self.offline_support = OfflineSupport()

    def detect_device(self, width: int, height: int, user_agent: str = "") -> DeviceInfo:
        """检测设备信息"""
        # 根据宽度判断设备类型
        if width < 768:
            device_type = DeviceType.MOBILE
        elif width < 1024:
            device_type = DeviceType.TABLET
        else:
            device_type = DeviceType.DESKTOP

        # 根据宽高比判断方向
        if width > height:
            orientation = Orientation.LANDSCAPE
        elif width < height:
            orientation = Orientation.PORTRAIT
        else:
            orientation = Orientation.UNKNOWN

        # 解析 User Agent
        is_touch = "touch" in user_agent.lower()
        supports_webgl = "webgl" in user_agent.lower()
        supports_service_worker = "serviceworker" in user_agent.lower()

        self.device_info = DeviceInfo(
            device_type=device_type,
            orientation=orientation,
            width=width,
            height=height,
            is_touch=is_touch,
            supports_webgl=supports_webgl,
            supports_service_worker=supports_service_worker
        )

        # 更新布局
        self.responsive_layout.update_layout(width, height)

        return self.device_info

    def get_optimized_layout(self) -> Dict[str, Any]:
        """获取优化后的布局"""
        layout = self.responsive_layout.current_layout or self.responsive_layout.update_layout(768)
        return {
            "columns": layout.columns,
            "gutter": layout.gutter,
            "margin": layout.margin,
            "fontSize": layout.font_size,
            "breakpoint": layout.name,
            "componentSizes": layout.component_sizes,
            "cssVariables": self.responsive_layout.get_css_variables()
        }

    def handle_resize(self, width: int, height: int):
        """处理窗口大小变化"""
        if self.device_info:
            self.device_info.width = width
            self.device_info.height = height
            self.device_info.orientation = Orientation.LANDSCAPE if width > height else Orientation.PORTRAIT

        self.responsive_layout.update_layout(width, height)

    def export_config(self) -> Dict[str, Any]:
        """导出配置"""
        return {
            "device": {
                "type": self.device_info.device_type.value if self.device_info else "unknown",
                "orientation": self.device_info.orientation.value if self.device_info else "unknown",
                "width": self.device_info.width if self.device_info else 0,
                "height": self.device_info.height if self.device_info else 0,
                "isTouch": self.device_info.is_touch if self.device_info else False
            },
            "layout": self.get_optimized_layout(),
            "offline": {
                "isOnline": self.offline_support.is_online,
                "pendingOperations": self.offline_support.get_pending_count()
            }
        }


# 全局单例
_global_mobile_system: Optional[MobileAdaptationSystem] = None


def get_mobile_system() -> MobileAdaptationSystem:
    """获取移动端适配系统单例"""
    global _global_mobile_system
    if _global_mobile_system is None:
        _global_mobile_system = MobileAdaptationSystem()
    return _global_mobile_system
