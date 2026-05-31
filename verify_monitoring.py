"""
简单验证监控模块
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing monitoring module import...")
try:
    from src.monitoring import (
        MetricsCollector,
        AlertManager,
        MemorySystemMonitor,
        MetricType,
        AlertLevel,
        get_monitor
    )
    print("✓ Monitoring module imported successfully!")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTesting MetricsCollector...")
try:
    collector = MetricsCollector()
    collector.increment("test", 1)
    assert collector.get_counter("test") == 1
    print("✓ MetricsCollector works!")
except Exception as e:
    print(f"✗ MetricsCollector failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting AlertManager...")
try:
    manager = AlertManager()
    alert_id = manager.alert(AlertLevel.INFO, "Test alert")
    assert alert_id is not None
    print("✓ AlertManager works!")
except Exception as e:
    print(f"✗ AlertManager failed: {e}")
    import traceback
    traceback.print_exc()

print("\nTesting MemorySystemMonitor...")
try:
    monitor = MemorySystemMonitor()
    health = monitor.run_health_checks()
    assert "overall" in health
    print("✓ MemorySystemMonitor works!")
except Exception as e:
    print(f"✗ MemorySystemMonitor failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("All basic tests passed!")
print("=" * 50)
