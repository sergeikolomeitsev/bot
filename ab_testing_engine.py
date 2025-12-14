# ============================================================
# AB TESTING ENGINE v11.0 — Parallel AB test
# ------------------------------------------------------------
# Эмулирует работу baseline и experimental стратегии одновременно
# при каждом поступлении market data. Хранит и сравнивает статистику.
# ============================================================

import json
import datetime
from ai_strategy_manager import AIStrategyManager
from freedom_manager import FreedomManager

REPORT_HOURS = list(range(8, 23))
HISTORY_PATH = 'ab_history.json'

class ABTestingEngine:
    def __init__(self, config, initial_balance=300):
        self.freedom_manager = FreedomManager(config=config, ai_manager=None)
        self.manager = AIStrategyManager(self.freedom_manager, config, initial_balance)
        self.last_hour = None
        self.last_report_date = None
        self.load_history()

    def load_history(self):
        try:
            with open(HISTORY_PATH, 'r') as f:
                self.history = json.load(f)
        except Exception:
            self.history = []

    def save_history(self):
        with open(HISTORY_PATH, 'w') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def on_market_data(self, market_data, freedom=1.0):
        # Обычно market_data содержит snapshot, symbol, history и т.д.
        # Для параллельной гонки стратегиям передаем все разом
        snapshot = market_data["snapshot"]
        symbol = market_data["symbol"]
        history = market_data["history"]
        # Параллельный шаг обеих стратегий. Обе обновляют свой state.
        self.manager.parallel_step(
            market_data, snapshot, symbol, history, freedom
        )

        now = datetime.datetime.now()
        current_hour = now.hour
        # Часовой отчет (оба pnl)
        if current_hour in REPORT_HOURS and self.last_hour != current_hour:
            self.make_hourly_report(now)
            self.last_hour = current_hour
        # Суточный отчет строго в 22:00 (оба pnl)
        if current_hour == 22 and (self.last_report_date != now.date()):
            self.make_daily_report(now)
            self.last_report_date = now.date()

    def make_hourly_report(self, now):
        baseline_pnl = self.manager.get_strategy_pnl('baseline')
        experiment_pnl = self.manager.get_strategy_pnl('experimental')
        data = {
            'type': 'hourly',
            'timestamp': now.isoformat(),
            'baseline_realized_pnl': baseline_pnl['realized'],
            'baseline_unrealized_pnl': baseline_pnl['unrealized'],
            'experiment_realized_pnl': experiment_pnl['realized'],
            'experiment_unrealized_pnl': experiment_pnl['unrealized'],
        }
        self.history.append(data)
        self.save_history()

    def make_daily_report(self, now):
        baseline_pnl = self.manager.get_strategy_pnl('baseline')
        experiment_pnl = self.manager.get_strategy_pnl('experimental')
        promote = experiment_pnl['realized'] > baseline_pnl['realized']
        data = {
            'type': 'daily',
            'timestamp': now.isoformat(),
            'baseline_realized_pnl': baseline_pnl['realized'],
            'baseline_unrealized_pnl': baseline_pnl['unrealized'],
            'experiment_realized_pnl': experiment_pnl['realized'],
            'experiment_unrealized_pnl': experiment_pnl['unrealized'],
            'promote': promote
        }
        self.history.append(data)
        self.save_history()