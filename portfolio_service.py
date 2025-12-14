# ============================================================
# PORTFOLIO SERVICE v9.1 — AI PRIME TRADING BOT with Realized PnL
# ------------------------------------------------------------
# Управляет виртуальным портфелем:
# - хранит позиции
# - считает текущую стоимость
# - считает PnL (unrealized и realized)
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

    Атрибуты:
    - realized_pnl: float — накопленная реализованная прибыль по всем закрытым сделкам.
    """

    def __init__(self, config):
        self.cfg = config
        self.positions: Dict[str, Dict[str, float]] = {}
        self.realized_pnl: float = 0.0  # Добавлен счетчик реализованного профита

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
    # PUBLIC — CLOSE POSITION (требует текущей цены для учета реализованного профита)
    # ------------------------------------------------------------
    def close_position(self, symbol: str, close_price: Optional[float] = None) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            return
        entry = pos["entry_price"]
        amount = pos["amount"]
        # Если есть цена закрытия — учитываем реализованный профит
        if close_price is not None:
            realized = (close_price - entry) * amount
            self.realized_pnl += realized
            print(f"[PortfolioService] Реализованный PnL по {symbol}: {realized:.2f}. Всего: {self.realized_pnl:.2f}")
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