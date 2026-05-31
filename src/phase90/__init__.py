class AlertManager:
    def __init__(self):
        self.initialized = True
        self.phase = 90
    
    def manage(self):
        return "告警管理功能已启用"
    
    def configure(self, **kwargs):
        return {"status": "configured", "phase": 90, **kwargs}


_instance = None

def get_alertmanager():
    global _instance
    if _instance is None:
        _instance = AlertManager()
    return _instance
