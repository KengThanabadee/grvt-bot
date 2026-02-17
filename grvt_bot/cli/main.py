"""
CLI entry point for the GRVT bot.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from grvt_bot.core.alerts import AlertManager
from grvt_bot.core.config import ConfigManager
from grvt_bot.core.executor import GRVTExecutor
from grvt_bot.core.risk import RiskEngine
from grvt_bot.core.runtime_lock import RuntimeLock
from grvt_bot.core.state import StateStore
from grvt_bot.strategies.random_strategy import RandomStrategy
from grvt_bot.utils.logger import setup_logger


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="GRVT Trading Bot - Automated trading for GRVT Exchange"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default="PAXGMeanReversionStrategy",
        choices=["random", "PAXGMeanReversionStrategy"],
        help="Trading strategy to use (default: PAXGMeanReversionStrategy)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="grvt_bot.log",
        help="Path to log file (default: grvt_bot.log)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no real orders)",
    )
    return parser.parse_args()


def seconds_until_next_run(
    interval_minutes: int,
    now: Optional[datetime] = None,
) -> float:
    """
    Return sleep time until the next minute-aligned run.

    interval_minutes defines cadence in minutes (1, 5, 15, ...).
    """
    now = now or datetime.now()
    interval_minutes = max(1, int(interval_minutes))

    next_boundary = now.replace(second=0, microsecond=0)
    if now > next_boundary:
        next_boundary += timedelta(minutes=1)

    minutes_since_midnight = next_boundary.hour * 60 + next_boundary.minute
    remainder = minutes_since_midnight % interval_minutes
    if remainder != 0:
        next_boundary += timedelta(minutes=interval_minutes - remainder)

    return max(0.0, (next_boundary - now).total_seconds()) + 0.05


def seconds_until_data_fetch(
    interval_minutes: int,
    data_close_buffer_seconds: int,
    now: Optional[datetime] = None,
) -> float:
    """Total wait until candle fetch: minute boundary sleep + close buffer."""
    return seconds_until_next_run(interval_minutes, now) + max(0, int(data_close_buffer_seconds))


def timeframe_to_seconds(timeframe: str) -> int:
    """Convert timeframe string (e.g. 1m, 15m, 1h) into seconds."""
    if not timeframe:
        return 60

    raw = str(timeframe).strip().lower()
    if raw.endswith("m"):
        return max(60, int(raw[:-1]) * 60)
    if raw.endswith("h"):
        return max(60, int(raw[:-1]) * 60 * 60)
    if raw.endswith("d"):
        return max(60, int(raw[:-1]) * 24 * 60 * 60)
    return 60


def normalize_side(raw_side: Any) -> Optional[str]:
    """Normalize strategy side values to exchange 'buy'/'sell'."""
    side = str(raw_side).lower()
    if side in {"buy", "long"}:
        return "buy"
    if side in {"sell", "short"}:
        return "sell"
    return None


def should_close_on_opposite_signal(
    open_position: Optional[Dict[str, Any]],
    signal: Optional[Dict[str, Any]],
) -> bool:
    """Return True when signal side is opposite to current open position side."""
    if not isinstance(open_position, dict) or not isinstance(signal, dict):
        return False

    open_side = normalize_side(open_position.get("side"))
    signal_side = normalize_side(signal.get("side"))
    if open_side is None or signal_side is None:
        return False

    return open_side != signal_side


def build_order_params(signal: Dict[str, Any]) -> Optional[Dict[str, float]]:
    """Map strategy signal fields to order params when present."""
    params: Dict[str, float] = {}

    sl_price = signal.get("sl_price")
    if isinstance(sl_price, (int, float)) and sl_price > 0:
        params["stopLossPrice"] = float(sl_price)

    tp_price = signal.get("tp_price")
    if isinstance(tp_price, (int, float)) and tp_price > 0:
        params["takeProfitPrice"] = float(tp_price)

    return params or None


def extract_equity_usdt(account_summary: Optional[Dict[str, Any]]) -> Optional[float]:
    """Best-effort equity extraction from ccxt-like balance response."""
    if not isinstance(account_summary, dict):
        return None

    total = account_summary.get("total")
    if isinstance(total, dict):
        for symbol in ("USDT", "USDC", "USD"):
            value = total.get(symbol)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    pass
        for value in total.values():
            if value is not None:
                try:
                    parsed = float(value)
                    if parsed > 0:
                        return parsed
                except (TypeError, ValueError):
                    continue

    for top_key in ("equity", "account_value", "net_asset_value", "value", "balance"):
        if top_key in account_summary:
            try:
                value = float(account_summary[top_key])
                if value > 0:
                    return value
            except (TypeError, ValueError):
                pass

    info = account_summary.get("info")
    if isinstance(info, dict):
        for key in ("equity", "account_value", "net_asset_value", "value"):
            if key in info:
                try:
                    value = float(info[key])
                    if value > 0:
                        return value
                except (TypeError, ValueError):
                    pass

    result = account_summary.get("result")
    if isinstance(result, dict):
        for key in ("equity", "account_value", "net_asset_value", "value"):
            if key in result:
                try:
                    value = float(result[key])
                    if value > 0:
                        return value
                except (TypeError, ValueError):
                    pass

    return None


def build_client_order_id(loop_count: int) -> str:
    """Build numeric client_order_id for idempotent submissions."""
    return str((int(time.time() * 1000) + int(loop_count)) % 2_147_483_647)


def _utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def run_adaptive_close(
    *,
    executor: GRVTExecutor,
    config: ConfigManager,
    state_store: StateStore,
    state: Dict[str, Any],
    symbol: str,
    open_position: Optional[Dict[str, Any]],
    reason_tag: str,
    dry_run: bool,
    seed: Optional[int] = None,
) -> Tuple[Dict[str, Any], bool, Dict[str, Any]]:
    """Run adaptive close flow and persist close attempt metadata."""
    state["pending_action"] = reason_tag
    state["last_close_attempt_at"] = _utc_now_iso()
    state = state_store.save(state)

    if not open_position:
        result = {
            "success": True,
            "code": "CLOSE_SUCCESS",
            "attempts": 0,
            "remaining_qty": 0.0,
        }
        state["pending_action"] = None
        state["last_close_reason"] = str(result["code"])
        state = state_store.save(state)
        return state, True, result

    side = str(open_position.get("side", "")).lower()
    close_side = "sell" if side == "buy" else "buy"
    qty = abs(float(open_position.get("amount_base", 0.0)))
    if qty <= 0:
        result = {
            "success": True,
            "code": "CLOSE_SUCCESS",
            "attempts": 0,
            "remaining_qty": 0.0,
        }
        state["open_position"] = None
        state["pending_action"] = None
        state["last_close_reason"] = str(result["code"])
        state = state_store.save(state)
        return state, True, result

    if dry_run:
        result = {
            "success": True,
            "code": "DRY_RUN_CLOSE",
            "attempts": 1,
            "remaining_qty": 0.0,
        }
        state["open_position"] = None
    else:
        result = executor.close_position_adaptive(
            symbol=symbol,
            side=close_side,
            remaining_qty=qty,
            config=config,
            client_order_id_seed=seed,
        )
        state["open_position"] = executor.get_open_position(symbol)

    prev_attempts = int(state.get("close_attempt_count", 0) or 0)
    attempts_raw = result.get("attempts", 0)
    try:
        attempts_value = int(str(attempts_raw or 0))
    except (TypeError, ValueError):
        attempts_value = 0
    state["close_attempt_count"] = prev_attempts + max(1, attempts_value)
    state["pending_action"] = None
    state["last_close_reason"] = str(result.get("code", ""))
    state = state_store.save(state)

    return state, bool(result.get("success")), result


def resolve_startup_mismatch_policy(config: ConfigManager) -> str:
    """Resolve startup mismatch policy with backward compatibility fallback."""
    policy = str(config.get("ops", "startup_mismatch_policy", "")).strip().lower()
    if not policy:
        return (
            "halt_only"
            if bool(config.get("ops", "halt_on_reconcile_mismatch", True))
            else "adopt_continue"
        )
    if policy not in {"adopt_continue", "halt_only", "auto_flatten_halt"}:
        return "adopt_continue"
    return policy


def load_strategy(name: str, config: ConfigManager, logger: logging.Logger) -> Any:
    """Instantiate the selected strategy."""
    if name == "random":
        return RandomStrategy(config, logger)

    if name == "PAXGMeanReversionStrategy":
        try:
            from grvt_bot.strategies.paxg_mean_reversion_strategy import (
                PAXGMeanReversionStrategy,
            )
        except ImportError as exc:
            logger.error(
                "Failed to import PAXG strategy. Install optional dependencies: pandas ta"
            )
            raise exc
        return PAXGMeanReversionStrategy(config, logger)

    raise ValueError(f"Unknown strategy: {name}")


def refresh_strategy_data(
    executor: GRVTExecutor,
    strategy: Any,
    symbol: str,
    logger: logging.Logger,
) -> Optional[int]:
    """Fetch latest candles, update strategy if supported, and return latest candle timestamp (ms)."""
    timeframe = str(getattr(strategy, "timeframe", "1m"))
    klines = executor.fetch_ohlcv(symbol, timeframe, limit=100)
    if not klines:
        logger.warning("Failed to fetch OHLCV data")
        return None

    latest_open_ms = int(float(klines[-1][0]))

    if hasattr(strategy, "update_market_data"):
        import pandas as pd

        df = pd.DataFrame(
            klines,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        strategy.update_market_data(df)

    return latest_open_ms


def main() -> int:
    """Main entry point for the trading bot."""
    args = parse_args()
    log_level = getattr(logging, args.log_level)
    logger = setup_logger("grvt_bot", args.log_file, log_level)
    runtime_lock: Optional[RuntimeLock] = None

    logger.info("=" * 60)
    logger.info("GRVT Trading Bot Starting...")
    logger.info("=" * 60)

    try:
        config_path = Path(args.config).resolve()
        logger.info("Loading configuration from: %s", config_path)
        if not config_path.exists():
            logger.error("Config file not found at: %s", config_path)
            logger.info("Create one from config/config.example.yaml")
            return 1

        config = ConfigManager(config_path=str(config_path))
        try:
            config.validate()
        except ValueError as exc:
            logger.error("Invalid configuration: %s", exc)
            return 1

        runtime_lock = RuntimeLock(config.LOCK_FILE, logger)
        try:
            runtime_lock.acquire()
        except RuntimeError as exc:
            logger.error("%s", exc)
            return 1

        logger.info("Environment: %s", config.GRVT_ENV)
        logger.info("Trading Symbol: %s", config.SYMBOL)
        logger.info("Order Size: %s USDT", config.ORDER_SIZE_USDT)
        logger.info("Leverage: %sx", config.LEVERAGE)
        logger.info("Active Track: %s", config.RISK_ACTIVE_TRACK)

        loop_interval_minutes = int(config.MAIN_LOOP_INTERVAL)
        if loop_interval_minutes < 1:
            logger.warning(
                "Invalid trading.loop_interval=%s. Falling back to 1 minute.",
                loop_interval_minutes,
            )
            loop_interval_minutes = 1
        data_close_buffer_seconds = max(0, int(config.DATA_CLOSE_BUFFER_SECONDS))

        if args.dry_run:
            logger.warning("DRY RUN MODE - No real orders will be placed")

        logger.info("Initializing GRVT executor...")
        executor = GRVTExecutor(config, logger)

        logger.info("Initializing strategy: %s", args.strategy)
        strategy = load_strategy(args.strategy, config, logger)
        strategy.initialize()

        risk_engine = RiskEngine(config, logger)
        alert_manager = AlertManager(config, logger)
        state_store = StateStore(config.STATE_FILE, logger)
        state = state_store.load()

        reconcile_result = state_store.reconcile(executor, config.SYMBOL)
        state = reconcile_result.state
        if reconcile_result.mismatch:
            alert_manager.send(
                f"[RECONCILE] Startup mismatch found. Exchange position adopted. reason={reconcile_result.reason}",
                level="warning",
            )
            startup_policy = resolve_startup_mismatch_policy(config)

            if startup_policy == "halt_only":
                state["halted"] = True
                state["halt_reason"] = "startup_reconcile_mismatch"
                state = state_store.save(state)
                alert_manager.send(
                    "[HALT] Halted due to reconcile mismatch at startup (policy=halt_only)",
                    level="error",
                )
            elif startup_policy == "auto_flatten_halt":
                open_position = state.get("open_position")
                state, close_ok, close_result = run_adaptive_close(
                    executor=executor,
                    config=config,
                    state_store=state_store,
                    state=state,
                    symbol=config.SYMBOL,
                    open_position=open_position,
                    reason_tag="startup_auto_flatten",
                    dry_run=args.dry_run,
                    seed=0,
                )
                state["halted"] = True
                result_code = str(close_result.get("code", "CLOSE_UNKNOWN"))
                state["halt_reason"] = f"startup_reconcile_auto_flatten_halt:{result_code}"
                state = state_store.save(state)
                if close_ok:
                    alert_manager.send(
                        "[HALT] Startup mismatch auto-flatten complete (policy=auto_flatten_halt)",
                        level="warning",
                    )
                else:
                    alert_manager.send(
                        f"[HALT] Startup auto-flatten failed: {result_code}",
                        level="error",
                    )
            else:
                alert_manager.send(
                    "[RECONCILE] Policy adopt_continue active; bot will continue with exchange position.",
                    level="info",
                )

        if state.get("open_position") and hasattr(strategy, "current_position"):
            strategy.current_position = dict(state["open_position"])

        account_summary = executor.get_account_summary()
        equity_usdt = extract_equity_usdt(account_summary)
        if state.get("baseline_equity_usdt") is None and equity_usdt is not None:
            state["baseline_equity_usdt"] = equity_usdt
            state = state_store.save(state)
            logger.info("Baseline equity set to %.6f", equity_usdt)

        logger.info("Bot initialized successfully")
        logger.info(
            "Main loop cadence: every %s minute(s), aligned to second 00",
            loop_interval_minutes,
        )
        logger.info(
            "Data close buffer after boundary: %ss",
            data_close_buffer_seconds,
        )

        loop_count = 0
        repeated_error_count = 0
        repeated_error_signature = ""
        repeated_error_last_ts = 0.0
        error_backoff_seconds = max(1, int(config.ERROR_BACKOFF_SECONDS))
        max_repeated_errors = max(1, int(config.MAX_REPEATED_ERRORS))
        repeated_error_window_seconds = max(1, int(config.REPEATED_ERROR_WINDOW_SECONDS))
        timeframe_seconds = timeframe_to_seconds(str(getattr(strategy, "timeframe", "1m")))

        while True:
            try:
                sleep_seconds = seconds_until_next_run(loop_interval_minutes)
                logger.info("Sleeping %.2fs until next minute boundary", sleep_seconds)
                time.sleep(sleep_seconds)

                if data_close_buffer_seconds > 0:
                    logger.info(
                        "Waiting %ss after boundary before candle fetch",
                        data_close_buffer_seconds,
                    )
                    time.sleep(data_close_buffer_seconds)

                loop_count += 1
                state = state_store.load()
                state["last_loop_started_at"] = datetime.utcnow().isoformat()
                state = state_store.save(state)

                logger.info(
                    "Minute cycle #%s started at %s",
                    loop_count,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )

                latest_candle_ms = refresh_strategy_data(executor, strategy, config.SYMBOL, logger)
                if latest_candle_ms is None:
                    alert_manager.send("[DATA] Candle fetch failed, skipping cycle", level="warning")
                    continue

                now_ms = int(time.time() * 1000)
                max_staleness_ms = max(120_000, timeframe_seconds * 2 * 1000)
                if now_ms - latest_candle_ms > max_staleness_ms:
                    alert_manager.send(
                        f"[DATA] Candle stale by {(now_ms - latest_candle_ms)/1000:.1f}s, skipping cycle",
                        level="warning",
                    )
                    continue

                last_candle_ms = state.get("last_candle_open_time_ms")
                if last_candle_ms == latest_candle_ms:
                    logger.info("No new candle since last cycle. Skipping signal evaluation.")
                    continue

                state["last_candle_open_time_ms"] = latest_candle_ms
                state = state_store.save(state)

                account_summary = executor.get_account_summary()
                equity_usdt = extract_equity_usdt(account_summary)

                if state.get("baseline_equity_usdt") is None and equity_usdt is not None:
                    state["baseline_equity_usdt"] = equity_usdt
                    state = state_store.save(state)

                threshold_decision = risk_engine.evaluate_thresholds(
                    current_equity_usdt=equity_usdt,
                    baseline_equity_usdt=state.get("baseline_equity_usdt"),
                )
                if not threshold_decision.allowed and threshold_decision.action in {"flatten_halt", "halt"}:
                    alert_manager.send(
                        f"[RISK] {threshold_decision.code}: {threshold_decision.reason}",
                        level="error",
                    )
                    if threshold_decision.action == "flatten_halt":
                        state, close_ok, close_result = run_adaptive_close(
                            executor=executor,
                            config=config,
                            state_store=state_store,
                            state=state,
                            symbol=config.SYMBOL,
                            open_position=state.get("open_position"),
                            reason_tag="threshold_flatten",
                            dry_run=args.dry_run,
                            seed=loop_count,
                        )
                        if not close_ok:
                            alert_manager.send(
                                f"[RISK] Threshold flatten failed: {close_result.get('code', 'CLOSE_UNKNOWN')}",
                                level="error",
                            )
                    else:
                        state["open_position"] = executor.get_open_position(config.SYMBOL)
                    state["halted"] = True
                    state["halt_reason"] = f"{threshold_decision.code}:{threshold_decision.reason}"
                    state = state_store.save(state)
                    if hasattr(strategy, "current_position"):
                        strategy.current_position = state.get("open_position")
                    continue

                open_position = state.get("open_position")
                if open_position and hasattr(strategy, "check_exit"):
                    current_price = executor.get_market_price(config.SYMBOL)
                    if current_price > 0:
                        exit_signal = strategy.check_exit(current_price, open_position)
                        if exit_signal and exit_signal.get("action") == "close":
                            amount_base = float(open_position.get("amount_base", 0.0))
                            if amount_base <= 0:
                                alert_manager.send(
                                    "[EXIT] Invalid position size in state; clearing local position",
                                    level="warning",
                                )
                                state["open_position"] = None
                                state = state_store.save(state)
                                if hasattr(strategy, "current_position"):
                                    strategy.current_position = None
                                continue

                            logger.info(
                                "Exit signal: %s | reason: %s",
                                exit_signal,
                                exit_signal.get("reason", "No reason"),
                            )
                            state, close_ok, close_result = run_adaptive_close(
                                executor=executor,
                                config=config,
                                state_store=state_store,
                                state=state,
                                symbol=config.SYMBOL,
                                open_position=open_position,
                                reason_tag="strategy_exit",
                                dry_run=args.dry_run,
                                seed=loop_count,
                            )
                            if close_ok:
                                if hasattr(strategy, "current_position"):
                                    strategy.current_position = None
                                logger.info("Position closed successfully")
                            else:
                                alert_manager.send(
                                    f"[EXIT] Failed to close position: {close_result.get('code', 'CLOSE_UNKNOWN')}",
                                    level="error",
                                )
                                if bool(config.get("execution", "fail_halt_on_close_failure", True)):
                                    state["halted"] = True
                                    state["halt_reason"] = (
                                        f"CLOSE_FAILURE:{close_result.get('code', 'CLOSE_UNKNOWN')}"
                                    )
                                    state = state_store.save(state)
                elif open_position:
                    fallback_signal = strategy.get_signal()
                    if should_close_on_opposite_signal(open_position, fallback_signal):
                        logger.info(
                            "Strategy has no check_exit. Opposite signal detected; closing open position."
                        )
                        state, close_ok, close_result = run_adaptive_close(
                            executor=executor,
                            config=config,
                            state_store=state_store,
                            state=state,
                            symbol=config.SYMBOL,
                            open_position=open_position,
                            reason_tag="opposite_signal_exit",
                            dry_run=args.dry_run,
                            seed=loop_count,
                        )
                        if close_ok:
                            if hasattr(strategy, "current_position"):
                                strategy.current_position = None
                            logger.info("Position closed successfully")
                        else:
                            alert_manager.send(
                                f"[EXIT] Failed to close position: {close_result.get('code', 'CLOSE_UNKNOWN')}",
                                level="error",
                            )
                            if bool(config.get("execution", "fail_halt_on_close_failure", True)):
                                state["halted"] = True
                                state["halt_reason"] = (
                                    f"CLOSE_FAILURE:{close_result.get('code', 'CLOSE_UNKNOWN')}"
                                )
                                state = state_store.save(state)

                open_position = state.get("open_position")
                if open_position:
                    logger.info("Open position detected. Skipping new entry this cycle.")
                    continue

                if state.get("halted"):
                    logger.warning("Bot is halted: %s", state.get("halt_reason", ""))
                    continue

                signal = strategy.get_signal()
                if not signal:
                    continue

                side = normalize_side(signal.get("side"))
                if side is None:
                    logger.warning("Skipping signal with invalid side: %s", signal)
                    continue

                signal_amount_raw = signal.get("amount_usdt")
                signal_amount_usdt: Optional[float] = None
                if signal_amount_raw is not None:
                    try:
                        signal_amount_usdt = float(signal_amount_raw)
                    except (TypeError, ValueError):
                        logger.warning("Skipping signal with invalid amount_usdt: %s", signal)
                        continue

                if equity_usdt is None:
                    if risk_engine.fail_closed:
                        alert_manager.send(
                            "[RISK] Equity unavailable and fail_closed=true. Skipping entry.",
                            level="error",
                        )
                        continue
                    # fallback for permissive mode
                    desired_notional = signal_amount_usdt if signal_amount_usdt is not None else float(
                        config.ORDER_SIZE_USDT
                    )
                else:
                    desired_notional = risk_engine.compute_notional_from_risk(
                        account_equity_usdt=equity_usdt,
                        leverage=float(config.LEVERAGE),
                        signal_amount_usdt=signal_amount_usdt,
                    )

                reason = signal.get("reason", "No reason provided")
                logger.info("Signal received: %s | reason: %s", signal, reason)

                market_limits = executor.get_market_limits(config.SYMBOL)
                reference_price = executor.get_reference_price(config.SYMBOL, side)

                risk_decision = risk_engine.evaluate_entry(
                    side=side,
                    amount_usdt=desired_notional,
                    reference_price=reference_price,
                    market_limits=market_limits,
                    is_halted=bool(state.get("halted")),
                    account_equity_usdt=equity_usdt,
                    leverage=float(config.LEVERAGE),
                )
                if not risk_decision.allowed:
                    alert_manager.send(
                        f"[ENTRY BLOCKED] {risk_decision.code}: {risk_decision.reason}",
                        level="warning",
                    )
                    continue

                assert risk_decision.order_qty is not None
                amount_base = float(risk_decision.order_qty)
                amount_usdt = float(risk_decision.order_notional_usdt or desired_notional)
                logger.info(
                    "Executing %s order: %.8f %s (~%.2f USDT at ref %.6f)",
                    side.upper(),
                    amount_base,
                    config.SYMBOL,
                    amount_usdt,
                    float(reference_price),
                )

                order_params = build_order_params(signal)
                if not args.dry_run:
                    order = executor.place_market_order(
                        symbol=config.SYMBOL,
                        side=side,
                        amount=amount_base,
                        leverage=config.LEVERAGE,
                        params=order_params,
                        client_order_id=build_client_order_id(loop_count),
                    )
                    if not order:
                        alert_manager.send("[ENTRY] Order placement failed", level="error")
                        continue

                    strategy.on_order_placed(order)
                    logger.info("Order placed successfully: %s", order.get("id"))
                else:
                    logger.info("[DRY RUN] Order would be placed here")

                state["open_position"] = {
                    "side": side,
                    "amount_base": amount_base,
                    "entry_price": float(reference_price),
                    "amount_usdt": amount_usdt,
                    "sl_price": signal.get("sl_price"),
                    "opened_at": datetime.utcnow().isoformat(),
                }
                state = state_store.save(state)
                if hasattr(strategy, "current_position"):
                    strategy.current_position = dict(state["open_position"])

                # Successful loop iteration resets repeated error tracking.
                repeated_error_count = 0
                repeated_error_signature = ""
                repeated_error_last_ts = 0.0

            except Exception as exc:
                logger.error("Error in main loop: %s", exc)
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(traceback.format_exc())
                else:
                    logger.error("Traceback suppressed (use --log-level DEBUG for full stack)")

                now_ts = time.time()
                signature = f"{type(exc).__name__}:{exc}"
                if (
                    signature == repeated_error_signature
                    and now_ts - repeated_error_last_ts <= repeated_error_window_seconds
                ):
                    repeated_error_count += 1
                else:
                    repeated_error_signature = signature
                    repeated_error_count = 1
                repeated_error_last_ts = now_ts

                if repeated_error_count >= max_repeated_errors:
                    logger.critical(
                        "Repeated runtime error threshold hit (%s/%s): %s. Exiting to prevent log flood.",
                        repeated_error_count,
                        max_repeated_errors,
                        signature,
                    )
                    return 1

                try:
                    strategy.on_error(exc)
                except Exception:
                    logger.error("Strategy on_error handler raised an exception")
                time.sleep(error_backoff_seconds)

    except KeyboardInterrupt:
        logger.info("=" * 60)
        logger.info("Bot stopped by user (Ctrl+C)")
        logger.info("=" * 60)
        if "strategy" in locals():
            strategy.cleanup()
        if runtime_lock:
            runtime_lock.release()
        return 0

    except Exception as exc:
        logger.critical("Fatal error: %s", exc)
        if logger.isEnabledFor(logging.DEBUG):
            logger.critical(traceback.format_exc())
        else:
            logger.error("Fatal traceback suppressed (use --log-level DEBUG for full stack)")
        if runtime_lock:
            runtime_lock.release()
        return 1
    finally:
        if runtime_lock:
            runtime_lock.release()


if __name__ == "__main__":
    sys.exit(main())
