# ============================================================
# AI STRATEGY MANAGER v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Отвечает за выбор активной стратегии:
# - базовая стратегия
# - экспериментальная стратегия (A/B тесты)
# - управление состоянием AI экспериментов
# Не содержит сигналов и торговой логики.
# ============================================================

from typing import Optional

class AIStrategyManager:
    """
    Менеджер стратегий ИИ:
    - хранит базовую стратегию
    - хранит экспериментальную стратегию (если активна)
    - выдает текущую активную стратегию для TradingEngine
    """

    def __init__(self, config):
        self.cfg = config

        self.base_strategy = None              # будет установлено DI
        self.experimental_strategy = None      # для A/B тестов
        self.experimental_active = False

    # ------------------------------------------------------------
    # PUBLIC — SET BASE STRATEGY
    # ------------------------------------------------------------
    def set_base_strategy(self, strategy) -> None:
        self.base_strategy = strategy

    # ------------------------------------------------------------
    # PUBLIC — SET EXPERIMENTAL STRATEGY
    # ------------------------------------------------------------
    def set_experimental(self, strategy) -> None:
        self.experimental_strategy = strategy
        self.experimental_active = True

    # ------------------------------------------------------------
    # PUBLIC — DISABLE EXPERIMENTAL STRATEGY
    # ------------------------------------------------------------
    def disable_experimental(self) -> None:
        self.experimental_active = False

    # ------------------------------------------------------------
    # PUBLIC — GET ACTIVE STRATEGY
    # ------------------------------------------------------------
    def get_active_strategy(self):
        """
        Возвращает стратегию, которая должна быть использована TradingEngine.
        """
        if self.experimental_active and self.experimental_strategy is not None:
            return self.experimental_strategy

        return self.base_strategy