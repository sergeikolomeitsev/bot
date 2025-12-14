# ============================================================
# HEAVY STRATEGY v9.1 — Real History Edition
# ============================================================

from typing import Dict, Any, Optional, List


class HeavyStrategy:
    def __init__(self, analyzer):
        self.analyzer = analyzer

    def generate_signal(
        self,
        snapshot: Dict[str, Any],
        symbol: str,
        history: List[float]
    ) -> Optional[Dict[str, Any]]:

        if not history or len(history) < 30:
            return None  # мало данных

        ema_fast = self.analyzer.ema(history, 5)
        ema_slow = self.analyzer.ema(history, 20)
        rsi_val = self.analyzer.rsi(history, 14)
        gap_val = self.analyzer.gap(history)
        vol = self.analyzer.volatility(history)

        if None in (ema_fast, ema_slow, rsi_val, gap_val, vol):
            return None

        # BUY logic
        if ema_fast > ema_slow and rsi_val < 65 and gap_val > 0:
            strength = (ema_fast - ema_slow) * 0.5 + max(0, 60 - rsi_val) * 0.2
            return {"signal": "buy", "strength": float(strength)}

        # SELL logic
        if ema_fast < ema_slow and rsi_val > 40 and gap_val < 0:
            strength = (ema_slow - ema_fast) * 0.5 + max(0, rsi_val - 40) * 0.2
            return {"signal": "sell", "strength": float(strength)}

        return {"signal": "hold", "strength": 0.0}
