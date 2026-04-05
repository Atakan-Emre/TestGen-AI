from __future__ import annotations

from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Optional
from uuid import uuid4


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class ScenarioJobLogEntry:
    timestamp: str
    level: str
    message: str


@dataclass
class ScenarioJobState:
    job_id: str
    request: dict[str, Any]
    status: str = "queued"
    progress: float = 0.0
    current_stage: str = "queued"
    logs: list[ScenarioJobLogEntry] = field(default_factory=list)
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    updated_at: str = field(default_factory=_now_iso)


class ScenarioJobManager:
    def __init__(self, max_logs: int = 300, max_jobs: int = 50):
        self._max_logs = max_logs
        self._max_jobs = max_jobs
        self._jobs: "OrderedDict[str, ScenarioJobState]" = OrderedDict()
        self._lock = Lock()

    def create_job(self, request: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            job_id = uuid4().hex
            state = ScenarioJobState(job_id=job_id, request=request)
            state.logs.append(
                ScenarioJobLogEntry(
                    timestamp=_now_iso(),
                    level="info",
                    message="Senaryo üretim işi kuyruğa alındı.",
                )
            )
            self._jobs[job_id] = state
            self._trim_jobs()
            return self._serialize(state)

    def start_job(
        self,
        job_id: str,
        *,
        message: str = "Senaryo üretimi başlatıldı.",
        progress: float = 0.01,
        stage: str = "starting",
    ) -> dict[str, Any]:
        with self._lock:
            state = self._get_state(job_id)
            state.status = "running"
            state.started_at = state.started_at or _now_iso()
            self._apply_progress(state, progress, stage)
            self._append_log(state, message, "info")
            return self._serialize(state)

    def append_log(
        self,
        job_id: str,
        message: str,
        *,
        level: str = "info",
        progress: Optional[float] = None,
        stage: Optional[str] = None,
    ) -> dict[str, Any]:
        with self._lock:
            state = self._get_state(job_id)
            if progress is not None or stage is not None:
                self._apply_progress(state, progress, stage)
            self._append_log(state, message, level)
            return self._serialize(state)

    def complete(
        self,
        job_id: str,
        result: dict[str, Any],
        *,
        message: str = "Senaryo üretimi tamamlandı.",
    ) -> dict[str, Any]:
        with self._lock:
            state = self._get_state(job_id)
            state.status = "completed"
            state.result = result
            state.error = None
            state.completed_at = _now_iso()
            self._apply_progress(state, 1.0, "completed")
            self._append_log(state, message, "info")
            return self._serialize(state)

    def fail(
        self,
        job_id: str,
        error: str,
        *,
        stage: str = "failed",
    ) -> dict[str, Any]:
        with self._lock:
            state = self._get_state(job_id)
            state.status = "failed"
            state.error = error
            state.completed_at = _now_iso()
            self._apply_progress(state, state.progress, stage)
            self._append_log(state, error, "error")
            return self._serialize(state)

    def get_job(self, job_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            state = self._jobs.get(job_id)
            return self._serialize(state) if state else None

    def _trim_jobs(self) -> None:
        while len(self._jobs) > self._max_jobs:
            self._jobs.popitem(last=False)

    def _apply_progress(
        self,
        state: ScenarioJobState,
        progress: Optional[float],
        stage: Optional[str],
    ) -> None:
        if progress is not None:
            bounded = max(0.0, min(float(progress), 1.0))
            if state.status == "failed":
                state.progress = bounded
            else:
                state.progress = max(state.progress, bounded)
        if stage:
            state.current_stage = stage
        state.updated_at = _now_iso()

    def _append_log(self, state: ScenarioJobState, message: str, level: str) -> None:
        state.logs.append(
            ScenarioJobLogEntry(
                timestamp=_now_iso(),
                level=level,
                message=message,
            )
        )
        if len(state.logs) > self._max_logs:
            state.logs = state.logs[-self._max_logs :]
        state.updated_at = _now_iso()

    def _get_state(self, job_id: str) -> ScenarioJobState:
        state = self._jobs.get(job_id)
        if state is None:
            raise KeyError(job_id)
        return state

    def _serialize(self, state: Optional[ScenarioJobState]) -> Optional[dict[str, Any]]:
        if state is None:
            return None
        return asdict(state)
