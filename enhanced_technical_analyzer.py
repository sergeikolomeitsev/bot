# ============================================================
# ENHANCED TECHNICAL ANALYZER v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Чистый математический анализатор:
# - EMA
# - RSI
# - GAP
# - Volatility
# Без состояния. Без побочных эффектов.
# ============================================================

from typing import List, Optional


class EnhancedTechnicalAnalyzer:
    """
    Полностью детерминированный технический анализатор.
    Все методы принимают только массивы чисел.
    """

    # ------------------------------------------------------------
    # INTERNAL — SAFE LIST NORMALIZATION
    # ------------------------------------------------------------
    def _safe(self, arr: Optional[List[float]]) -> Optional[List[float]]:
        if arr is None or not isinstance(arr, list):
            return None
        try:
            return [float(x) for x in arr if x is not None]
        except Exception:
            return None

    # ------------------------------------------------------------
    # EMA
    # ------------------------------------------------------------
    def ema(self, arr: Optional[List[float]], period: int) -> Optional[float]:
        arr = self._safe(arr)
        if arr is None or len(arr) < period or period <= 0:
            return None

        multiplier = 2 / (period + 1)
        value = arr[0]

        for price in arr[1:]:
            value = (price - value) * multiplier + value

        return float(value)

    # ------------------------------------------------------------
    # RSI
    # ------------------------------------------------------------
    def rsi(self, arr: Optional[List[float]], period: int) -> Optional[float]:
        arr = self._safe(arr)
        if arr is None or len(arr) < period + 1 or period <= 0:
            return None

        gains = []
        losses = []

        for i in range(1, len(arr)):
            delta = arr[i] - arr[i - 1]
            if delta > 0:
                gains.append(delta)
                losses.append(0.0)
            else:
                losses.append(abs(delta))
                gains.append(0.0)

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0
        if avg_gain == 0:
            return 0.0

        rs = avg_gain / avg_loss
        return float(100 - (100 / (1 + rs)))

    # ------------------------------------------------------------
    # GAP (последнее изменение)
    # ------------------------------------------------------------
    def gap(self, arr: Optional[List[float]]) -> Optional[float]:
        arr = self._safe(arr)
        if arr is None or len(arr) < 2:
            return None

        return float(arr[-1] - arr[-2])

    # ------------------------------------------------------------
    # VOLATILITY (среднее абсолютное отклонение)
    # ------------------------------------------------------------
    def volatility(self, arr: Optional[List[float]]) -> Optional[float]:
        arr = self._safe(arr)
        if arr is None or len(arr) < 2:
            return None

        diffs = [abs(arr[i] - arr[i - 1]) for i in range(1, len(arr))]
        return float(sum(diffs) / len(diffs))
