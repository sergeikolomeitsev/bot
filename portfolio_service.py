# ============================================================
# portfolio_service.py — v2.4 (DI-integration, dump/load methods, heartbeat sync)
# ------------------------------------------------------------
# Теперь добавлены методы save_to_file/load_from_file (опционально JSON путь передают стратегии, если нужно),
# после КАЖДОЙ сделки состояние обязательно сохраняется!
# ============================================================

from typing import Dict, Any, Optional
from datetime import datetime, date
import json

class PortfolioService:
    def __init__(self, config, path: Optional[str] = None):
        self.cfg = config
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.realized_pnl: float = 0.0
        self.trades = []
        self.path = path

    def save_to_file(self, path: Optional[str] = None):
        if not path:
            path = self.path
        if path:
            with open(path, "w") as f:
                json.dump(self.as_dict(), f, indent=2)

    def load_from_file(self, path: Optional[str] = None):
        if not path:
            path = self.path
        if path:
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                self.load_from_dict(data)
            except Exception:
                pass

    def trades_today_stats(self):
        today = date.today()
        total = win = loss = 0
        for t in self.trades:
            close_dt = t.get("close_time")
            if close_dt:
                try:
                    d = datetime.fromisoformat(close_dt).date()
                except Exception:
                    d = today
            else:
                d = today
            if d == today:
                total += 1
                if t.get("pnl", 0) > 0:
                    win += 1
                elif t.get("pnl", 0) < 0:
                    loss += 1
        return total, win, loss

    def open_position(self, symbol: str, price: float, amount: float, side: str = "long") -> None:
        assert side in ("long", "short")
        existing = self.positions.get(symbol)
        if existing is not None:
            self.close_position(symbol, close_price=price)
        self.positions[symbol] = {
            "symbol": symbol,
            "entry_price": float(price),
            "amount": float(amount),
            "side": side
        }
        print(f"[PortfolioService] Открыта позиция: {symbol} {side} qty={amount} @ {price}")
        self.save_to_file()

    def close_position(self, symbol: str, close_price: Optional[float] = None) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            print(f"[PortfolioService] Нет позиции для закрытия: {symbol}")
            return
        entry = pos["entry_price"]
        amount = pos["amount"]
        side = pos.get("side", "long")
        realized = 0.0
        close_time = datetime.now().isoformat()
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
                "pnl": realized,
                "close_time": close_time
            })
            total, win, loss = self.trades_today_stats()
            print(f"[PortfolioService] Закрыта позиция: {symbol} {side} qty={amount} @ {close_price} | PnL={realized:.2f}   Total realized: {self.realized_pnl:.2f}")
            print(f"[PortfolioService] 🔢 Сделок за сегодня: всего={total} | успешных={win} | неуспешных={loss}")
        else:
            print(f"[PortfolioService] Закрыта позиция: {symbol} без расчёта прибыли (нет close_price)")
        del self.positions[symbol]
        self.save_to_file()

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        return self.positions.get(symbol)

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

    def portfolio_value(self, snapshot: Dict[str, Any]) -> float:
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

    def as_dict(self) -> dict:
        return {
            "positions": self.positions,
            "realized_pnl": self.realized_pnl,
            "trades": self.trades
        }

    def load_from_dict(self, data: dict):
        self.positions = data.get("positions", {})
        self.realized_pnl = data.get("realized_pnl", 0.0)
        self.trades = data.get("trades", [])
        print("[PortfolioService] Слепок портфеля успешно загружен.")