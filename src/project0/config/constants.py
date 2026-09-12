# ============================================================
# Project0 - Project0 Constants
#
# File: constants.py
#
# Purpose:
#     Define constants used throughout Project0.
#
# ============================================================

# Logging level default
DEFAULT_LOG_LEVEL = "INFO"

# Ollama reasoning provider defaults
DEFAULT_OLLAMA_TIMEOUT_SECONDS = 600.0
DEFAULT_OLLAMA_CONTEXT_WINDOW_TOKENS = 16384

# Knowledge service limits
KNOWLEDGE_MAXIMUM_DOCUMENTS = 5

# Research source provider defaults
#
# Default behavior preserves the current live research workflow.
# Acceptance environments may override provider selection through
# runtime configuration.
DEFAULT_RESEARCH_SOURCE_PROVIDERS = (
    "semantic_scholar",
    "arxiv",
)

DEFAULT_RESEARCH_DIRECTION_ANALYSIS_ENABLED = True

# Supported providers
SUPPORTED_RESEARCH_SOURCE_PROVIDERS = (
    "semantic_scholar",
    "openalex",
    "openreview",
    "crossref",
    "arxiv",
    "stub",
)
