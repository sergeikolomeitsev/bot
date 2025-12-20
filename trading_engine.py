# ============================================================
# TRADING ENGINE v9.5 — Параллельное управление двумя стратегиями
# ------------------------------------------------------------
# ✔ Получает real-market history через DI
# ✔ Передаёт history сразу в обе стратегии через parallel_step
# ✔ Для каждого символа рассчитывает сигналы, действия, PnL для baseline и experimental
# ✔ Корректно ведёт логику открытия/закрытия для двух портфелей
# ============================================================

from typing import Dict, Any, Optional

class TradingEngine:
    def __init__(
        self,
        config,
        ai_manager,
        analyzer,
        portfolio=None,     # теперь портфели у стратегий!
        utils=None,
        freedom=None,
        market_data=None
    ):
        self.cfg = config
        self.ai_manager = ai_manager
        self.analyzer = analyzer
        self.utils = utils
        self.freedom = freedom
        self.market_data = market_data  # DI injected MarketDataManager

    # ------------------------------------------------------------
    # PROCESS ONE SYMBOL (ПАРАЛЛЕЛЬНО ДЛЯ BASE и EXPERIMENTAL)
    # ------------------------------------------------------------
    def process(
        self,
        snapshot: Dict[str, Any],
        symbol: str,
        history: Optional[list] = None,
        return_explanation: bool = False
    ):
        """
        Параллельный расчет решений и действий для baseline и experimental стратегий.
        Возвращает dict из двух решений или (dict, dict_explanation)
        """

        # 1) Получаем историю, если TradingLoop не передал её напрямую
        if history is None and self.market_data is not None:
            history = self.market_data.get_history(symbol)

        if not history or len(history) < 10:
            explanation = {
                'baseline': 'History too short',
                'experimental': 'History too short'
            }
            return (None, explanation) if return_explanation else None

        # 2) Запускаем parallel_step менеджера стратегий
        freedom = self.freedom.get_multiplier() if self.freedom is not None else 1.0
        results = self.ai_manager.parallel_step(
            market_data=self.market_data,
            snapshot=snapshot,
            symbol=symbol,
            history=history,
            freedom=freedom,
            return_decisions=True
        )
        # results: {
        #   'baseline': {'signal': ..., 'action': ...},
        #   'experimental': {'signal': ..., 'action': ...},
        # }

        # 3) Получаем price из snapshot
        price = snapshot.get(symbol)

        # 4) Собираем и рассчитываем информацию по обоим стратегиям
        decisions = {}
        explanations = {}
        for mode, res in results.items():
            strat = self.ai_manager.baseline_strategy if mode == 'baseline' else self.ai_manager.experimental_strategy
            sig = res.get('signal')
            action = res.get('action')

            # Для PnL, позиции и силы сигнала
            strength = float(sig.get('strength', 0.0)) if sig else 0.0
            signal = sig.get('signal') if sig else 'hold'
            pos = strat.positions.get(symbol) if hasattr(strat, "positions") else None

            pnl = None
            if pos and price is not None and hasattr(strat, "get_pnl"):
                try:
                    pnl = strat.get_pnl(snapshot).get("realized", None)
                except Exception:
                    pnl = None

            explanation = None
            if action == 'open_long':
                explanation = "Open LONG"
            elif action == 'open_short':
                explanation = "Open SHORT"
            elif action == 'hold_long':
                explanation = "Already in LONG"
            elif action == 'hold_short':
                explanation = "Already in SHORT"
            elif action == 'hold':
                explanation = "Hold"
            else:
                explanation = f"Unknown action: {action}"

            decisions[mode] = {
                "symbol": symbol,
                "signal": signal,
                "strength": strength,
                "pnl": pnl,
                "action": action
            }
            explanations[mode] = explanation

        if return_explanation:
            return (decisions, explanations)
        else:
            return decisions