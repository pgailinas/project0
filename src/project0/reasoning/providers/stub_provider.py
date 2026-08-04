# ============================================================
# Project0 - Stub Reasoning Provider
#
# File: stub_provider.py
#
# Purpose:
#     Provide deterministic reasoning provider behavior for
#     Project0 tests, demonstrations, and integration flows.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field

from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
)


@dataclass(slots=True)
class StubReasoningProvider:
    """Return configured provider responses without model execution."""

    response: ProviderResponse
    error: Exception | None = None
    requests: list[ProviderRequest] = field(
        default_factory=list,
        init=False,
    )

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Record the request and return the configured result."""

        self.requests.append(request)

        if self.error is not None:
            raise self.error

        return self.response
