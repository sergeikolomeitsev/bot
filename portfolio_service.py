# ============================================================
# portfolio_service.py — v2.5 (TP, SL, trailing_extremum fields in trade history)
# ============================================================

from typing import Dict, Any, Optional
from datetime import datetime, date
import json

class PortfolioService:
    def __init__(self, config, path: Optional[str] = None):
        print("[DEBUG] PortfolioService created! id:", id(self))

        self.cfg = config
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.realized_pnl: float = 0.0
        self.trades = []
        self.path = path
        self.open_extras = {}  # для хранения фич входа по каждой открытой позиции

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

    # Измени open_position так:
    def open_position(
            self, symbol: str, price: float, amount: float, side: str = "long",
            tp: Optional[float] = None, sl: Optional[float] = None, trailing_extremum: Optional[float] = None,
            indicators: Optional[dict] = None, confidence: Optional[float] = None,
            market_snapshot: Optional[dict] = None, balance: Optional[float] = None, risk: Optional[float] = None,
            open_reason: Optional[str] = None,
            timestamp: Optional[str] = None,
    ) -> None:
        assert side in ("long", "short")
        existing = self.positions.get(symbol)
        if existing is not None:
            self.close_position(symbol, close_price=price, close_reason="open_new")
        now = timestamp or datetime.now().isoformat()
        # Сохраним все доп.поля по открытию в спец-словарь open_extras
        self.open_extras[symbol] = {
            "indicators": indicators or {},
            "confidence": confidence,
            "market_snapshot": market_snapshot or {},
            "open_reason": open_reason,
            "open_time": now,
            "open_balance": balance,
            "open_risk": risk,
            "bars_lifetime": 0,
        }
        self.positions[symbol] = {
            "symbol": symbol,
            "entry_price": float(price),
            "amount": float(amount),
            "side": side,
            "tp": tp,
            "sl": sl,
            "trailing_extremum": trailing_extremum,
            "open_time": now,
        }
        print(
            f"[PortfolioService] Открыта позиция: {symbol} {side} qty={amount} @ {price} TP={tp} SL={sl} trailing={trailing_extremum}")
        self.save_to_file()

    # Измени close_position:

    def close_position(
            self, symbol: str, close_price: Optional[float] = None,
            close_reason: Optional[str] = None, close_timestamp: Optional[str] = None
    ) -> None:
        pos = self.positions.get(symbol)
        if not pos:
            print(f"[PortfolioService] Нет позиции для закрытия: {symbol}")
            return
        entry = pos["entry_price"]
        amount = pos["amount"]
        side = pos.get("side", "long")
        tp = pos.get("tp")
        sl = pos.get("sl")
        trailing_extremum = pos.get("trailing_extremum")
        open_time = pos.get("open_time")
        realized = 0.0
        close_time = close_timestamp or datetime.now().isoformat()
        # lifetime in bars (если заполняется где-то, иначе None)
        bars_lifetime = None
        # достанем экстры
        extras = self.open_extras.pop(symbol, {})
        indicators = extras.get("indicators")
        confidence = extras.get("confidence")
        market_snapshot = extras.get("market_snapshot")
        open_reason = extras.get("open_reason")
        open_balance = extras.get("open_balance")
        open_risk = extras.get("open_risk")
        bars_lifetime = extras.get("bars_lifetime")
        if open_time and close_time:
            try:
                enter_dt = datetime.fromisoformat(open_time)
                close_dt = datetime.fromisoformat(close_time)
                seconds_lifetime = (close_dt - enter_dt).total_seconds()
            except Exception:
                seconds_lifetime = None
        else:
            seconds_lifetime = None

        if close_price is not None:
            fee_pct = getattr(self.cfg, "FEE_PCT", 0.0007)
            spread_pct = getattr(self.cfg, "SPREAD_PCT", 0.0005)
            total_fee = fee_pct + spread_pct

            if side == "long":
                realized = (close_price - entry) * amount
            else:
                realized = (entry - close_price) * amount

            commission_open = entry * amount * total_fee
            commission_close = close_price * amount * total_fee
            realized -= commission_open
            realized -= commission_close

            self.realized_pnl += realized
            self.trades.append({
                "symbol": symbol,
                "entry_price": entry,
                "close_price": close_price,
                "amount": amount,
                "side": side,
                "pnl": realized,
                "tp": tp,
                "sl": sl,
                "trailing_extremum": trailing_extremum,
                "open_time": open_time,
                "close_time": close_time,
                "seconds_lifetime": seconds_lifetime,
                "bars_lifetime": bars_lifetime,
                "commission_open": commission_open,
                "commission_close": commission_close,
                "indicators": indicators,
                "confidence": confidence,
                "market_snapshot": market_snapshot,
                "open_reason": open_reason,
                "open_balance": open_balance,
                "open_risk": open_risk,
                "close_reason": close_reason,
            })
            total, win, loss = self.trades_today_stats()
            print(
                f"[PortfolioService] Закрыта позиция: {symbol} {side} qty={amount} @ {close_price} | PnL={realized:.2f}   Total realized: {self.realized_pnl:.2f}")
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