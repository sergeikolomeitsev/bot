# ============================================================
# TRADING ENGINE v9.2 — Real-Market Indicators (FIXED)
# ------------------------------------------------------------
# ✔ Получает real-market history через DI
# ✔ Передаёт history в стратегию
# ✔ Корректно считает strength + freedom
# ✔ PnL считается только при наличии позиции
# ✔ Возвращает decision + optional explanation
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
    # PROCESS ONE SYMBOL
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

        raw_strength = float(sig.get("strength", 0.0))
        strength = raw_strength * self.freedom.get_multiplier()

        # 4) PnL
        price = snapshot.get(symbol)
        pos = self.portfolio.get_position(symbol)

        pnl = None
        if pos and price is not None:
            try:
                pnl = self.portfolio.calc_pnl(symbol, float(price))
            except Exception:
                pnl = None

        # 5) Decision object
        decision = {
            "symbol": symbol,
            "signal": sig.get("signal", "hold"),
            "strength": strength,
            "pnl": pnl
        }

        # 6) Classic mode
        if not return_explanation:
            return decision

        # 7) Explanation mode
        explanation = (
            f"Strategy={strategy.__class__.__name__}, "
            f"Signal={sig.get('signal')}, "
            f"Strength(raw)={raw_strength}, "
            f"Strength(adj)={strength}, "
            f"Price={price}, "
            f"PnL={pnl}, "
            f"HistoryLen={len(history)}"
        )

        return decision, explanation
