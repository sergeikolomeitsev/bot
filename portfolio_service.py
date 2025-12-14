# ============================================================
# PORTFOLIO SERVICE v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Управляет виртуальным портфелем:
# - хранит позиции
# - считает текущую стоимость
# - считает PnL
# - не содержит торговых сигналов
# - не ходит в сеть
# ============================================================

from typing import Optional, Dict, Any


class PortfolioService:
    """
    Управляет виртуальными позициями бота.
    Формат позиции:
    {
        "symbol": str,
        "entry_price": float,
        "amount": float
    }
    """

    def __init__(self, config):
        self.cfg = config
        self.positions: Dict[str, Dict[str, float]] = {}

    # ------------------------------------------------------------
    # PUBLIC — OPEN POSITION
    # ------------------------------------------------------------
    def open_position(self, symbol: str, price: float, amount: float) -> None:
        self.positions[symbol] = {
            "symbol": symbol,
            "entry_price": float(price),
            "amount": float(amount)
        }

    # ------------------------------------------------------------
    # PUBLIC — CLOSE POSITION
    # ------------------------------------------------------------
    def close_position(self, symbol: str) -> None:
        if symbol in self.positions:
            del self.positions[symbol]

    # ------------------------------------------------------------
    # PUBLIC — GET POSITION
    # ------------------------------------------------------------
    def get_position(self, symbol: str) -> Optional[Dict[str, float]]:
        return self.positions.get(symbol)

    # ------------------------------------------------------------
    # PUBLIC — CALCULATE PNL
    # ------------------------------------------------------------
    def calc_pnl(self, symbol: str, current_price: float) -> Optional[float]:
        pos = self.positions.get(symbol)
        if not pos:
            return None

        entry = pos["entry_price"]
        amount = pos["amount"]

        return float((current_price - entry) * amount)

    # ------------------------------------------------------------
    # PUBLIC — PORTFOLIO VALUE
    # ------------------------------------------------------------
    def portfolio_value(self, snapshot: Dict[str, Any]) -> float:
        total = 0.0
        for sym, pos in self.positions.items():
            price = snapshot.get(sym)
            if price is not None:
                total += pos["amount"] * float(price)
        return float(total)
