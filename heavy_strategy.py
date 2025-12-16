# ============================================================
# HEAVY STRATEGY v10.4 — с open_position/close_position для AI Strategy Manager
# ============================================================
# - Совместима с AI Strategy Manager и AB Testing Engine
# - Хранит портфель в JSON (portfolio_baseline.json или portfolio_experiment.json)
# - Сохраняет историю сделок и позиций
# - generate_signal не менялся, бизнес-логика сохранена полностью
# - Добавлены open_position и close_position для совместимости с менеджером стратегий
# ============================================================

from typing import Dict, Any, Optional, List
import json
import os

class HeavyStrategy:
    def __init__(self, portfolio_file, analyzer=None):
        self.analyzer = analyzer
        self.portfolio_file = portfolio_file
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
        history: List[float]
    ) -> Optional[Dict[str, Any]]:
        if not history or len(history) < 30:
            return None  # мало данных

        ema_fast = self.analyzer.ema(history, 5)
        ema_slow = self.analyzer.ema(history, 20)
        rsi_val = self.analyzer.rsi(history, 14)
        gap_val = self.analyzer.gap(history)
        vol = self.analyzer.volatility(history)

        if None in (ema_fast, ema_slow, rsi_val, gap_val, vol):
            return None

        # LONG logic
        if ema_fast > ema_slow and rsi_val < 65 and gap_val > 0:
            strength = (ema_fast - ema_slow) * 0.5 + max(0, 60 - rsi_val) * 0.2
            return {"signal": "long", "strength": float(strength)}

        # SHORT logic
        if ema_fast < ema_slow and rsi_val > 40 and gap_val < 0:
            strength = (ema_slow - ema_fast) * 0.5 + max(0, rsi_val - 40) * 0.2
            return {"signal": "short", "strength": float(strength)}

        return {"signal": "hold", "strength": 0.0}

    def get_pnl(self):
        """
        Возвращает pnl по реализованным и нереализованным позициям:
        {'realized': ..., 'unrealized': ...}
        """
        realized = sum([t.get('pnl', 0) for t in self.trades])
        unrealized = 0  # реализуйте свой расчет при необходимости
        return {'realized': realized, 'unrealized': unrealized}

    def on_market_data(self, market_data):
        """
        Заглушка для совместимости. При необходимости реализуйте вашу логику.
        """
        pass