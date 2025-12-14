# ============================================================
# PORTFOLIO SERVICE v9.2 — AI PRIME TRADING BOT with Short support
# ------------------------------------------------------------
# Управляет виртуальным портфелем с учётом шортов:
# - хранит позиции с направлением
# - считает PnL (unrealized и realized), учитывая long/short
# - поддерживает открытие и закрытие short и long
# ============================================================

from typing import Optional, Dict, Any

class PortfolioService:
    """
    Управляет виртуальными позициями бота.
    Формат позиции:
    {
        "symbol": str,
        "entry_price": float,
        "amount": float,
        "side": "long" | "short"
    }

    Атрибуты:
    - realized_pnl: float — накопленная реализованная прибыль по всем закрытым сделкам.
    """

    def __init__(self, config):
        self.cfg = config
        self.positions: Dict[str, Dict[str, float]] = {}
        self.realized_pnl: float = 0.0  # Добавлен счетчик реализованного профита

    # ------------------------------------------------------------
    # PUBLIC — OPEN POSITION (side = 'long' или 'short')
    # ------------------------------------------------------------
    def open_position(self, symbol: str, price: float, amount: float, side: str = "long") -> None:
        """Открыть позицию (long или short)."""
        assert side in ("long", "short")
        self.positions[symbol] = {
            "symbol": symbol,
            "entry_price": float(price),
            "amount": float(amount),
            "side": side
        }

    # ------------------------------------------------------------
    # PUBLIC — CLOSE POSITION (требует текущей цены для учета реализованного профита)
    # ------------------------------------------------------------
    def close_position(self, symbol: str, close_price: Optional[float] = None) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        entry = pos["entry_price"]
        amount = pos["amount"]
        side = pos.get("side", "long")
        # Если есть цена закрытия — учитываем реализованный профит
        if close_price is not None:
            # Для long: profit = (close - entry) * amount
            # Для short: profit = (entry - close) * amount
            if side == "long":
                realized = (close_price - entry) * amount
            else:
                realized = (entry - close_price) * amount
            self.realized_pnl += realized
            print(f"[PortfolioService] Реализованный PnL по {symbol} ({side}): {realized:.2f}. Всего: {self.realized_pnl:.2f}")
        del self.positions[symbol]

    # ------------------------------------------------------------
    # PUBLIC — GET POSITION
    # ------------------------------------------------------------
    def get_position(self, symbol: str) -> Optional[Dict[str, float]]:
        return self.positions.get(symbol)

    # ------------------------------------------------------------
    # PUBLIC — CALCULATE PNL (unrealized PnL по открытой позиции)
    # ------------------------------------------------------------
    def calc_pnl(self, symbol: str, current_price: float) -> Optional[float]:
        pos = self.positions.get(symbol)
        if not pos:
            return None

        entry = pos["entry_price"]
        amount = pos["amount"]
        side = pos.get("side", "long")

        if side == "long":
            return float((current_price - entry) * amount)
        else:
            return float((entry - current_price) * amount)

    # ------------------------------------------------------------
    # PUBLIC — PORTFOLIO VALUE
    # ------------------------------------------------------------
    def portfolio_value(self, snapshot: Dict[str, Any]) -> float:
        # Текущая стоимость по всем открытым позициям (long и short)
        total = 0.0
        for sym, pos in self.positions.items():
            entry = pos["entry_price"]
            amount = pos["amount"]
            side = pos.get("side", "long")
            price = snapshot.get(sym)
            if price is None:
                continue
            if side == "long":
                total += (price - entry) * amount
            else:
                total += (entry - price) * amount
        return total