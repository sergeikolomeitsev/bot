# ============================================================
# AB TESTING ENGINE v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Управляет A/B экспериментами:
# - включает экспериментальные стратегии
# - оценивает их результаты
# - промоутит или откатывает стратегию
# - НЕ содержит торговой логики
# - НЕ вызывает TradingEngine
# ============================================================

from typing import Optional, Dict, Any


class ABTestingEngine:
    """
    Управление A/B тестированием стратегий.
    Состояние эксперимента:
    - активен или нет
    - метрики результата
    """

    def __init__(self, config, ai_manager, freedom_manager):
        self.cfg = config
        self.ai_manager = ai_manager
        self.freedom = freedom_manager

        self.active: bool = False
        self.metrics: Dict[str, float] = {
            "wins": 0.0,
            "losses": 0.0,
            "score": 0.0
        }

    # ------------------------------------------------------------
    # PUBLIC — START EXPERIMENT
    # ------------------------------------------------------------
    def start_experiment(self, experimental_strategy) -> None:
        """
        Активирует экспериментальную стратегию.
        """
        self.ai_manager.set_experimental(experimental_strategy)
        self.active = True
        self.metrics = {"wins": 0.0, "losses": 0.0, "score": 0.0}

    # ------------------------------------------------------------
    # PUBLIC — RECORD OUTCOME
    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # PUBLIC — RECORD OUTCOME (SAFE v9.1)
    # ------------------------------------------------------------
    def record_result(self, profit: float) -> None:
        """
        Записывает результат эксперимента.
        profit может быть None → такие случаи игнорируются.
        """

        # 1) Если прибыли нет — пропускаем
        if profit is None:
            # Можно добавить лог, если нужно:
            # print("A/B: received None pnl → ignoring")
            return

        # 2) Классическая логика win/loss
        if profit > 0:
            self.metrics["wins"] += 1
        else:
            self.metrics["losses"] += 1

        # 3) Score = wins - losses
        self.metrics["score"] = self.metrics["wins"] - self.metrics["losses"]

    # ------------------------------------------------------------
    # PUBLIC — SHOULD PROMOTE?
    # ------------------------------------------------------------
    def should_promote(self) -> bool:
        """
        Решает, стоит ли продвигать стратегию:
        - если score > threshold
        """
        threshold = 3  # в будущем вынесем в конфиг
        return self.metrics["score"] >= threshold

    # ------------------------------------------------------------
    # PUBLIC — PROMOTE EXPERIMENT
    # ------------------------------------------------------------
    def promote(self) -> None:
        """
        Продвигает экспериментальную стратегию в основную.
        """
        if not self.active:
            return

        exp = self.ai_manager.experimental_strategy
        if exp is None:
            return

        self.ai_manager.set_base_strategy(exp)
        self.ai_manager.disable_experimental()
        self.active = False

    # ------------------------------------------------------------
    # PUBLIC — ROLLBACK EXPERIMENT
    # ------------------------------------------------------------
    def rollback(self) -> None:
        """
        Откатывает экспериментальную стратегию.
        """
        self.ai_manager.disable_experimental()
        self.active = False
