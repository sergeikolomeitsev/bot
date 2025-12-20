# ============================================================
# CONFIG v9.3 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Единый конфигурационный модуль:
# - API настройки
# - Trading настройки
# - Telegram настройки
# - Logging настройки
# - WebSocket параметры
# Все значения могут быть переопределены через .env
# ============================================================

import os
from dataclasses import dataclass
from pathlib import Path

# ------------------------------------------------------------
# LOAD .env (если присутствует)
# ------------------------------------------------------------
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(">>> .env LOADED FROM:", env_path)
else:
    print(">>> .env NOT FOUND at:", env_path)
print(">>> ENV CHECK: TELEGRAM_TOKEN =", repr(os.getenv('TELEGRAM_TOKEN')))
print(">>> ENV CHECK: TELEGRAM_CHAT_ID =", repr(os.getenv('TELEGRAM_CHAT_ID')))


# ============================================================
# API SETTINGS
# ============================================================
@dataclass
class APISettings:
    telegram_token: str = os.getenv("TELEGRAM_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # 🔥 NEW (фикс для WSPriceFeed)
    use_testnet: bool = os.getenv("USE_TESTNET", "false").lower() == "true"


# ============================================================
# TRADING SETTINGS
# ============================================================
@dataclass
class TradingSettings:
    default_symbol: str = os.getenv("DEFAULT_SYMBOL", "BTCUSDT")
    trading_cycle_seconds: int = int(os.getenv("TRADING_CYCLE", "60"))

    # 🔥 NEW — параметр для логирования snapshot
    snapshot_interval_seconds: int = 300

    symbols: list = None

    def __post_init__(self):
        raw = os.getenv(
            "SYMBOLS",
            "BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT,DOGEUSDT,AVAXUSDT"
        )
        self.symbols = raw.replace(" ", "").split(",")

    monitoring_interval_minutes: int = int(os.getenv("MONITOR_INTERVAL", "1"))


# ============================================================
# LOGGING SETTINGS
# ============================================================
@dataclass
class LoggingSettings:
    log_to_file: bool = os.getenv("LOG_TO_FILE", "true").lower() == "true"
    log_file_path: str = os.getenv("LOG_FILE_PATH", "logs/bot.log")
    level: str = os.getenv("LOG_LEVEL", "INFO")


# ============================================================
# WS FEED SETTINGS
# (оставлены для совместимости — не ломаем архитектуру)
# ============================================================
@dataclass
class WSSettings:
    url_main = "ws://<your-server-ip>:8765/relay"
    url_test = "ws://<your-server-ip>:8765/test-relay"  # Добавлена строка


# ============================================================
# ROOT CONFIG OBJECT
# ============================================================
class Config:
    """
    Единый объект конфигурации v9.3
    """

    def __init__(self):
        self.api = APISettings()
        self.trading = TradingSettings()
        self.logging = LoggingSettings()
        self.ws = WSSettings()

        # Корневая директория проекта
        self.root_path = Path(__file__).resolve().parent

    # --------------------------------------------------------
    # PUBLIC — GET WS URL
    # --------------------------------------------------------
    def get_ws_url(self) -> str:
        """
        Возвращает правильный WS URL, основываясь на APISettings.use_testnet.
        Только так твой новый WSPriceFeed будет работать корректно.
        """
        return self.ws.url_test if self.api.use_testnet else self.ws.url_main


config = Config()