# ============================================================
# DEPENDENCY CONTAINER v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Создаёт и связывает все модули проекта.
# Не содержит бизнес-логики.
# Не запускает Loop.
# Только DI.
# ============================================================

from config import Config
from ws_price_feed import WSPriceFeed
from market_data_manager import MarketDataManager
from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from engine_utils import EngineUtils
from vtr_strategy import VTRStrategy
from heavy_strategy import HeavyStrategy
from ai_strategy_manager import AIStrategyManager
from freedom_manager import FreedomManager
from ab_testing_engine import ABTestingEngine
from portfolio_service import PortfolioService
from trading_engine import TradingEngine
from reporting_engine import ReportingEngine
from telegram_bot import TelegramBot
from trading_loop import TradingLoop
from validation_service import ValidationService
from heartbeat_builder import HeartbeatBuilder


class DependencyContainer:
    """
    DI-контейнер: создаёт все модули и связывает зависимости строго по контракту v9.0.
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
        # AI MANAGER
        # ------------------------------------------------------------
        self.ai_manager = AIStrategyManager(self.config)
        self.ai_manager.set_base_strategy(self.vtr_strategy)

        # ------------------------------------------------------------
        # FREEDOM MANAGER
        # ------------------------------------------------------------
        self.freedom_manager = FreedomManager(self.config, self.ai_manager)

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
            market_data=self.market_data  # <-- FIX v9.6
        )

        # ------------------------------------------------------------
        # REPORTING ENGINE
        # ------------------------------------------------------------
        self.reporting_engine = ReportingEngine(self.telegram_bot)

        # ------------------------------------------------------------
        # TRADING LOOP
        # ------------------------------------------------------------
        # ------------------------------------------------------------
        # TRADING LOOP (fixed for v9.3)
        # ------------------------------------------------------------
        self.trading_loop = TradingLoop(
            self.config,
            self.market_data,       # ← вместо self.market
            self.trading_engine,    # ← вместо self.strategy
            self.portfolio,
            self.telegram_bot
        )

        self.heartbeat = HeartbeatBuilder(self)

    # ------------------------------------------------------------
    # PUBLIC — GET LOOP
    # ------------------------------------------------------------
    def get_loop(self):
        return self.trading_loop

    # ============================================================
    # HEARTBEAT SUMMARY v9.6
    # ============================================================
    def build_heartbeat_summary(self):
        """
        Формирует подробный heartbeat:
        - последний снапшот цен
        - открытые позиции
        - PnL по каждой позиции
        - активная стратегия
        - параметры принятия решений
        """
        md = self.market_data   # MarketDataManager
        engine = self.trading_engine
        portfolio = self.portfolio
        ai = self.ai_manager

        snapshot = md.get_snapshot()
        lines = []

        # --- Header ---
        lines.append("📡 MARKET SNAPSHOT")
        for sym, price in snapshot.items():
            lines.append(f"{sym}: {price}")

        # --- Active strategy ---
        strategy = ai.get_active_strategy()
        lines.append("\n🎯 Active strategy:")
        lines.append(strategy.__class__.__name__ if strategy else "None")

        # --- Portfolio state ---
        lines.append("\n💼 POSITIONS:")
        if portfolio.positions:
            for sym, pos in portfolio.positions.items():
                price = snapshot.get(sym)
                pnl = portfolio.calc_pnl(sym, price) if price else None
                lines.append(
                    f"{sym}: amount={pos['amount']} entry={pos['entry_price']} PnL={pnl}"
                )
        else:
            lines.append("No open positions")

        # --- Indicators from history ---
        lines.append("\n📊 TECHNICAL INDICATORS:")
        for sym in snapshot:
            history = md.get_history(sym)
            if len(history) < 20:
                lines.append(f"{sym}: insufficient history")
                continue

            ema_fast = self.analyzer.ema(history, 5)
            ema_slow = self.analyzer.ema(history, 20)
            rsi_val = self.analyzer.rsi(history, 14)
            gap_val = self.analyzer.gap(history)
            vol = self.analyzer.volatility(history)

            lines.append(
                f"{sym}: EMA5={ema_fast:.2f}, EMA20={ema_slow:.2f}, "
                f"RSI14={rsi_val:.2f}, GAP={gap_val:.5f}, VOL={vol:.5f}"
            )

        return "\n".join(lines)

