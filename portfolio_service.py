# ============================================================
# portfolio_service.py — v2.0 (Single Source of Truth Edition)
# ------------------------------------------------------------
# Управляет виртуальными позициями бота — промышленный дизайн.
# Единственный источник правды по позициям и PnL для всех стратегий/бота.
# Все вызовы открытия/закрытия/запроса состояния — только через PortfolioService!
# ============================================================

from typing import Dict, Any, Optional

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
    - trades: list — история всех совершённых сделок (закрытий), для аудита и аналитики.
    """

    def __init__(self, config):
        self.cfg = config
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.realized_pnl: float = 0.0
        self.trades = []

    # ------------------------------------------------------------
    # OPEN POSITION (side = 'long' или 'short')
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
        print(f"[PortfolioService] Открыта позиция: {symbol} {side} qty={amount} @ {price}")

    # ------------------------------------------------------------
    # CLOSE POSITION (записывает реализованный PnL и трейд в историю)
    # ------------------------------------------------------------
    def close_position(self, symbol: str, close_price: Optional[float] = None) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            print(f"[PortfolioService] Нет позиции для закрытия: {symbol}")
            return
        entry = pos["entry_price"]
        amount = pos["amount"]
        side = pos.get("side", "long")
        realized = 0.0
        if close_price is not None:
            if side == "long":
                realized = (close_price - entry) * amount
            else:
                realized = (entry - close_price) * amount
            self.realized_pnl += realized
            self.trades.append({
                "symbol": symbol,
                "entry_price": entry,
                "close_price": close_price,
                "amount": amount,
                "side": side,
                "pnl": realized
            })
            print(f"[PortfolioService] Закрыта позиция: {symbol} {side} qty={amount} @ {close_price} | PnL={realized:.2f}   Total realized: {self.realized_pnl:.2f}")
        else:
            print(f"[PortfolioService] Закрыта позиция: {symbol} без расчёта прибыли (нет close_price)")

        del self.positions[symbol]

    # ------------------------------------------------------------
    # GET POSITION
    # ------------------------------------------------------------
    def get_position(self, symbol: str) -> Optional[Dict[str, float]]:
        return self.positions.get(symbol)

    # ------------------------------------------------------------
    # CALCULATE PNL (unrealized PnL по открытой позиции)
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
    # GET PORTFOLIO SNAPSHOT — для heartbeat, отчётов, мониторинга
    # ------------------------------------------------------------
    def portfolio_value(self, snapshot: Dict[str, Any]) -> float:
        """
        Возвращает совокупную (бумажную) стоимость позиций при текущих ценах.
        """
        value = 0.0
        for sym, pos in self.positions.items():
            price = snapshot.get(sym)
            if price is None: continue
            entry = pos["entry_price"]
            amount = pos["amount"]
            side = pos.get("side", "long")
            if side == "long":
                value += (price - entry) * amount
            else:
                value += (entry - price) * amount
        return value

    # ------------------------------------------------------------
    # СНЯТИЕ СЛЕПКА — сериализация портфеля (для бэкапа/аудита)
    # ------------------------------------------------------------
    def as_dict(self) -> dict:
        return {
            "positions": self.positions,
            "realized_pnl": self.realized_pnl,
            "trades": self.trades
        }

    # ------------------------------------------------------------
    # ЗАГРУЗКА СНЯТОГО СЛЕПКА — десериализация портфеля (для бэкапа/аудита)
    # ------------------------------------------------------------
    def load_from_dict(self, data: dict):
        self.positions = data.get("positions", {})
        self.realized_pnl = data.get("realized_pnl", 0.0)
        self.trades = data.get("trades", [])
        print("[PortfolioService] Слепок портфеля успешно загружен.")