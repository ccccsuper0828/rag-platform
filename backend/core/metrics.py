import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JsonlMetricsLogger:
    """Append-only JSONL logger for performance metrics.

    One file per rag_id by default:
      logs/metrics/{rag_id}.jsonl
    """

    def __init__(self, rag_id: str, arch: str):
        self.rag_id = rag_id
        self.arch = arch
        base_dir = os.getenv("METRICS_DIR", "logs/metrics")
        os.makedirs(base_dir, exist_ok=True)
        self.path = os.path.join(base_dir, f"{rag_id}.jsonl")

    def write(self, event: str, data: Optional[Dict[str, Any]] = None):
        payload: Dict[str, Any] = {
            "ts": _utc_now_iso(),
            "rag_id": self.rag_id,
            "arch": self.arch,
            "event": event,
        }
        if data:
            payload.update(data)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @contextmanager
    def time_block(self, stage: str, extra: Optional[Dict[str, Any]] = None):
        start = time.perf_counter()
        try:
            yield
            ok = True
            err = None
        except Exception as e:
            ok = False
            err = str(e)
            raise
        finally:
            dur_ms = (time.perf_counter() - start) * 1000.0
            self.write(
                event="timing",
                data={
                    "stage": stage,
                    "ok": ok,
                    "duration_ms": round(dur_ms, 3),
                    "error": err,
                    **(extra or {}),
                },
            )


