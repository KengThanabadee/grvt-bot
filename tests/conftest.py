import os
from pathlib import Path

import pytest


RUN_LIVE_TESTS_ENV = "RUN_LIVE_TESTS"
LIVE_TEST_CONFIG_ENV = "GRVT_TEST_CONFIG"


def _live_tests_enabled() -> bool:
    return os.getenv(RUN_LIVE_TESTS_ENV, "0").strip().lower() in {"1", "true", "yes"}


@pytest.fixture(scope="session")
def live_config():
    """Load validated config for live integration tests."""
    if not _live_tests_enabled():
        pytest.skip(
            f"Live tests disabled. Set {RUN_LIVE_TESTS_ENV}=1 to enable integration tests."
        )

    config_path = Path(os.getenv(LIVE_TEST_CONFIG_ENV, "config/config.yaml")).resolve()
    if not config_path.exists():
        pytest.skip(f"Live test config not found: {config_path}")

    from grvt_bot.core.config import ConfigManager

    config = ConfigManager(config_path=str(config_path))
    try:
        config.validate()
    except ValueError as exc:
        pytest.skip(f"Invalid live test config: {exc}")

    return config


@pytest.fixture(scope="session")
def live_executor(live_config):
    """Build executor for live integration tests."""
    from grvt_bot.core.executor import GRVTExecutor

    return GRVTExecutor(live_config)

