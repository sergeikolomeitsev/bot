# ============================================================
# freedom_manager.py — v9.1 (add: set_ai_manager for cyclic dep)
# ------------------------------------------------------------
# FREEDOM MANAGER v9.1 — AI PRIME TRADING BOT
# Управляет уровнем свободы стратегии. Теперь поддерживает двухфазную установку ссылки на AIManager.
# ============================================================

from typing import Optional

class FreedomManager:
    """
    Менеджер уровня свободы:
    - контролирует, насколько стратегия может отклоняться от базовых параметров
    - поддерживает интеграцию с AI Strategy Manager через set_ai_manager()
    - значение freedom_level передаётся в TradingEngine
    """

    def __init__(self, config, ai_manager):
        self.cfg = config
        self.ai_manager = ai_manager
        self.freedom_level: int = 1

    def set_ai_manager(self, ai_manager):
        self.ai_manager = ai_manager

    def set_level(self, level: int) -> None:
        level = int(level)
        if level < 1:
            level = 1
        if level > 5:
            level = 5
        self.freedom_level = level

    def get_level(self) -> int:
        return self.freedom_level

    def get_multiplier(self) -> float:
        return 1.0 + (self.freedom_level - 1) * 0.25

    def apply_experimental_boost(self) -> float:
        base = self.get_multiplier()
        return base * 1.15