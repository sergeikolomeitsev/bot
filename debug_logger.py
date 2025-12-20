import json
import threading
from datetime import datetime

class DebugLogger:
    def __init__(self, path, max_records=10000):
        self.enabled = False
        self.log_path = path
        self.lock = threading.Lock()
        self._cache = []
        self.max_records = max_records

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def log(self, message, **kwargs):
        if not self.enabled:
            return
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
            "message": message,
            "details": kwargs
        }
        with self.lock:
            self._cache.append(entry)
            # Ограничение размера — только последние N записей
            if len(self._cache) > self.max_records:
                self._cache = self._cache[-self.max_records:]
            try:
                with open(self.log_path, "w") as f:
                    json.dump(self._cache, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[DebugLogger] Write error: {e}")

    def clear(self):
        with self.lock:
            self._cache = []
            try:
                with open(self.log_path, "w") as f:
                    json.dump([], f)
            except Exception:
                pass