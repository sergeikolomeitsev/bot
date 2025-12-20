# ============================================================
# TRADING ENGINE v9.4 — Real-Market Indicators + Short Support
# ------------------------------------------------------------
# ✔ Получает real-market history через DI
# ✔ Передаёт history в стратегию
# ✔ Корректно считает strength + freedom
# ✔ PnL считается только при наличии позиции
# ✔ Поддержка long и short: сигналы "long", "short", закрытие/открытие/удержание
# ============================================================


from typing import Dict, Any, Optional

class TradingEngine:
    def __init__(
        self,
        config,
        ai_manager,
        analyzer,
        portfolio,
        utils,
        freedom,
        market_data=None
    ):
        self.cfg = config
        self.ai_manager = ai_manager
        self.analyzer = analyzer
        self.portfolio = portfolio
        self.utils = utils
        self.freedom = freedom
        self.market_data = market_data  # DI injected MarketDataManager

    # ------------------------------------------------------------
    # PROCESS ONE SYMBOL (с поддержкой шортов)
    # ------------------------------------------------------------
    def process(
        self,
        snapshot: Dict[str, Any],
        symbol: str,
        history: Optional[list] = None,
        return_explanation: bool = False
    ):
        """
        Главный метод вычисления торгового решения.
        Возвращает decision, либо (decision, explanation)
        """

        # 1) Выбираем активную стратегию
        strategy = self.ai_manager.get_active_strategy()
        if strategy is None:
            explanation = "No active strategy"
            return (None, explanation) if return_explanation else None

        # 2) Получаем историю, если TradingLoop не передал её напрямую
        if history is None and self.market_data is not None:
            history = self.market_data.get_history(symbol)

        if not history or len(history) < 10:
            explanation = "History too short"
            return (None, explanation) if return_explanation else None

        # 3) Генерация сигнала
        sig = strategy.generate_signal(snapshot, symbol, history)
        if sig is None:
            explanation = "Strategy returned None"
            return (None, explanation) if return_explanation else None

        signal = sig.get("signal")
        raw_strength = float(sig.get("strength", 0.0))
        strength = raw_strength * self.freedom.get_multiplier()

        price = snapshot.get(symbol)
        # объединяем получение позиции через стратегию (ведь стратегия хранит активные трейды и работает с портфелем)
        pos = strategy.positions.get(symbol) if hasattr(strategy, "positions") else None
        action = None

        # 4) Обработка сигнала с поддержкой шорта — ВСЕГДА через методы стратегии!
        if signal == "long":
            if not pos or pos.get("side") != "long":
                if pos:
                    strategy.close_position(symbol, price)
                strategy.open_position(symbol, price, strength, "long")
                explanation = "Open LONG"
                action = "open_long"
            else:
                explanation = "Already in LONG"
                action = "hold_long"

        elif signal == "short":
            if not pos or pos.get("side") != "short":
                if pos:
                    strategy.close_position(symbol, price)
                strategy.open_position(symbol, price, strength, "short")
                explanation = "Open SHORT"
                action = "open_short"
            else:
                explanation = "Already in SHORT"
                action = "hold_short"

        elif signal == "hold":
            explanation = "Hold"
            action = "hold"

        else:
            explanation = f"Unknown signal: {signal}"
            action = "error"

        # 5) PnL (можно получить у стратегии, если нужно)
        pnl = None
        if pos and price is not None and hasattr(strategy, "get_pnl"):
            try:
                pnl = strategy.get_pnl(snapshot).get("realized", None)
            except Exception:
                pnl = None

        # 6) Decision объект
        decision = {
            "symbol": symbol,
            "signal": signal,
            "strength": strength,
            "pnl": pnl,
            "action": action
        }
        return (decision, explanation) if return_explanation else decision