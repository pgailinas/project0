"""Thread-safe, in-process execution and state tracking for dashboard runs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from typing import Callable, Generic, TypeVar
from uuid import uuid4


ResultT = TypeVar("ResultT")


class BackgroundRunState(StrEnum):
    """Platform-owned lifecycle states for background work."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class BackgroundRun(Generic[ResultT]):
    """Immutable snapshot of one background run."""

    run_id: str
    agent_identifier: str
    state: BackgroundRunState
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: ResultT | None = None
    error_message: str | None = None


class BackgroundRunManager:
    """Execute dashboard work outside request lifetimes and retain results."""

    def __init__(self, max_workers: int = 1) -> None:
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="project0-dashboard-run",
        )
        self._lock = Lock()
        self._runs: dict[str, BackgroundRun[object]] = {}

    def submit(
        self,
        agent_identifier: str,
        operation: Callable[[], ResultT],
    ) -> BackgroundRun[ResultT]:
        """Create a run and return without waiting for its operation."""

        run: BackgroundRun[ResultT] = BackgroundRun(
            run_id=str(uuid4()),
            agent_identifier=agent_identifier,
            state=BackgroundRunState.QUEUED,
            created_at=datetime.now(UTC),
        )
        with self._lock:
            self._runs[run.run_id] = run
        self._executor.submit(self._execute, run.run_id, operation)
        return run

    def get(self, run_id: str) -> BackgroundRun[object] | None:
        """Return an immutable run snapshot, if it exists."""

        with self._lock:
            return self._runs.get(run_id)

    def _execute(
        self,
        run_id: str,
        operation: Callable[[], object],
    ) -> None:
        self._update(
            run_id,
            state=BackgroundRunState.RUNNING,
            started_at=datetime.now(UTC),
        )
        try:
            result = operation()
        except Exception as error:  # The platform must retain unexpected failures.
            self._update(
                run_id,
                state=BackgroundRunState.FAILED,
                completed_at=datetime.now(UTC),
                error_message=str(error),
            )
        else:
            self._update(
                run_id,
                state=BackgroundRunState.COMPLETED,
                completed_at=datetime.now(UTC),
                result=result,
            )

    def _update(self, run_id: str, **changes: object) -> None:
        with self._lock:
            current = self._runs[run_id]
            self._runs[run_id] = replace(current, **changes)
