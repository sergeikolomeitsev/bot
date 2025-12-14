# ============================================================
# ai_strategy_manager.py — v11.0 — Parallel AB test
# ------------------------------------------------------------
# Поддержка параллельной работы baseline и experimental стратегий
# для live-сравнения в AB-режиме.
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

    # --- Новый главный параллельный step для обоих стратегий ---
    def parallel_step(self, market_data, snapshot, symbol, history, freedom, return_decisions=False):
        # baseline
        base_sig = self.baseline_strategy.generate_signal(snapshot, symbol, history)
        base_action = None
        if base_sig is not None:
            raw_str = float(base_sig.get("strength", 0.0))
            base_strength = raw_str * freedom
            base_signal = base_sig.get("signal")
            pos = self.baseline_strategy.positions.get(symbol)
            price = snapshot[symbol]
            if base_signal == "long":
                if not pos or pos.get("side") != "long":
                    if pos:
                        self.baseline_strategy.close_position(symbol, price)
                    self.baseline_strategy.open_position(symbol, price, base_strength, "long")
                    base_action = "open_long"
                else:
                    base_action = "hold_long"
            elif base_signal == "short":
                if not pos or pos.get("side") != "short":
                    if pos:
                        self.baseline_strategy.close_position(symbol, price)
                    self.baseline_strategy.open_position(symbol, price, base_strength, "short")
                    base_action = "open_short"
                else:
                    base_action = "hold_short"
            elif base_signal == "hold":
                base_action = "hold"

        # experimental
        exp_sig = self.experimental_strategy.generate_signal(snapshot, symbol, history)
        exp_action = None
        if exp_sig is not None:
            raw_str = float(exp_sig.get("strength", 0.0))
            exp_strength = raw_str * freedom
            exp_signal = exp_sig.get("signal")
            pos = self.experimental_strategy.positions.get(symbol)
            price = snapshot[symbol]
            if exp_signal == "long":
                if not pos or pos.get("side") != "long":
                    if pos:
                        self.experimental_strategy.close_position(symbol, price)
                    self.experimental_strategy.open_position(symbol, price, exp_strength, "long")
                    exp_action = "open_long"
                else:
                    exp_action = "hold_long"
            elif exp_signal == "short":
                if not pos or pos.get("side") != "short":
                    if pos:
                        self.experimental_strategy.close_position(symbol, price)
                    self.experimental_strategy.open_position(symbol, price, exp_strength, "short")
                    exp_action = "open_short"
                else:
                    exp_action = "hold_short"
            elif exp_signal == "hold":
                exp_action = "hold"

        if return_decisions:
            return {
                "baseline": {"signal": base_sig, "action": base_action},
                "experimental": {"signal": exp_sig, "action": exp_action}
            }

    def get_strategy_pnl(self, which):
        if which == 'baseline':
            return self.baseline_strategy.get_pnl()
        elif which == 'experimental':
            return self.experimental_strategy.get_pnl()
        else:
            return {'realized': 0, 'unrealized': 0}