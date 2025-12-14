# ============================================================
# VTR STRATEGY v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Базовая чистая стратегия:
# - получает snapshot
# - использует Analyzer
# - возвращает направления/сигналы без торговли
# - не знает про портфель, комиссии, ордера
# ============================================================

from typing import Optional, Dict, Any

class VTRStrategy:
    """
    Чистая базовая стратегия.
    Возвращает структурированный сигнал:
    {
        "symbol": str,
        "signal": "buy" | "sell" | "hold",
        "strength": float
    }
    """

    def __init__(self, analyzer):
        self.analyzer = analyzer

    # ------------------------------------------------------------
    # PUBLIC — MAIN ENTRY
    # ------------------------------------------------------------
    def generate_signal(self, snapshot: Dict[str, Any], symbol: str, history: Optional[list] = None) -> Optional[
        Dict[str, Any]]:
        """
        Генерирует базовый сигнальный объект на реальной истории.
        """
        price = snapshot.get(symbol)
        if price is None or history is None or len(history) < 20:
            return None

        ema_fast = self.analyzer.ema(history, 5)
        ema_slow = self.analyzer.ema(history, 14)
        gap_val = self.analyzer.gap(history)

        if ema_fast is None or ema_slow is None or gap_val is None:
            return None

        if ema_fast > ema_slow and gap_val > 0:
            return {
                "symbol": symbol,
                "signal": "buy",
                "strength": float(abs(gap_val))
            }
        if ema_fast < ema_slow and gap_val < 0:
            return {
                "symbol": symbol,
                "signal": "sell",
                "strength": float(abs(gap_val))
            }

        return {
            "symbol": symbol,
            "signal": "hold",
            "strength": 0.0
        }
