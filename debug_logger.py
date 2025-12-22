import json
import threading
from datetime import datetime
from collections import deque
import os

class DebugLogger:
    def __init__(self, path, max_records=10000):
        self.enabled = False
        self.log_path = path
        self.lock = threading.Lock()
        self.max_records = max_records
        self._cache = deque(maxlen=max_records)
        self._load_from_file()

    def _load_from_file(self):
        """Загружает логи из файла при инициализации logger, если файл существует."""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data[-self.max_records:]:
                            self._cache.append(item)
            except Exception as e:
                print(f"[DebugLogger] Load error: {e}")

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
            try:
                # Convert deque to list for json serialization
                with open(self.log_path, "w", encoding='utf-8') as f:
                    json.dump(list(self._cache), f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[DebugLogger] Write error: {e}")

    def clear(self):
        with self.lock:
            self._cache.clear()
            try:
                with open(self.log_path, "w", encoding='utf-8') as f:
                    json.dump([], f)
            except Exception:
                pass