# ============================================================
# VTR STRATEGY v10.3 — добавлен open_position/close_position для AI Strategy Manager
# ============================================================

from typing import Optional, Dict, Any, List
import json
import os

class VTRStrategy:
    def __init__(self, portfolio_file, risk=1.0, analyzer=None):
        self.analyzer = analyzer
        self.portfolio_file = portfolio_file
        self.risk = risk
        self._ensure_portfolio_file()
        self._load_portfolio()

    def _ensure_portfolio_file(self):
        if not os.path.exists(self.portfolio_file):
            with open(self.portfolio_file, 'w') as f:
                json.dump({'balance': 300, 'positions': {}, 'trades': []}, f, indent=2)

    def _load_portfolio(self):
        with open(self.portfolio_file, 'r') as f:
            data = json.load(f)
        self.balance = data.get('balance', 300)
        self.positions = data.get('positions', {})
        self.trades = data.get('trades', [])

    def _save_portfolio(self):
        data = {
            'balance': self.balance,
            'positions': self.positions,
            'trades': self.trades
        }
        with open(self.portfolio_file, 'w') as f:
            json.dump(data, f, indent=2)

    def open_position(self, symbol, price, amount, side="long"):
        self.positions[symbol] = {
            "symbol": symbol,
            "entry_price": float(price),
            "amount": float(amount),
            "side": side
        }
        self.trades.append({
            "symbol": symbol,
            "entry_price": float(price),
            "amount": float(amount),
            "side": side,
            "type": "open"
        })
        self._save_portfolio()

    def close_position(self, symbol, close_price=None):
        pos = self.positions.get(symbol)
        if not pos:
            return
        entry = pos["entry_price"]
        amount = pos["amount"]
        side = pos.get("side", "long")
        realized = 0
        if close_price is not None:
            if side == "long":
                realized = (close_price - entry) * amount
            else:
                realized = (entry - close_price) * amount
        self.trades.append({
            "symbol": symbol,
            "entry_price": entry,
            "close_price": close_price,
            "amount": amount,
            "side": side,
            "type": "close",
            "pnl": realized
        })
        del self.positions[symbol]
        self._save_portfolio()

    def generate_signal(
        self,
        snapshot: Dict[str, Any],
        symbol: str,
        history: Optional[List[float]] = None
    ) -> Optional[Dict[str, Any]]:
        price = snapshot.get(symbol)
        if price is None or history is None or len(history) < 20:
            return None

        ema_fast = self.analyzer.ema(history, 5)
        ema_slow = self.analyzer.ema(history, 14)
        gap_val = self.analyzer.gap(history)

        if ema_fast is None or ema_slow is None or gap_val is None:
            return None

        # LONG logic (buy/open/hold long)
        if ema_fast > ema_slow and gap_val > 0:
            return {
                "symbol": symbol,
                "signal": "long",
                "strength": float(abs(gap_val) * self.risk)
            }
        # SHORT logic (sell/open/hold short)
        if ema_fast < ema_slow and gap_val < 0:
            return {
                "symbol": symbol,
                "signal": "short",
                "strength": float(abs(gap_val) * self.risk)
            }
        # otherwise HOLD
        return {
            "symbol": symbol,
            "signal": "hold",
            "strength": 0.0
        }

    def get_pnl(self):
        """
        Возвращает pnl по реализованным и нереализованным позициям:
        {'realized': ..., 'unrealized': ...}
        """
        realized = sum([t.get('pnl', 0) for t in self.trades])
        unrealized = 0  # реализуйте свой расчет при необходимости
        return {'realized': realized, 'unrealized': unrealized}

    def on_market_data(self, market_data):
        pass