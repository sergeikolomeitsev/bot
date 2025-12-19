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

    def adx(self, highs: list, lows: list, closes: list, period: int = 14) -> float:
        """
        Highs, lows, closes — списки значений (float), одинаковой длины ≥ period+1.
        Возвращает значение ADX по классике Уайлдера.
        """
        if (
            highs is None or lows is None or closes is None or
            len(highs) != len(lows) or len(lows) != len(closes) or
            len(closes) < period + 1
        ):
            return None

        tr_list, plus_dm_list, minus_dm_list = [], [], []

        for i in range(1, len(closes)):
            high = highs[i]
            low = lows[i]
            prev_high = highs[i - 1]
            prev_low = lows[i - 1]
            prev_close = closes[i - 1]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            plus_dm = high - prev_high if (high - prev_high) > (prev_low - low) and (high - prev_high) > 0 else 0
            minus_dm = prev_low - low if (prev_low - low) > (high - prev_high) and (prev_low - low) > 0 else 0

            tr_list.append(tr)
            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

        def wilder_smooth(values):
            result = [sum(values[:period])]
            for val in values[period:]:
                result.append(result[-1] - (result[-1] / period) + val)
            return result

        tr_smoothed = wilder_smooth(tr_list)
        plus_dm_smoothed = wilder_smooth(plus_dm_list)
        minus_dm_smoothed = wilder_smooth(minus_dm_list)

        plus_di = [100 * p / t if t else 0 for p, t in zip(plus_dm_smoothed, tr_smoothed)]
        minus_di = [100 * m / t if t else 0 for m, t in zip(minus_dm_smoothed, tr_smoothed)]
        dx = [100 * abs(p - m) / (p + m) if (p + m) else 0 for p, m in zip(plus_di, minus_di)]

        if len(dx) < period:
            return None
        adx_values = [sum(dx[:period]) / period]
        for d in dx[period:]:
            adx_values.append((adx_values[-1] * (period - 1) + d) / period)
        return float(adx_values[-1]) if adx_values else None