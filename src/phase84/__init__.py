class IntrusionDetector:
    def __init__(self):
        self.initialized = True
        self.phase = 84
    
    def manage(self):
        return "入侵检测功能已启用"
    
    def configure(self, **kwargs):
        return {"status": "configured", "phase": 84, **kwargs}


_instance = None

def get_intrusiondetector():
    global _instance
    if _instance is None:
        _instance = IntrusionDetector()
    return _instance
