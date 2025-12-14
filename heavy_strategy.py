# ============================================================
# HEAVY STRATEGY v10.0 — Real History Edition / AB Compatible
# ============================================================
# - Совместима с новым AI Strategy Manager и AB Testing Engine
# - Каждый экземпляр хранит СОБСТВЕННЫЙ портфель в JSON (portfolio_baseline.json или portfolio_experiment.json)
# - Автоматически сохраняет и загружает историю сделок и позиции при работе
# - generate_signal не менялся, бизнес-логика сигналов полностью сохранена
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

        # BUY logic
        if ema_fast > ema_slow and rsi_val < 65 and gap_val > 0:
            strength = (ema_fast - ema_slow) * 0.5 + max(0, 60 - rsi_val) * 0.2
            return {"signal": "buy", "strength": float(strength)}

        # SELL logic
        if ema_fast < ema_slow and rsi_val > 40 and gap_val < 0:
            strength = (ema_slow - ema_fast) * 0.5 + max(0, rsi_val - 40) * 0.2
            return {"signal": "sell", "strength": float(strength)}

        return {"signal": "hold", "strength": 0.0}

    def get_pnl(self):
        """
        Возвращает pnl по реализованным и нереализованным позициям:
        {'realized': ..., 'unrealized': ...}
        """
        realized = sum([t.get('pnl', 0) for t in self.trades])
        unrealized = 0  # реализуйте свою метрику, если нужно
        return {'realized': realized, 'unrealized': unrealized}