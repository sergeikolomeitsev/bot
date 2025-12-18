# ============================================================
# dependency_container.py — v9.4 DI: portfolio injection to all strategies
# ------------------------------------------------------------

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
    DI-контейнер: создаёт все модули и связывает зависимости строго по контракту.
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
        # PORTFOLIOS (инъекция!)
        # ------------------------------------------------------------
        self.portfolio_baseline = PortfolioService(self.config)
        self.portfolio_experiment = PortfolioService(self.config)

        # ------------------------------------------------------------
        # STRATEGIES (портфель передаётся обязательно!)
        # ------------------------------------------------------------
        self.vtr_strategy = VTRStrategy(self.portfolio_experiment, analyzer=self.analyzer)
        self.heavy_strategy = HeavyStrategy(self.portfolio_baseline, analyzer=self.analyzer)

        # ------------------------------------------------------------
        # CYCLIC DEPS: FREEDOM MANAGER <-> AI STRATEGY MANAGER
        # ------------------------------------------------------------
        self.freedom_manager = FreedomManager(self.config, None)
        print("[DEBUG] DependencyContainer: self.analyzer before manager =", repr(self.analyzer), type(self.analyzer))
        self.ai_manager = AIStrategyManager(self.freedom_manager, self.config, self.analyzer,
                                            portfolio_baseline=self.portfolio_baseline,
                                            portfolio_experiment=self.portfolio_experiment)
        self.freedom_manager.set_ai_manager(self.ai_manager)
        # ------------------------------------------------------------
        # WS FEED
        # ------------------------------------------------------------
        self.ws_feed = WSPriceFeed(self.config)
        # ------------------------------------------------------------
        # MARKET DATA MANAGER
        # ------------------------------------------------------------
        self.market_data = MarketDataManager(self.config, self.ws_feed)
        # ------------------------------------------------------------
        # AB TESTING ENGINE
        # ------------------------------------------------------------
        self.ab_engine = ABTestingEngine(
            self.config, self.analyzer, initial_balance=300,
            portfolio_baseline=self.portfolio_baseline,
            portfolio_experiment=self.portfolio_experiment
        )
        # ------------------------------------------------------------
        # TRADING ENGINE
        # ------------------------------------------------------------
        self.trading_engine = TradingEngine(
            self.config,
            self.ai_manager,
            self.analyzer,
            self.portfolio_baseline,
            self.utils,
            self.freedom_manager,
            market_data=self.market_data
        )

        # ------------------------------------------------------------
        # REPORTING ENGINE
        # ------------------------------------------------------------
        self.reporting_engine = ReportingEngine(self.telegram_bot)

        # ------------------------------------------------------------
        # HEARTBEAT & TRADING LOOP
        # ------------------------------------------------------------
        self.heartbeat = HeartbeatBuilder(self,
                                          baseline_strategy=self.heavy_strategy,
                                          experimental_strategy=self.vtr_strategy)
        self.trading_loop = TradingLoop(
            self.config,
            self.ab_engine,
            self.telegram_bot,
            self.heartbeat,
            market_data=self.market_data
        )

    def get_loop(self):
        return self.trading_loop

    def build_heartbeat_summary(self):
        return self.heartbeat.build()