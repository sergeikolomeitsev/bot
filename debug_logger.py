import json
import threading

class DebugLogger:
    ENABLED = False
    LOG_PATH = "strategy_debug_log.json"
    _lock = threading.Lock()
    _cache = []

    @classmethod
    def enable(cls):
        cls.ENABLED = True

    @classmethod
    def disable(cls):
        cls.ENABLED = False

    @classmethod
    def set_path(cls, path):
        cls.LOG_PATH = path

    @classmethod
    def log(cls, message, **kwargs):
        if not cls.ENABLED:
            return
        entry = {
            "message": message,
            "details": kwargs
        }
        with cls._lock:
            cls._cache.append(entry)
            try:
                with open(cls.LOG_PATH, "w") as f:
                    json.dump(cls._cache, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[DebugLogger] Write error: {e}")

    @classmethod
    def clear(cls):
        with cls._lock:
            cls._cache = []
            try:
                with open(cls.LOG_PATH, "w") as f:
                    json.dump([], f)
            except Exception:
                pass