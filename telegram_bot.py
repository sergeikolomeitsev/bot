# ============================================================
# TELEGRAM BOT v9.0 — AI PRIME TRADING BOT
# ------------------------------------------------------------
# Функции:
# - отправка текстовых сообщений
# - отправка PNG-графиков equity
# - уведомления об ошибках
# - ежедневные / недельные уведомления
#
# Ограничения:
# - НЕТ бизнес-логики
# - НЕТ теханализа
# - НЕТ стратегии
# - НЕТ торговли
# ============================================================

import logging
import requests
from pathlib import Path


class TelegramBot:
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.logger = logging.getLogger("TelegramBot")

        self.base_url = f"https://api.telegram.org/bot{self.token}"

    # ------------------------------------------------------------
    # INTERNAL — SEND TELEGRAM REQUEST
    # ------------------------------------------------------------
    def _post(self, method: str, data: dict = None, files: dict = None):
        url = f"{self.base_url}/{method}"

        try:
            resp = requests.post(url, data=data, files=files, timeout=10)
            return resp.json()
        except Exception as e:
            self.logger.error(f"Telegram error: {e}", exc_info=True)
            return None

    # ------------------------------------------------------------
    # PUBLIC — SEND TEXT MESSAGE
    # ------------------------------------------------------------
    def send_message(self, text: str):
        data = {
            "chat_id": self.chat_id,
            "text": text
        }
        response = self._post("sendMessage", data=data)
        print(">>> TELEGRAM API RESPONSE:", response)
        if not response or not response.get("ok"):
            self.logger.error(f"Telegram send_message failed: {response}")
        return response

    # ------------------------------------------------------------
    # PUBLIC — SEND PNG IMAGE
    # ------------------------------------------------------------
    def send_photo(self, image_path: str, caption: str = None):
        path = Path(image_path)

        if not path.exists():
            self.logger.error(f"Image not found: {image_path}")
            return None

        with path.open("rb") as img:
            files = {"photo": img}
            data = {"chat_id": self.chat_id}

            if caption:
                data["caption"] = caption

            return self._post("sendPhoto", data=data, files=files)

    # ------------------------------------------------------------
    # PUBLIC — ERROR ALERT
    # ------------------------------------------------------------
    def send_error(self, msg: str):
        text = f"❗ CRITICAL ERROR v9.0:\n{msg}"
        return self.send_message(text)

    # ------------------------------------------------------------
    # PUBLIC — EQUITY REPORT
    # ------------------------------------------------------------
    def send_equity_report(self, image_path: str):
        return self.send_photo(image_path, "📈 Equity Report v9.0")

    # ------------------------------------------------------------
    # PUBLIC — DAILY SUMMARY
    # ------------------------------------------------------------
    def notify_daily(self):
        return self.send_message("📊 Daily summary (v9.0) отправлен.")

    # ------------------------------------------------------------
    # PUBLIC — WEEKLY SUMMARY
    # ------------------------------------------------------------
    def notify_weekly(self):
        return self.send_message("📈 Weekly summary (v9.0) отправлен.")

    def send_heartbeat(self, text: str):
        prefix = "❤️ HEARTBEAT v9.6\n"
        return self.send_message(prefix + text)

