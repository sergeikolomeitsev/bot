# ============================================================
# FREEDOM MANAGER v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Управляет уровнем свободы стратегии:
# - регулирует агрессивность сигналов
# - взаимодействует с AI Strategy Manager
# - не содержит торговой логики
# - не изменяет портфель
# - SRP-чистый модуль
# ============================================================

from typing import Optional

class FreedomManager:
    """
    Менеджер уровня свободы:
    - контролирует, насколько стратегия может отклоняться
      от базовых параметров
    - поддерживает интеграцию с AI Strategy Manager
    - значение freedom_level передаётся в TradingEngine
    """

    def __init__(self, config, ai_manager):
        self.cfg = config
        self.ai_manager = ai_manager

        # Уровень свободы: 1..5
        self.freedom_level: int = 1

    # ------------------------------------------------------------
    # PUBLIC — SET FREEDOM LEVEL
    # ------------------------------------------------------------
    def set_level(self, level: int) -> None:
        """
        Устанавливает уровень свободы (1–5).
        """
        level = int(level)
        if level < 1:
            level = 1
        if level > 5:
            level = 5

        self.freedom_level = level

    # ------------------------------------------------------------
    # PUBLIC — GET FREEDOM LEVEL
    # ------------------------------------------------------------
    def get_level(self) -> int:
        return self.freedom_level

    # ------------------------------------------------------------
    # PUBLIC — FREEDOM MULTIPLIER
    # ------------------------------------------------------------
    def get_multiplier(self) -> float:
        """
        Возвращает множитель агрессивности стратегии.
        Используется TradingEngine.
        """
        return 1.0 + (self.freedom_level - 1) * 0.25

    # ------------------------------------------------------------
    # PUBLIC — EXPERIMENT BOOST
    # ------------------------------------------------------------
    def apply_experimental_boost(self) -> float:
        """
        Возвращает усиленный множитель для экспериментальной стратегии.
        """
        base = self.get_multiplier()
        return base * 1.15