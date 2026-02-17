"""
GRVT Executor - Order Execution and Exchange Interface.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path to find pysdk when running from source checkout.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from pysdk.grvt_ccxt import GrvtCcxt
from pysdk.grvt_ccxt_env import GrvtEnv


class GRVTExecutor:
    """
    Executor for GRVT Exchange operations.

    Handles authentication, order placement, and position management.
    """

    def __init__(self, config: Any, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        self.api_key = self._get_config("GRVT_API_KEY")
        self.private_key = self._get_config("GRVT_PRIVATE_KEY")
        self.trading_account_id = self._get_config("GRVT_TRADING_ACCOUNT_ID")
        self.sub_account_id = self._get_config("GRVT_SUB_ACCOUNT_ID")
        self.env_str = self._get_config("GRVT_ENV")

        self.client: Optional[GrvtCcxt] = None
        self._markets_cache: Dict[str, Dict[str, Any]] = {}
        self.initialize_client()

    def _get_config(self, key: str) -> Any:
        """Get configuration value from config object."""
        if hasattr(self.config, key):
            return getattr(self.config, key)
        if isinstance(self.config, dict):
            return self.config.get(key)
        if hasattr(self.config, "get"):
            # Dict-like fallback.
            return self.config.get(key)
        raise ValueError(f"Config missing required field: {key}")

    def _cfg_get(self, section: str, key: str, default: Any) -> Any:
        """Best-effort section/key config accessor with default fallback."""
        if hasattr(self.config, "get"):
            try:
                return self.config.get(section, key, default)
            except TypeError:
                pass
        if isinstance(self.config, dict):
            return self.config.get(section, {}).get(key, default)
        return default

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        """Parse number-like values and normalize GRVT fixed-point prices when needed."""
        if value is None:
            return None
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return None
        if parsed <= 0:
            return None

        # GRVT payloads may encode prices in 1e9 fixed point in some endpoints.
        if parsed >= 1_000_000_000:
            scaled = parsed / 1_000_000_000
            if scaled > 0:
                return scaled
        return parsed

    @staticmethod
    def _normalize_ticker_payload(response: Any) -> Dict[str, Any]:
        """Normalize ticker response into a single dict."""
        if isinstance(response, list):
            return response[0] if response and isinstance(response[0], dict) else {}

        if isinstance(response, dict):
            if isinstance(response.get("result"), list):
                result = response["result"]
                return result[0] if result and isinstance(result[0], dict) else {}
            if isinstance(response.get("result"), dict):
                return response["result"]
            return response

        return {}

    def initialize_client(self) -> None:
        """Initialize the GRVT CCXT client."""
        try:
            env = GrvtEnv(self.env_str)
            params = {
                "api_key": self.api_key,
                "trading_account_id": self.trading_account_id,
                "private_key": self.private_key,
            }
            # Keep SDK logs quiet in normal runs; full detail is available in DEBUG mode.
            sdk_logger = logging.getLogger(f"{self.logger.name}.sdk")
            sdk_logger.handlers = list(self.logger.handlers)
            sdk_logger.propagate = False
            sdk_logger.setLevel(logging.DEBUG if self.logger.isEnabledFor(logging.DEBUG) else logging.WARNING)

            self.client = GrvtCcxt(env, sdk_logger, parameters=params)
            self.logger.info("Initialized GRVT client for env: %s", self.env_str)
        except Exception as exc:
            self.logger.error("Failed to initialize GRVT client: %s", exc)
            raise

    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """Fetch account summary for the sub-account."""
        try:
            assert self.client is not None
            return self.client.fetch_balance()
        except Exception as exc:
            self.logger.error("Error fetching account summary: %s", exc)
            return None

    def _fetch_ticker_payload(self, symbol: str) -> Dict[str, Any]:
        assert self.client is not None
        ticker_response = self.client.fetch_ticker(symbol)
        payload = self._normalize_ticker_payload(ticker_response)
        if not payload and isinstance(ticker_response, dict) and "info" in ticker_response:
            payload = self._normalize_ticker_payload(ticker_response.get("info"))
        return payload

    def get_reference_price(self, symbol: str, side: str) -> Optional[float]:
        """
        Get pre-trade reference price.

        Price chain:
        - buy: best_ask
        - sell: best_bid
        - fallback: last_price -> mark_price
        """
        try:
            payload = self._fetch_ticker_payload(symbol)
            if not payload:
                return None

            side = str(side).lower()
            chain: List[str] = []
            if side == "buy":
                chain.extend(["best_ask_price", "ask", "bestAsk"])
            elif side == "sell":
                chain.extend(["best_bid_price", "bid", "bestBid"])

            chain.extend(["last", "last_price", "close", "mark_price", "mark", "mid_price"])

            for key in chain:
                price = self._to_float(payload.get(key))
                if price is not None:
                    return price

            return None
        except Exception as exc:
            self.logger.error("Error fetching reference price for %s: %s", symbol, exc)
            return None

    def get_market_price(self, symbol: str) -> float:
        """Get current market price for a symbol."""
        try:
            payload = self._fetch_ticker_payload(symbol)
            if payload:
                for key in ("last", "last_price", "close", "mark_price", "mark", "mid_price"):
                    price = self._to_float(payload.get(key))
                    if price is not None:
                        return price
            return 0.0
        except Exception as exc:
            self.logger.error("Error fetching ticker for %s: %s", symbol, exc)
            return 0.0

    def _load_markets(self) -> Dict[str, Dict[str, Any]]:
        assert self.client is not None

        markets: Dict[str, Dict[str, Any]] = {}
        try:
            loaded = self.client.load_markets()
            if isinstance(loaded, dict):
                markets.update(loaded)
        except Exception as exc:
            self.logger.warning("load_markets failed: %s", exc)

        if not markets:
            try:
                fetched = self.client.fetch_markets()
                if isinstance(fetched, list):
                    markets = {
                        str(item.get("instrument")): item
                        for item in fetched
                        if isinstance(item, dict) and item.get("instrument")
                    }
            except Exception as exc:
                self.logger.warning("fetch_markets failed: %s", exc)

        if markets:
            self._markets_cache = markets
        return self._markets_cache

    def get_market_limits(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get market metadata including min_qty (from min_size)."""
        try:
            markets = self._markets_cache or self._load_markets()
            market = markets.get(symbol) if isinstance(markets, dict) else None
            if not market:
                return None

            min_qty = self._to_float(market.get("min_size"))
            tick_size = self._to_float(market.get("tick_size"))
            base_decimals = market.get("base_decimals")
            try:
                if base_decimals is not None:
                    base_decimals = int(base_decimals)
            except (TypeError, ValueError):
                base_decimals = None

            return {
                "symbol": symbol,
                "min_qty": min_qty,
                "tick_size": tick_size,
                "base_decimals": base_decimals,
                "raw": market,
            }
        except Exception as exc:
            self.logger.error("Error fetching market limits for %s: %s", symbol, exc)
            return None

    @staticmethod
    def _normalize_orderbook_levels(levels: Any) -> List[Tuple[float, float]]:
        normalized: List[Tuple[float, float]] = []
        if not isinstance(levels, list):
            return normalized

        for level in levels:
            if not isinstance(level, (list, tuple)) or len(level) < 2:
                continue
            try:
                price = float(level[0])
                qty = float(level[1])
            except (TypeError, ValueError):
                continue
            if price <= 0 or qty <= 0:
                continue
            normalized.append((price, qty))
        return normalized

    def get_order_book(self, symbol: str, limit: int = 20) -> Optional[Dict[str, Any]]:
        """Fetch normalized orderbook (ccxt-like bids/asks)."""
        try:
            assert self.client is not None
            limit = max(1, int(limit))
            try:
                response = self.client.fetch_order_book(symbol, limit=limit)
            except TypeError:
                response = self.client.fetch_order_book(symbol)

            payload = response
            if isinstance(response, dict) and "result" in response:
                payload = response["result"]
            if not isinstance(payload, dict):
                return None

            bids = self._normalize_orderbook_levels(payload.get("bids"))
            asks = self._normalize_orderbook_levels(payload.get("asks"))
            if not bids and not asks:
                return None
            return {"bids": bids, "asks": asks, "raw": payload}
        except Exception as exc:
            self.logger.error("Error fetching order book for %s: %s", symbol, exc)
            return None

    @staticmethod
    def _available_qty_in_band(
        order_book: Dict[str, Any],
        close_side: str,
        reference_price: float,
        max_slippage_bps: int,
    ) -> float:
        """Compute available opposing-book quantity within slippage band."""
        close_side = str(close_side).lower()
        if close_side == "buy":
            levels = order_book.get("asks", [])
            max_price = reference_price * (1.0 + max(0.0, float(max_slippage_bps)) / 10_000.0)
            return sum(qty for price, qty in levels if price <= max_price)
        if close_side == "sell":
            levels = order_book.get("bids", [])
            min_price = reference_price * (1.0 - max(0.0, float(max_slippage_bps)) / 10_000.0)
            return sum(qty for price, qty in levels if price >= min_price)
        return 0.0

    @staticmethod
    def _apply_qty_precision(qty: float, base_decimals: Optional[int]) -> float:
        if base_decimals is None:
            return qty
        try:
            precision = max(0, int(base_decimals))
        except (TypeError, ValueError):
            return qty
        return round(qty, precision)

    def set_leverage(self, symbol: str, leverage: int) -> Optional[Dict[str, Any]]:
        """
        Set leverage for a symbol when supported.

        Note: May be unsupported by API and need manual web configuration.
        """
        try:
            assert self.client is not None
            self.logger.info("Attempting to set leverage %sx for %s", leverage, symbol)
            if hasattr(self.client, "set_leverage") and callable(self.client.set_leverage):
                result = self.client.set_leverage(leverage, symbol)
                self.logger.info("Set leverage response: %s", result)
                return result
            self.logger.warning("set_leverage not available in client")
            return None
        except Exception as exc:
            self.logger.error("Error setting leverage: %s", exc)
            import traceback

            self.logger.error(traceback.format_exc())
            return None

    def get_current_leverage(self, symbol: Optional[str] = None) -> Optional[Any]:
        """
        Fetch leverage information when supported by the exchange client.
        """
        try:
            assert self.client is not None
            params = {"sub_account_id": self.sub_account_id}

            if symbol:
                if hasattr(self.client, "fetch_leverage") and callable(self.client.fetch_leverage):
                    try:
                        return self.client.fetch_leverage(symbol, params=params)
                    except TypeError:
                        return self.client.fetch_leverage(symbol)

                if hasattr(self.client, "fetch_leverages") and callable(self.client.fetch_leverages):
                    try:
                        return self.client.fetch_leverages([symbol], params=params)
                    except TypeError:
                        return self.client.fetch_leverages([symbol])

                if hasattr(self.client, "fetch_positions") and callable(self.client.fetch_positions):
                    try:
                        return self.client.fetch_positions([symbol], params=params)
                    except TypeError:
                        return self.client.fetch_positions([symbol])
            else:
                if hasattr(self.client, "fetch_leverages") and callable(self.client.fetch_leverages):
                    try:
                        return self.client.fetch_leverages(params=params)
                    except TypeError:
                        return self.client.fetch_leverages()

                if hasattr(self.client, "fetch_positions") and callable(self.client.fetch_positions):
                    try:
                        return self.client.fetch_positions(params=params)
                    except TypeError:
                        return self.client.fetch_positions()

            self.logger.warning("Client does not expose leverage query methods")
            return None
        except Exception as exc:
            self.logger.error("Error fetching leverage info: %s", exc)
            import traceback

            self.logger.error(traceback.format_exc())
            return None

    def place_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        leverage: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Place a market order.

        client_order_id is forwarded to exchange for idempotency.
        """
        try:
            assert self.client is not None
            req_params: Dict[str, Any] = {"sub_account_id": self.sub_account_id}
            if client_order_id is not None:
                req_params["client_order_id"] = str(client_order_id)
            if params:
                req_params.update(params)

            order = self.client.create_order(
                symbol=symbol,
                order_type="market",
                side=side,
                amount=amount,
                params=req_params,
            )
            return self._handle_order_response(order, "market")
        except Exception as exc:
            self.logger.error("Error placing market order: %s", exc)
            import traceback

            self.logger.error(traceback.format_exc())
            return None

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        leverage: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        client_order_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Place a limit order."""
        try:
            assert self.client is not None
            req_params: Dict[str, Any] = {"sub_account_id": self.sub_account_id}
            if client_order_id is not None:
                req_params["client_order_id"] = str(client_order_id)
            if params:
                req_params.update(params)

            order = self.client.create_order(
                symbol=symbol,
                order_type="limit",
                side=side,
                amount=amount,
                price=price,
                params=req_params,
            )
            return self._handle_order_response(order, "limit")
        except Exception as exc:
            self.logger.error("Error placing limit order: %s", exc)
            import traceback

            self.logger.error(traceback.format_exc())
            return None

    def _handle_order_response(
        self,
        order_response: Optional[Dict[str, Any]],
        order_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Validate and normalize the order response."""
        if not order_response:
            return None

        if "code" in order_response and order_response["code"] != 0:
            if order_response.get("status") != 200 and "message" in order_response:
                self.logger.error("Order failed: %s", order_response)
                return None

        result = order_response.get("result", {})
        if isinstance(result, dict) and "order_id" in result:
            order_response["id"] = result["order_id"]
            order_response["type"] = order_type
        elif "order_id" in order_response:
            order_response["id"] = order_response["order_id"]
            order_response["type"] = order_type

        if "id" in order_response:
            self.logger.info("%s order placed: %s", order_type.capitalize(), order_response["id"])
            return order_response

        self.logger.warning("Order placed but ID not found in response: %s", order_response)
        return order_response

    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch positions for current sub-account."""
        try:
            assert self.client is not None
            params = {"sub_account_id": self.sub_account_id}
            symbols = [symbol] if symbol else []
            try:
                response = self.client.fetch_positions(symbols, params=params)
            except TypeError:
                response = self.client.fetch_positions(symbols)
            if isinstance(response, list):
                return response
            return []
        except Exception as exc:
            self.logger.error("Error fetching positions: %s", exc)
            return []

    @staticmethod
    def _extract_position_size(position: Dict[str, Any]) -> float:
        for key in ("contracts", "size", "position_size", "net_size", "qty", "quantity"):
            if key in position:
                try:
                    return float(position[key])
                except (TypeError, ValueError):
                    continue
        info = position.get("info")
        if isinstance(info, dict):
            for key in ("contracts", "size", "position_size", "net_size", "qty", "quantity"):
                if key in info:
                    try:
                        return float(info[key])
                    except (TypeError, ValueError):
                        continue
        return 0.0

    @staticmethod
    def _extract_position_side(position: Dict[str, Any], size: float) -> str:
        for key in ("side", "position_side"):
            value = str(position.get(key, "")).lower()
            if value in {"long", "buy"}:
                return "buy"
            if value in {"short", "sell"}:
                return "sell"
        return "buy" if size > 0 else "sell"

    def get_open_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Return normalized open position for symbol, if any."""
        positions = self.get_positions(symbol=symbol)
        best: Optional[Dict[str, Any]] = None
        best_qty = 0.0

        for position in positions:
            instrument = position.get("instrument") or position.get("symbol")
            if instrument and instrument != symbol:
                continue

            size = self._extract_position_size(position)
            qty = abs(size)
            if qty <= 0:
                continue
            if qty <= best_qty:
                continue

            best_qty = qty
            best = {
                "symbol": symbol,
                "side": self._extract_position_side(position, size),
                "amount_base": qty,
                "raw": position,
            }

        return best

    def close_position_adaptive(
        self,
        symbol: str,
        side: str,
        remaining_qty: float,
        *,
        config: Any,
        client_order_id_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Close position with adaptive orderbook-aware reduce-only market slices.

        This flow is finite-state and always exits due to one of:
        success, retry cap, duration cap, or no-progress cap.
        """
        def cfg_get(section: str, key: str, default: Any) -> Any:
            if hasattr(config, "get"):
                try:
                    return config.get(section, key, default)
                except TypeError:
                    pass
            if isinstance(config, dict):
                return config.get(section, {}).get(key, default)
            return default

        start_ts = time.time()
        attempts = 0
        orders_sent = 0
        no_progress_retries = 0

        close_side = str(side).lower()
        if close_side not in {"buy", "sell"}:
            return {
                "success": False,
                "code": "CLOSE_INVALID_SIDE",
                "remaining_qty": float(max(0.0, remaining_qty)),
                "attempts": attempts,
                "orders_sent": orders_sent,
                "elapsed_seconds": 0.0,
            }

        tolerance = float(cfg_get("execution", "position_qty_tolerance", 0.000001))
        max_retries = int(cfg_get("execution", "close_max_retries", 20))
        max_duration_seconds = int(cfg_get("execution", "close_max_duration_seconds", 90))
        close_no_progress_retries = int(cfg_get("execution", "close_no_progress_retries", 3))
        close_retry_interval_seconds = int(cfg_get("execution", "close_retry_interval_seconds", 2))
        max_slippage_bps = int(cfg_get("execution", "max_slippage_bps", 20))
        liquidity_usage_pct = float(cfg_get("execution", "liquidity_usage_pct", 0.20))
        orderbook_levels = int(cfg_get("execution", "orderbook_levels", 20))
        min_slice_qty = float(cfg_get("execution", "close_min_slice_qty", 0.01))

        max_retries = max(1, max_retries)
        max_duration_seconds = max(1, max_duration_seconds)
        close_no_progress_retries = max(1, close_no_progress_retries)
        close_retry_interval_seconds = max(1, close_retry_interval_seconds)
        orderbook_levels = max(1, orderbook_levels)
        liquidity_usage_pct = min(max(liquidity_usage_pct, 0.01), 1.0)
        min_slice_qty = max(0.0, min_slice_qty)

        remaining_qty = max(0.0, float(remaining_qty))
        previous_remaining = remaining_qty

        while remaining_qty > tolerance:
            elapsed = time.time() - start_ts
            if attempts >= max_retries:
                return {
                    "success": False,
                    "code": "CLOSE_TIMEOUT",
                    "remaining_qty": remaining_qty,
                    "attempts": attempts,
                    "orders_sent": orders_sent,
                    "elapsed_seconds": elapsed,
                }
            if elapsed >= max_duration_seconds:
                return {
                    "success": False,
                    "code": "CLOSE_TIMEOUT",
                    "remaining_qty": remaining_qty,
                    "attempts": attempts,
                    "orders_sent": orders_sent,
                    "elapsed_seconds": elapsed,
                }

            open_position = self.get_open_position(symbol)
            if not open_position:
                return {
                    "success": True,
                    "code": "CLOSE_SUCCESS",
                    "remaining_qty": 0.0,
                    "attempts": attempts,
                    "orders_sent": orders_sent,
                    "elapsed_seconds": elapsed,
                }

            live_qty = abs(float(open_position.get("amount_base", 0.0)))
            if live_qty <= tolerance:
                return {
                    "success": True,
                    "code": "CLOSE_SUCCESS",
                    "remaining_qty": 0.0,
                    "attempts": attempts,
                    "orders_sent": orders_sent,
                    "elapsed_seconds": elapsed,
                }
            remaining_qty = live_qty
            open_side = str(open_position.get("side", "")).lower()
            close_side = "sell" if open_side == "buy" else "buy"

            reference_price = self.get_reference_price(symbol, close_side)
            order_book = self.get_order_book(symbol, limit=orderbook_levels)
            if reference_price is None or reference_price <= 0 or not order_book:
                attempts += 1
                no_progress_retries += 1
                if no_progress_retries >= close_no_progress_retries:
                    return {
                        "success": False,
                        "code": "CLOSE_NO_PROGRESS",
                        "remaining_qty": remaining_qty,
                        "attempts": attempts,
                        "orders_sent": orders_sent,
                        "elapsed_seconds": time.time() - start_ts,
                    }
                time.sleep(close_retry_interval_seconds)
                continue

            available_qty = self._available_qty_in_band(
                order_book,
                close_side=close_side,
                reference_price=float(reference_price),
                max_slippage_bps=max_slippage_bps,
            )
            if available_qty <= 0:
                attempts += 1
                no_progress_retries += 1
                if no_progress_retries >= close_no_progress_retries:
                    return {
                        "success": False,
                        "code": "CLOSE_NO_PROGRESS",
                        "remaining_qty": remaining_qty,
                        "attempts": attempts,
                        "orders_sent": orders_sent,
                        "elapsed_seconds": time.time() - start_ts,
                    }
                time.sleep(close_retry_interval_seconds)
                continue

            if available_qty >= remaining_qty:
                target_qty = remaining_qty
            else:
                target_qty = max(min_slice_qty, available_qty * liquidity_usage_pct)
                target_qty = min(target_qty, remaining_qty)

            limits = self.get_market_limits(symbol) or {}
            min_qty_value = limits.get("min_qty")
            min_qty = float(min_qty_value) if min_qty_value not in (None, "", 0) else 0.0
            base_decimals = limits.get("base_decimals")
            target_qty = self._apply_qty_precision(float(target_qty), base_decimals)

            if target_qty <= tolerance:
                attempts += 1
                no_progress_retries += 1
                if no_progress_retries >= close_no_progress_retries:
                    return {
                        "success": False,
                        "code": "CLOSE_NO_PROGRESS",
                        "remaining_qty": remaining_qty,
                        "attempts": attempts,
                        "orders_sent": orders_sent,
                        "elapsed_seconds": time.time() - start_ts,
                    }
                time.sleep(close_retry_interval_seconds)
                continue

            if min_qty > 0 and target_qty < min_qty:
                if remaining_qty <= (min_qty + tolerance):
                    target_qty = remaining_qty
                else:
                    attempts += 1
                    no_progress_retries += 1
                    if no_progress_retries >= close_no_progress_retries:
                        return {
                            "success": False,
                            "code": "CLOSE_INCOMPLETE_THIN_BOOK",
                            "remaining_qty": remaining_qty,
                            "attempts": attempts,
                            "orders_sent": orders_sent,
                            "elapsed_seconds": time.time() - start_ts,
                        }
                    time.sleep(close_retry_interval_seconds)
                    continue

            attempts += 1
            order_id_seed = int(time.time() * 1000) if client_order_id_seed is None else int(client_order_id_seed)
            client_order_id = str((order_id_seed + attempts + orders_sent) % 2_147_483_647)
            response = self.place_market_order(
                symbol=symbol,
                side=close_side,
                amount=float(target_qty),
                params={"reduce_only": True},
                client_order_id=client_order_id,
            )

            if response:
                orders_sent += 1
            else:
                no_progress_retries += 1
                if no_progress_retries >= close_no_progress_retries:
                    return {
                        "success": False,
                        "code": "CLOSE_NO_PROGRESS",
                        "remaining_qty": remaining_qty,
                        "attempts": attempts,
                        "orders_sent": orders_sent,
                        "elapsed_seconds": time.time() - start_ts,
                    }

            time.sleep(close_retry_interval_seconds)
            latest_position = self.get_open_position(symbol)
            latest_remaining = (
                abs(float(latest_position.get("amount_base", 0.0)))
                if latest_position
                else 0.0
            )

            if latest_remaining <= tolerance:
                return {
                    "success": True,
                    "code": "CLOSE_SUCCESS",
                    "remaining_qty": 0.0,
                    "attempts": attempts,
                    "orders_sent": orders_sent,
                    "elapsed_seconds": time.time() - start_ts,
                }

            if previous_remaining - latest_remaining > tolerance:
                no_progress_retries = 0
            else:
                no_progress_retries += 1
                if no_progress_retries >= close_no_progress_retries:
                    return {
                        "success": False,
                        "code": "CLOSE_NO_PROGRESS",
                        "remaining_qty": latest_remaining,
                        "attempts": attempts,
                        "orders_sent": orders_sent,
                        "elapsed_seconds": time.time() - start_ts,
                    }
            previous_remaining = latest_remaining
            remaining_qty = latest_remaining

        return {
            "success": True,
            "code": "CLOSE_SUCCESS",
            "remaining_qty": 0.0,
            "attempts": attempts,
            "orders_sent": orders_sent,
            "elapsed_seconds": time.time() - start_ts,
        }

    def flatten_all_positions(self, symbol: str) -> bool:
        """
        Flatten open position using adaptive reduce-only close policy.
        """
        open_position = self.get_open_position(symbol)
        if not open_position:
            return False

        open_side = str(open_position.get("side", "")).lower()
        close_side = "sell" if open_side == "buy" else "buy"
        amount = abs(float(open_position.get("amount_base", 0.0)))
        if amount <= 0:
            return False

        self.logger.warning(
            "Flattening position via adaptive close: symbol=%s qty=%s close_side=%s",
            symbol,
            amount,
            close_side,
        )
        result = self.close_position_adaptive(
            symbol=symbol,
            side=close_side,
            remaining_qty=amount,
            config=self.config,
        )
        if not result.get("success"):
            self.logger.error(
                "Adaptive flatten failed: code=%s remaining_qty=%s attempts=%s",
                result.get("code"),
                result.get("remaining_qty"),
                result.get("attempts"),
            )
            return False
        return True

    def close_all_positions(self, symbol: str) -> None:
        """Backward-compatible alias for flatten_all_positions."""
        self.flatten_all_positions(symbol)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> Any:
        """
        Fetch OHLCV (candlestick) data.

        Returns:
            List[ [timestamp_ms, open, high, low, close, volume], ... ]
        """
        try:
            assert self.client is not None
            if not hasattr(self.client, "fetch_ohlcv"):
                self.logger.error("Client does not support fetch_ohlcv")
                return []

            response = self.client.fetch_ohlcv(symbol, timeframe, limit=limit)

            if isinstance(response, dict) and "result" in response:
                candidates = response["result"]
                ohlcv_list = []
                for candle in candidates:
                    ts_ms = int(candle.get("open_time", 0)) / 1_000_000  # ns -> ms
                    o = float(candle.get("open", 0))
                    h = float(candle.get("high", 0))
                    l = float(candle.get("low", 0))
                    c_price = float(candle.get("close", 0))
                    volume = float(candle.get("volume", candle.get("volume_u", 0)))
                    ohlcv_list.append([ts_ms, o, h, l, c_price, volume])
                ohlcv_list.sort(key=lambda x: x[0])
                return ohlcv_list

            if isinstance(response, list):
                return response

            self.logger.warning("Unexpected OHLCV response format: %s", type(response))
            return []
        except Exception as exc:
            self.logger.error("Error fetching OHLCV: %s", exc)
            import traceback

            self.logger.error(traceback.format_exc())
            return []
