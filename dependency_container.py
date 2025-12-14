# ============================================================
# dependency_container.py — v9.1 (refactor: cyclic deps fix)
# ------------------------------------------------------------
# DI-контейнер: создание объектов модулей и правильная установка зависимостей для AI PRIME TRADING BOT
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
    DI-контейнер: создаёт все модули и связывает зависимости строго по контракту v9.1.
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
        # STRATEGIES
        # ------------------------------------------------------------
        self.vtr_strategy = VTRStrategy(self.analyzer)
        self.heavy_strategy = HeavyStrategy(self.analyzer)

        # ------------------------------------------------------------
        # CYCLIC DEPS: FREEDOM MANAGER <-> AI STRATEGY MANAGER
        # ------------------------------------------------------------
        # ФАЗА 1 — создать FreedomManager с временным None вместо AIManager
        self.freedom_manager = FreedomManager(self.config, None)
        # ФАЗА 2 — создать AIManager с freedom_manager
        self.ai_manager = AIStrategyManager(self.freedom_manager, self.config)
        # ФАЗА 3 — сконнектить обратно AIManager в FreedomManager
        self.freedom_manager.set_ai_manager(self.ai_manager)
        # NB: если надо, сюда же переносим вызов set_base_strategy
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
        self.ab_engine = ABTestingEngine(
            self.config,
            self.ai_manager,
            self.freedom_manager
        )

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
        # TRADING LOOP
        # ------------------------------------------------------------
        self.trading_loop = TradingLoop(
            self.config,
            self.market_data,
            self.trading_engine,
            self.portfolio,
            self.telegram_bot
        )

        self.heartbeat = HeartbeatBuilder(self)

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