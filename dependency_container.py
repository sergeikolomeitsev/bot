# ============================================================
# dependency_container.py — v9.5 DI: STRICT portfolio injection
# ------------------------------------------------------------
# Портфели и стратегии создаются только внутри AIStrategyManager!
# Точка входа — только через manager и его parallel_step.
# ==============================================================

from config import Config
from telegram_bot import TelegramBot
from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from engine_utils import EngineUtils
from validation_service import ValidationService
from ai_strategy_manager import AIStrategyManager
from freedom_manager import FreedomManager
from ws_price_feed import WSPriceFeed
from market_data_manager import MarketDataManager
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
        # CYCLIC DEPS: FREEDOM MANAGER <-> AI STRATEGY MANAGER
        # ------------------------------------------------------------
        self.freedom_manager = FreedomManager(self.config, None)
        print("[DEBUG] DependencyContainer: self.analyzer before manager =", repr(self.analyzer), type(self.analyzer))
        self.ai_manager = AIStrategyManager(
            self.freedom_manager,
            self.config,
            self.analyzer,
            portfolio_baseline=None,      # portfolio создаётся внутри самого менеджера!
            portfolio_experiment=None
        )
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
        # AB TESTING ENGINE (заводится на тот же портфель если нужно сравнение)
        # ------------------------------------------------------------
        self.ab_engine = ABTestingEngine(
            self.config, self.analyzer, initial_balance=300,
            # Передача None (пусть тест создает сам или не мешает production портфелям)
            portfolio_baseline=None,
            portfolio_experiment=None
        )

        # ------------------------------------------------------------
        # TRADING ENGINE (весь routing через manager!)
        # ------------------------------------------------------------
        self.trading_engine = TradingEngine(
            self.config,
            self.ai_manager,
            self.analyzer,
            None,    # portfolio теперь не нужен — manager всё решает!
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
        self.heartbeat = HeartbeatBuilder(
            self,
            self.ai_manager.baseline_strategy,
            self.ai_manager.experimental_strategy
        )

        self.trading_loop = TradingLoop(
            self.config,
            self.ab_engine,
            self.telegram_bot,
            self.heartbeat,
            self.market_data
        )

        print("[DEBUG] DependencyContainer initialization complete.")
