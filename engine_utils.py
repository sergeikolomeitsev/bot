# ============================================================
# ENGINE UTILS v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Чистые утилиты без состояния:
# - safe_float
# - clamp
# - percent_change
# - normalize_strength
# ------------------------------------------------------------

from typing import Optional


class EngineUtils:
    """
    Полностью детерминированный набор вспомогательных функций.
    Никаких сетевых запросов, логирования или состояния.
    """

    # --------------------------------------------------------
    # SAFE FLOAT
    # --------------------------------------------------------
    @staticmethod
    def safe_float(value) -> Optional[float]:
        try:
            return float(value)
        except Exception:
            return None

    # --------------------------------------------------------
    # CLAMP
    # --------------------------------------------------------
    @staticmethod
    def clamp(x: float, min_v: float, max_v: float) -> float:
        if x < min_v:
            return min_v
        if x > max_v:
            return max_v
        return x

    # --------------------------------------------------------
    # PERCENT CHANGE
    # --------------------------------------------------------
    @staticmethod
    def percent_change(old: Optional[float], new: Optional[float]) -> Optional[float]:
        try:
            if old is None or new is None or old == 0:
                return None
            return float((new - old) / old * 100)
        except Exception:
            return None

    # --------------------------------------------------------
    # NORMALIZE STRENGTH 0..1
    # --------------------------------------------------------
    @staticmethod
    def normalize_strength(x: Optional[float]) -> Optional[float]:
        if x is None:
            return None
        try:
            return EngineUtils.clamp(float(x), 0.0, 1.0)
        except Exception:
            return None
