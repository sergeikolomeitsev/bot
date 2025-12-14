# ============================================================
# AI STRATEGY MANAGER v10.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Управляет двумя стратегиями одновременно:
# - базовая стратегия (HeavyStrategy)
# - экспериментальная стратегия (VTRStrategy, меняет risk)
# - работает только в тандеме с ABTestingEngine & FreedomManager
# Не содержит активатора A/B. Все стратегии получают данные параллельно.
# Автоматически сохраняет/читает state из json (портфели и trades).
# ============================================================

import json
from heavy_strategy import HeavyStrategy
from vtr_strategy import VTRStrategy

class AIStrategyManager:
    def __init__(self, freedom_manager, initial_balance=300):
        # Интерфейс работы с портфелями по двум json-файлам
        self.baseline_file = 'portfolio_baseline.json'
        self.experiment_file = 'portfolio_experiment.json'
        self.freedom_manager = freedom_manager
        self._init_portfolio_files(initial_balance)
        self.baseline_strategy = HeavyStrategy(self.baseline_file)
        # Экспериментальная стратегия: risk берется из freedom_manager — всегда!
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

    def step(self, market_data):
        """
        Все market_data прокидываются каждой стратегии.
        """
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
        """Текущий risk экспериментальной стратегии (берёт у объекта VTRStrategy)"""
        return getattr(self.experimental_strategy, 'risk', 1.0)

    def promote_experiment(self):
        """
        Promotion: экспериментальная становится базовой,
        новая экспериментальная запускается с повышенным risk через freedom_manager.
        """
        # Переносим state experiment -> baseline
        with open(self.experiment_file, 'r') as f:
            exp_data = json.load(f)
        with open(self.baseline_file, 'w') as f:
            json.dump(exp_data, f, indent=2)
        # Новый experiment — чистый портфель, новый риск
        with open(self.experiment_file, 'w') as f:
            json.dump({'balance': 300, 'positions': {}, 'trades': []}, f, indent=2)
        # Увеличиваем смелость на 1 (но не больше 5, SRP)
        self.freedom_manager.set_level(min(self.freedom_manager.get_level() + 1, 5))
        risk = self.freedom_manager.apply_experimental_boost()
        self.baseline_strategy = HeavyStrategy(self.baseline_file)
        self.experimental_strategy = VTRStrategy(self.experiment_file, risk=risk)

    def reset_experiment(self):
        """
        Новый эксперимент, но risk не увеличивается (в случае провала).
        """
        with open(self.experiment_file, 'w') as f:
            json.dump({'balance': 300, 'positions': {}, 'trades': []}, f, indent=2)
        # Берём актуальный risk у менеджера свободы
        risk = self.freedom_manager.apply_experimental_boost()
        self.experimental_strategy = VTRStrategy(self.experiment_file, risk=risk)