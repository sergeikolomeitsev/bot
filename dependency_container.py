# ============================================================
# dependency_container.py — v9.3 (инициализация TradingLoop строго с 4 аргументами)
# ------------------------------------------------------------
# DI-контейнер: создание объектов модулей и установка зависимостей для AI PRIME TRADING BOT
# ============================================================

from config import Config
from telegram_bot import TelegramBot
from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from engine_utils import EngineUtils
from validation_service import ValidationService
from vtr_strategy import VTRStrategy
from heavy_strategy import HeavyStrategy
from ai_strategy_manager import AIStrategyManager
from freedom_manager import FreedomManager
from ws_price_feed import WSPriceFeed
from market_data_manager import MarketDataManager
from portfolio_service import PortfolioService
from ab_testing_engine import ABTestingEngine
from trading_engine import TradingEngine
from reporting_engine import ReportingEngine
from trading_loop import TradingLoop
from heartbeat_builder import HeartbeatBuilder

class DependencyContainer:
    """
    DI-контейнер: создаёт все модули и связывает зависимости строго по контракту v9.3.
    """

    def __init__(self):
        # ------------------------------------------------------------
        # CONFIG
        # ------------------------------------------------------------
        self.config = Config()

        # ------------------------------------------------------------
        # TELEGRAM BOT
        # ------------------------------------------------------------
        self.telegram_bot = TelegramBot(
            token=self.config.api.telegram_token,
            chat_id=self.config.api.telegram_chat_id
        )

        # ------------------------------------------------------------
        # UTILS / ANALYZER / VALIDATOR
        # ------------------------------------------------------------
        self.analyzer = EnhancedTechnicalAnalyzer()
        self.utils = EngineUtils()
        self.validator = ValidationService()

        # ------------------------------------------------------------
        # STRATEGIES (первым аргументом - путь к json-файлу портфеля)
        # ------------------------------------------------------------
        self.vtr_strategy = VTRStrategy("portfolio_experiment.json", analyzer=self.analyzer)
        self.heavy_strategy = HeavyStrategy("portfolio_baseline.json", analyzer=self.analyzer)

        # ------------------------------------------------------------
        # CYCLIC DEPS: FREEDOM MANAGER <-> AI STRATEGY MANAGER
        # ------------------------------------------------------------
        self.freedom_manager = FreedomManager(self.config, None)
        self.ai_manager = AIStrategyManager(self.freedom_manager, self.config)
        self.freedom_manager.set_ai_manager(self.ai_manager)
        self.ai_manager.set_base_strategy(self.vtr_strategy)

        # ------------------------------------------------------------
        # WS FEED
        # ------------------------------------------------------------
        self.ws_feed = WSPriceFeed(self.config)

        # ------------------------------------------------------------
        # MARKET DATA MANAGER
        # ------------------------------------------------------------
        self.market_data = MarketDataManager(self.config, self.ws_feed)

        # ------------------------------------------------------------
        # PORTFOLIO
        # ------------------------------------------------------------
        self.portfolio = PortfolioService(self.config)

        # ------------------------------------------------------------
        # AB TESTING ENGINE
        # ------------------------------------------------------------
        self.ab_engine = ABTestingEngine()  # Только один аргумент или без аргументов

        # ------------------------------------------------------------
        # TRADING ENGINE
        # ------------------------------------------------------------
        self.trading_engine = TradingEngine(
            self.config,
            self.ai_manager,
            self.analyzer,
            self.portfolio,
            self.utils,
            self.freedom_manager,
            market_data=self.market_data
        )

        # ------------------------------------------------------------
        # REPORTING ENGINE
        # ------------------------------------------------------------
        self.reporting_engine = ReportingEngine(self.telegram_bot)

        # ------------------------------------------------------------
        # TRADING LOOP (ТОЛЬКО 4 аргумента!)
        # ------------------------------------------------------------
        self.heartbeat = HeartbeatBuilder(self)
        self.trading_loop = TradingLoop(
            self.config,
            self.ab_engine,
            self.telegram_bot,
            self.heartbeat
        )

    def get_loop(self):
        return self.trading_loop

    def build_heartbeat_summary(self):
        """
        Формирует подробный heartbeat:
        - последний снапшот цен
        - открытые позиции
        - PnL по каждой позиции
        - активная стратегия
        - параметры принятия решений
        """
        md = self.market_data
        engine = self.trading_engine
        portfolio = self.portfolio