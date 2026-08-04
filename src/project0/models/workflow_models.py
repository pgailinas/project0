# ============================================================
# Project0 - Workflow Models
#
# File: workflow_models.py
#
# Purpose:
#     Define shared workflow and task data models used by
#     Project0 platform components and AI agents.
#
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Callable
from uuid import uuid4


class WorkflowStatus(StrEnum):
    """Supported workflow execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskStatus(StrEnum):
    """Supported task execution states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class WorkflowTask:
    """A single executable task within a workflow."""

    name: str
    action: Callable[[], object]
    task_id: str = field(default_factory=lambda: str(uuid4()))


@dataclass(frozen=True, slots=True)
class TaskExecutionResult:
    """Result of one task execution."""

    task_id: str
    task_name: str
    status: TaskStatus
    started_at: datetime
    completed_at: datetime
    output: object | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowExecutionResult:
    """Result of a complete workflow execution."""

    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    started_at: datetime
    completed_at: datetime
    task_results: tuple[TaskExecutionResult, ...]
    error_message: str | None = None
