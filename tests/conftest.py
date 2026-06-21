from pathlib import Path

import pytest

from signalscope.api.container import ApplicationContainer, build_container
from signalscope.core.config import Settings


@pytest.fixture()
def settings() -> Settings:
    return Settings(
        environment="test",
        data_dir=Path("data/demo"),
        cors_origins="http://localhost:3000",
        llm_provider="deterministic",
    )


@pytest.fixture()
def container(settings: Settings) -> ApplicationContainer:
    instance = build_container(settings)
    instance.catalog.load()
    return instance
