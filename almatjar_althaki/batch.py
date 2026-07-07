from __future__ import annotations

import json
import statistics
import time
import tracemalloc
from pathlib import Path

from .store import handle_store_message, load_catalog


def _p(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1))))]


def evaluate(events_path: str | Path, catalog_path: str | Path, *, repeat: int = 1) -> dict:
    catalog = load_catalog(catalog_path)
    rows = [json.loads(line) for line in Path(events_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = drafts = escalations = 0
    latencies = []
    started = time.perf_counter()
    tracemalloc.start()
    for _ in range(repeat):
        for row in rows:
            t0 = time.perf_counter()
            try:
                result = handle_store_message(str(row.get("message") or ""), catalog)
                drafts += 1 if result["action"] == "CREATE_DRAFT_ORDER" else 0
                escalations += 1 if result["action"] == "ESCALATE_SUPPORT" else 0
            except Exception:
                errors += 1
            latencies.append((time.perf_counter() - t0) * 1000)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    processed = len(rows) * repeat
    return {
        "processed": processed,
        "errors": errors,
        "draft_orders": drafts,
        "escalations": escalations,
        "latency_ms": {"mean": statistics.fmean(latencies) if latencies else 0.0, "p99": _p(latencies, 99), "max": max(latencies) if latencies else 0.0},
        "memory_mb": {"current": current / 1_000_000, "peak": peak / 1_000_000},
        "elapsed_seconds": time.perf_counter() - started,
        "collapse_check": {"passed": errors == 0, "criteria": "errors == 0"},
    }

