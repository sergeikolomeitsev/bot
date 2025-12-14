# ============================================================
# AB TESTING ENGINE v10.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Инкапсулирует весь процесс A/B тестирования стратегий:
# - Прокидывает market_data обеим стратегиям через AIStrategyManager
# - Раз в час (08:00-22:00) формирует отчёты по pnl (реализованный/нереализованный)
# - В 22:00 оценивает продвижение экспериментальной стратегии
# - Вся история хранится в ab_history.json, сохранение "трэйдов" и портфелей — в json
# - Не теряет данные при рестарте, всё всегда читается с диска и дописывается
# ============================================================

import json
from datetime import datetime
from ai_strategy_manager import AIStrategyManager
from freedom_manager import FreedomManager

REPORT_HOURS = list(range(8, 23))
HISTORY_PATH = 'ab_history.json'

class ABTestingEngine:
    def __init__(self, initial_balance=300):
        self.freedom_manager = FreedomManager(config=None, ai_manager=None)
        self.manager = AIStrategyManager(self.freedom_manager, initial_balance)
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

    def on_market_data(self, market_data):
        self.manager.step(market_data)
        now = datetime.now()
        current_hour = now.hour

        # Ежечасные отчеты с 8:00 по 22:00, не чаще чем раз в час
        if current_hour in REPORT_HOURS and self.last_hour != current_hour:
            self.make_hourly_report(now)
            self.last_hour = current_hour

        # Суточный отчет строго в 22:00, не срабатывает повторно за один день
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
            'date': now.date().isoformat(),
            'baseline_realized_pnl': baseline_pnl['realized'],
            'experiment_realized_pnl': experiment_pnl['realized'],
            'promoted': promote,
            'experiment_risk': self.manager.get_experiment_risk()
        }
        self.history.append(data)
        self.save_history()

        if promote:
            self.manager.promote_experiment()
        else:
            self.manager.reset_experiment()

    def get_history(self):
        return self.history