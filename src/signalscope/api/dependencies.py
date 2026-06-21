"""FastAPI dependency helpers."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from signalscope.api.container import ApplicationContainer


def get_container(request: Request) -> ApplicationContainer:
    """Retrieve the process-scoped dependency container."""

    return cast(ApplicationContainer, request.app.state.container)
