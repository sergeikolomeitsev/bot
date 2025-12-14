# ============================================================
# ai_strategy_manager.py — v10.2 (fix: get_active_strategy и experimental_active)
# ------------------------------------------------------------
# AI STRATEGY MANAGER v10.2 — AI PRIME TRADING BOT
# Поддержка get_active_strategy и experimental_active для heartbeat
# ============================================================

import json
from heavy_strategy import HeavyStrategy
from vtr_strategy import VTRStrategy

class AIStrategyManager:
    def __init__(self, freedom_manager, config, initial_balance=300):
        self.baseline_file = 'portfolio_baseline.json'
        self.experiment_file = 'portfolio_experiment.json'
        self.freedom_manager = freedom_manager
        self.config = config
        self._init_portfolio_files(initial_balance)
        self.baseline_strategy = HeavyStrategy(self.baseline_file)
        risk = self.freedom_manager.apply_experimental_boost()
        self.experimental_strategy = VTRStrategy(self.experiment_file, risk=risk)

        self._experimental_active = False  # По умолчанию

    def _init_portfolio_files(self, balance):
        for fname in [self.baseline_file, self.experiment_file]:
            try:
                with open(fname, 'r') as f:
                    content = json.load(f)
                    if 'balance' not in content:
                        raise Exception
            except Exception:
                with open(fname, 'w') as f:
                    json.dump({'balance': balance, 'positions': {}, 'trades': []}, f, indent=2)

    def set_base_strategy(self, strategy):
        self.baseline_strategy = strategy

    def step(self, market_data):
        self.baseline_strategy.on_market_data(market_data)
        self.experimental_strategy.on_market_data(market_data)

    def get_strategy_pnl(self, which):
        if which == 'baseline':
            return self.baseline_strategy.get_pnl()
        elif which == 'experimental':
            return self.experimental_strategy.get_pnl()
        else:
            return {'realized': 0, 'unrealized': 0}

    def get_experiment_risk(self):
        return getattr(self.experimental_strategy, 'risk', 1.0)

    def promote_experiment(self):
        with open(self.experiment_file, 'r') as f:
            exp_data = json.load(f)
        with open(self.baseline_file, 'w') as f:
            json.dump(exp_data, f, indent=2)
        with open(self.experiment_file, 'w') as f:
            json.dump({'balance': self.config.initial_balance, 'positions': {}, 'trades': []}, f, indent=2)
        risk = self.freedom_manager.apply_experimental_boost()
        self.experimental_strategy = VTRStrategy(self.experiment_file, risk=risk)

    # ==========================
    # Добавлено для heartbeat
    # ==========================
    def get_active_strategy(self):
        """Возвращает текущую активную стратегию: экспериментальная или базовая."""
        if self.experimental_active:
            return self.experimental_strategy
        else:
            return self.baseline_strategy

    @property
    def experimental_active(self):
        """Вернуть True если активен эксперимент (заглушка, при необходимости расширить)."""
        return self._experimental_active

    @experimental_active.setter
    def experimental_active(self, val):
        self._experimental_active = bool(val)