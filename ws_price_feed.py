# ============================================================
# WS PRICE FEED v9.3 — Stable Version with Dead-Feed Protection
# ------------------------------------------------------------
# ✔ Stable reconnect loop
# ✔ Filters empty & zero prices
# ✔ Dead-feed detection (no updates)
# ✔ is_alive() used by TradingLoop for safety
# ✔ Thread-safe updates
# ============================================================

import logging
import time
import json
import websocket
import threading
import ssl   # <-- added for SSL fix


class WSPriceFeed:
    """
    WebSocket price feed for Bybit SPOT.
    Provides:
        - latest prices in dict
        - last update timestamp
        - dead-feed detection
    """

    def __init__(self, config):
        self.logger = logging.getLogger("WSPriceFeed")
        self.logger.info("🌐 WSPriceFeed v9.3 initialized")

        self.cfg = config

        # latest prices: {"BTCUSDT": 91350.1, ...}
        self.prices = {}

        # timestamp of last received update
        self.last_update = None

        # if no messages for this number of seconds → WS considered dead
        self.dead_interval = 20

        # ------------------------------------------------------------
        # Endpoint selection
        # ------------------------------------------------------------
        self.ws_url = (
            "wss://stream.bybit.com/v5/public/spot"
            if not config.api.use_testnet else
            "wss://stream-testnet.bybit.com/v5/public/spot"
        )

        # background WS thread
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    # =====================================================================
    # PUBLIC API
    # =====================================================================

    def get_prices(self):
        """Return last valid price snapshot (used by MarketDataManager)."""
        return dict(self.prices)

    def is_alive(self):
        """
        WS is alive if:
        - at least one update happened
        - last update was not too long ago
        """
        if self.last_update is None:
            return False
        return (time.time() - self.last_update) < self.dead_interval

    # =====================================================================
    # INTERNAL — MAIN LOOP
    # =====================================================================

    def _run(self):
        """
        Infinite reconnect loop.
        If WS dies → auto reconnect.
        """
        while True:
            try:
                self._connect()
            except Exception as e:
                self.logger.error(f"❌ WS main-loop exception: {e}")
            time.sleep(2)

    # =====================================================================
    # INTERNAL — CONNECT + SUBSCRIBE
    # =====================================================================

    def _connect(self):
        """
        Opens the WebSocket connection and runs it until failure.
        """
        self.logger.info(f"🔌 Connecting to WS: {self.ws_url}")

        ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_message=self.on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        # ------------------------------------------------------------
        # SSL FIX for macOS / Python / websocket-client
        # ------------------------------------------------------------
        ws.run_forever(
            ping_interval=20,
            ping_timeout=10,
            sslopt={
                "cert_reqs": ssl.CERT_NONE,
                "check_hostname": False,
                "ca_certs": None
            }
        )

    # =====================================================================
    # CALLBACKS
    # =====================================================================

    def _on_open(self, ws):
        """Subscribe to all spot symbols defined in config."""
        self.logger.info("✅ WS connected")

        subs = []
        for sym in self.cfg.trading.symbols:
            subs.append(f"tickers.{sym}")

        if not subs:
            self.logger.error("⚠ No symbols to subscribe")
            return

        msg = {"op": "subscribe", "args": subs}

        try:
            ws.send(json.dumps(msg))
            self.logger.info(f"📡 Subscribed to: {subs}")
        except Exception as e:
            self.logger.error(f"❌ WS subscribe error: {e}")

    # ---------------------------------------------------------------------

    def on_message(self, ws, message):
        """
        Handles incoming Bybit ticker messages passed through relay.
        Example RAW:
        {
            "topic":"tickers.BTCUSDT",
            "data": {
                "symbol": "BTCUSDT",
                "lastPrice": "89789.9",
                ...
            }
        }
        """
        try:
            data = json.loads(message)

            # ignore messages without "data"
            if "data" not in data:
                return

            payload = data["data"]

            # symbol + price
            symbol = payload.get("symbol")
            price_raw = payload.get("lastPrice")

            if not symbol or not price_raw:
                return

            # parse price
            try:
                price = float(price_raw)
                if price <= 0:
                    return
            except:
                return

            # update
            self.prices[symbol] = price
            self.last_update = time.time()

        except Exception as e:
            self.logger.error(f"❌ WS parse error: {e} | RAW={message}")


    # ---------------------------# ============================================================
    # # WS PRICE FEED v9.3 — Stable Version with Dead-Feed Protection
    # # ------------------------------------------------------------
    # # ✔ Stable reconnect loop
    # # ✔ Filters empty & zero prices
    # # ✔ Dead-feed detection (no updates)
    # # ✔ is_alive() used by TradingLoop for safety
    # # ✔ Thread-safe updates
    # # ============================================================
    #
    # import logging
    # import time
    # import json
    # import websocket
    # import threading
    # import ssl   # <-- added for SSL fix
    #
    #
    # class WSPriceFeed:
    #     """
    #     WebSocket price feed for Bybit SPOT.
    #     Provides:
    #         - latest prices in dict
    #         - last update timestamp
    #         - dead-feed detection
    #     """
    #
    #     def __init__(self, config):
    #         self.logger = logging.getLogger("WSPriceFeed")
    #         self.logger.info("🌐 WSPriceFeed v9.3 initialized")
    #
    #         self.cfg = config
    #
    #         # latest prices: {"BTCUSDT": 91350.1, ...}
    #         self.prices = {}
    #
    #         # timestamp of last received update
    #         self.last_update = None
    #
    #         # if no messages for this number of seconds → WS considered dead
    #         self.dead_interval = 20
    #
    #         # ------------------------------------------------------------
    #         # Endpoint selection
    #         # ------------------------------------------------------------
    #         self.ws_url = (
    #             "wss://stream.bybit.com/v5/public/spot"
    #             if not config.api.use_testnet else
    #             "wss://stream-testnet.bybit.com/v5/public/spot"
    #         )
    #
    #         # background WS thread
    #         self.thread = threading.Thread(target=self._run, daemon=True)
    #         self.thread.start()
    #
    #     # =====================================================================
    #     # PUBLIC API
    #     # =====================================================================
    #
    #     def get_prices(self):
    #         """Return last valid price snapshot (used by MarketDataManager)."""
    #         return dict(self.prices)
    #
    #     def is_alive(self):
    #         """
    #         WS is alive if:
    #         - at least one update happened
    #         - last update was not too long ago
    #         """
    #         if self.last_update is None:
    #             return False
    #         return (time.time() - self.last_update) < self.dead_interval
    #
    #     # =====================================================================
    #     # INTERNAL — MAIN LOOP
    #     # =====================================================================
    #
    #     def _run(self):
    #         """
    #         Infinite reconnect loop.
    #         If WS dies → auto reconnect.
    #         """
    #         while True:
    #             try:
    #                 self._connect()
    #             except Exception as e:
    #                 self.logger.error(f"❌ WS main-loop exception: {e}")
    #             time.sleep(2)
    #
    #     # =====================================================================
    #     # INTERNAL — CONNECT + SUBSCRIBE
    #     # =====================================================================
    #
    #     def _connect(self):
    #         """
    #         Opens the WebSocket connection and runs it until failure.
    #         """
    #         self.logger.info(f"🔌 Connecting to WS: {self.ws_url}")
    #
    #         ws = websocket.WebSocketApp(
    #             self.ws_url,
    #             on_open=self._on_open,
    #             on_message=self.on_message,
    #             on_error=self._on_error,
    #             on_close=self._on_close,
    #         )
    #
    #         # ------------------------------------------------------------
    #         # SSL FIX for macOS / Python / websocket-client
    #         # ------------------------------------------------------------
    #         ws.run_forever(
    #             ping_interval=20,
    #             ping_timeout=10,
    #             sslopt={
    #                 "cert_reqs": ssl.CERT_NONE,
    #                 "check_hostname": False,
    #                 "ca_certs": None
    #             }
    #         )
    #
    #     # =====================================================================
    #     # CALLBACKS
    #     # =====================================================================
    #
    #     def _on_open(self, ws):
    #         """Subscribe to all spot symbols defined in config."""
    #         self.logger.info("✅ WS connected")
    #
    #         subs = []
    #         for sym in self.cfg.trading.symbols:
    #             subs.append(f"tickers.{sym}")
    #
    #         if not subs:
    #             self.logger.error("⚠ No symbols to subscribe")
    #             return
    #
    #         msg = {"op": "subscribe", "args": subs}
    #
    #         try:
    #             ws.send(json.dumps(msg))
    #             self.logger.info(f"📡 Subscribed to: {subs}")
    #         except Exception as e:
    #             self.logger.error(f"❌ WS subscribe error: {e}")
    #
    #     # ---------------------------------------------------------------------
    #
    #     def on_message(self, ws, message):
    #         """
    #         Handles incoming WS messages from relay.
    #         Bybit tickers format:
    #         {
    #             "topic": "tickers.BTCUSDT",
    #             "type": "snapshot" or "delta",
    #             "ts": 123456789,
    #             "data": {
    #                 "symbol": "BTCUSDT",
    #                 "lastPrice": "91363.7",
    #                 ... other fields ...
    #             }
    #         }
    #         """
    #         try:
    #             data = json.loads(message)
    #
    #             # Bybit sometimes sends pings or empty payloads
    #             if "data" not in data:
    #                 return
    #
    #             payload = data["data"]
    #
    #             symbol = payload.get("symbol")  # e.g., BTCUSDT
    #             price = float(payload.get("lastPrice", 0))
    #
    #             if symbol and price > 0:
    #                 self.prices[symbol] = price
    #                 self.last_update = time.time()
    #
    #         except Exception as e:
    #             self.logger.error(f"❌ WS parse error: {e} | RAW={message}")
    #
    #     # ---------------------------------------------------------------------
    #
    #     def _on_error(self, ws, error):
    #         self.logger.error(f"❌ WS error: {error}")
    #
    #     # ---------------------------------------------------------------------
    #
    #     def _on_close(self, ws, close_status_code, close_msg):
    #         self.logger.warning(f"⚠ WS closed: {close_status_code} {close_msg}")------------------------------------------

    def _on_error(self, ws, error):
        self.logger.error(f"❌ WS error: {error}")

    # ---------------------------------------------------------------------

    def _on_close(self, ws, close_status_code, close_msg):
        self.logger.warning(f"⚠ WS closed: {close_status_code} {close_msg}")
