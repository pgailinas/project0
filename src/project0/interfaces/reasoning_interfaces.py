# ============================================================
# Project0 - Reasoning Interfaces
#
# File: reasoning_interfaces.py
#
# Purpose:
#     Define shared interfaces for reasoning services, prompt
#     builders, and AI model providers used by Project0.
#
# ============================================================

from __future__ import annotations

from typing import Protocol

from project0.models.reasoning_models import (
    ProviderRequest,
    ProviderResponse,
    ReasoningRequest,
    ReasoningResult,
)


class PromptBuilderProtocol(Protocol):
    """Interface for building provider-neutral reasoning prompts."""

    def build_prompt(
        self,
        request: ReasoningRequest,
    ) -> ProviderRequest:
        """Build a provider request from a reasoning request."""

        ...


class ReasoningProviderProtocol(Protocol):
    """Interface for AI reasoning model providers."""

    def generate(
        self,
        request: ProviderRequest,
    ) -> ProviderResponse:
        """Generate a provider response."""

        ...


class ReasoningServiceProtocol(Protocol):
    """Interface for AI-assisted repository reasoning services."""

    def reason(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResult:
        """Execute repository reasoning for a request."""

        ...
