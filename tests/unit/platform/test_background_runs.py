"""Tests for platform-owned dashboard background runs."""

from threading import Event

from project0.platform.background_runs import (
    BackgroundRunManager,
    BackgroundRunState,
)


def test_submit_returns_before_operation_completes() -> None:
    release = Event()
    manager = BackgroundRunManager(max_workers=1)

    run = manager.submit("research", lambda: release.wait(1))

    assert run.state is BackgroundRunState.QUEUED
    assert manager.get(run.run_id) is not None
    release.set()


def test_completed_run_retains_result() -> None:
    completed = Event()
    manager = BackgroundRunManager(max_workers=1)

    def operation() -> str:
        completed.set()
        return "result"

    run = manager.submit("documentation", operation)
    assert completed.wait(1)

    snapshot = manager.get(run.run_id)
    while snapshot is not None and snapshot.state is not BackgroundRunState.COMPLETED:
        snapshot = manager.get(run.run_id)

    assert snapshot is not None
    assert snapshot.result == "result"
    assert snapshot.completed_at is not None


def test_failed_run_retains_error() -> None:
    attempted = Event()
    manager = BackgroundRunManager(max_workers=1)

    def operation() -> None:
        attempted.set()
        raise RuntimeError("failure")

    run = manager.submit("research", operation)
    assert attempted.wait(1)

    snapshot = manager.get(run.run_id)
    while snapshot is not None and snapshot.state is not BackgroundRunState.FAILED:
        snapshot = manager.get(run.run_id)

    assert snapshot is not None
    assert snapshot.error_message == "failure"
