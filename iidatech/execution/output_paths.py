"""Durable business_build_outputs root (honors DATA_DIR / BUSINESS_OUTPUTS_ROOT)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def business_outputs_root() -> Path:
    """Return the durable outputs directory used for queues, checklists, and artifacts."""
    explicit = (os.getenv("BUSINESS_OUTPUTS_ROOT") or "").strip()
    if explicit:
        root = Path(explicit)
    else:
        data_dir = (os.getenv("DATA_DIR") or "").strip()
        if data_dir:
            root = Path(data_dir) / "business_build_outputs"
        else:
            root = Path(__file__).resolve().parents[2] / "business_build_outputs"
    root.mkdir(parents=True, exist_ok=True)
    return root


def employee_os2_root() -> Path:
    p = business_outputs_root() / "employee_os2"
    p.mkdir(parents=True, exist_ok=True)
    return p


def employee_runtime_root() -> Path:
    p = business_outputs_root() / "employee_runtime"
    p.mkdir(parents=True, exist_ok=True)
    return p


def automation_queues_root() -> Path:
    p = business_outputs_root() / "automation_queues"
    p.mkdir(parents=True, exist_ok=True)
    return p