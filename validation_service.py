# ============================================================
# VALIDATION SERVICE v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Отвечает только за проверку snapshot:
# - корректность структуры
# - отсутствие None / NaN
# - корректные типы
# - минимальные требования к данным
# Не содержит бизнес-логики.
# ============================================================

from typing import Dict, Any, Optional


class ValidationService:
    """
    Чистый валидатор данных рынка.
    Не знает про стратегии, позиции, торговый цикл.
    """

    # ------------------------------------------------------------
    # PUBLIC — MAIN VALIDATION
    # ------------------------------------------------------------
    def validate_snapshot(self, snapshot: Optional[Dict[str, Any]]) -> bool:
        if snapshot is None:
            return False

        if not isinstance(snapshot, dict):
            return False

        if len(snapshot) == 0:
            return False

        for symbol, price in snapshot.items():

            # Символ должен быть строкой
            if not isinstance(symbol, str) or len(symbol) == 0:
                return False

            # Цена должна быть числом
            if price is None:
                return False

            try:
                p = float(price)
            except Exception:
                return False

            if p <= 0:
                return False

        return True

    # ------------------------------------------------------------
    # PUBLIC — SAFE EXTRACT PRICE
    # ------------------------------------------------------------
    def get_price(self, snapshot: Dict[str, Any], symbol: str) -> Optional[float]:
        """
        Возвращает цену инструмента, если она есть и валидна.
        """
        if symbol not in snapshot:
            return None

        try:
            p = float(snapshot[symbol])
            return p if p > 0 else None
        except Exception:
            return None
