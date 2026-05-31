class RoleManager:
    def __init__(self):
        self.initialized = True
        self.phase = 77
    
    def manage(self):
        return "角色管理功能已启用"
    
    def configure(self, **kwargs):
        return {"status": "configured", "phase": 77, **kwargs}


_instance = None

def get_rolemanager():
    global _instance
    if _instance is None:
        _instance = RoleManager()
    return _instance
