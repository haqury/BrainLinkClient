"""Export current BrainLink Client settings for the game to read."""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ui.main_window import MainWindow

logger = logging.getLogger(__name__)

EXPORT_FILENAME = "brainlink_export_for_game.json"
EXPORT_VERSION = 1

# All 11 EegFaultModel keys required in export (int)
BASE_FAULT_KEYS = (
    "attention",
    "meditation",
    "signal",
    "delta",
    "theta",
    "low_alpha",
    "high_alpha",
    "low_beta",
    "high_beta",
    "low_gamma",
    "high_gamma",
)


def get_export_dir() -> Path:
    base = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "BrainLink"
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_export_path() -> Path:
    return get_export_dir() / EXPORT_FILENAME


def _fault_config_path_store() -> Path:
    from utils.path_utils import get_config_dir
    return get_config_dir() / "fault_config_path.json"


def load_fault_config_path() -> Optional[str]:
    """Load last fault JSON path from config/fault_config_path.json."""
    store = _fault_config_path_store()
    try:
        if not store.exists():
            return None
        with open(store, "r", encoding="utf-8") as f:
            data = json.load(f)
        path = (data.get("fault_config_path") or "").strip()
        return path or None
    except Exception as e:
        logger.warning("Failed to load fault_config_path.json: %s", e)
        return None


def save_fault_config_path(path: str) -> None:
    """Persist absolute path to last fault config JSON."""
    if not path:
        return
    abs_path = str(Path(path).expanduser().resolve())
    store = _fault_config_path_store()
    try:
        store.parent.mkdir(parents=True, exist_ok=True)
        with open(store, "w", encoding="utf-8") as f:
            json.dump({"fault_config_path": abs_path}, f, indent=2, ensure_ascii=False)
        logger.info("Saved fault_config_path: %s", abs_path)
    except Exception as e:
        logger.warning("Failed to save fault_config_path.json: %s", e)


def normalize_base_fault(raw: Optional[dict]) -> dict[str, int]:
    """Ensure all 11 base_fault keys exist as ints."""
    src = raw or {}
    out: dict[str, int] = {}
    for key in BASE_FAULT_KEYS:
        try:
            out[key] = int(src.get(key, 0) or 0)
        except (TypeError, ValueError):
            out[key] = 0
    return out


def _resolve_fault_config_path(main_window: "MainWindow") -> str:
    """Absolute path to last fault JSON (form path > persisted > default config.json)."""
    form = getattr(main_window, "config_form", None)
    if form is not None and hasattr(form, "txt_filepath"):
        text = (form.txt_filepath.text() or "").strip()
        if text:
            return str(Path(text).expanduser().resolve())

    stored = load_fault_config_path()
    if stored:
        return str(Path(stored).expanduser().resolve())

    from config_defaults import get_default_config_path
    return str(Path(get_default_config_path()).resolve())


def _base_fault_for_export(main_window: "MainWindow") -> dict[str, int]:
    """
    Source of truth: MainWindow.config.eeg_fault.
    If ConfigForm is open and visible, merge base fields from the form,
    but keep signal from in-memory config when the form has no signal field
    (or always prefer form when signal is present).
    """
    memory_fault = {}
    if getattr(main_window, "config", None) and main_window.config.eeg_fault:
        memory_fault = main_window.config.eeg_fault.to_dict()

    form = getattr(main_window, "config_form", None)
    if form is not None:
        try:
            visible = form.isVisible()
        except Exception:
            visible = False
        if visible and hasattr(form, "get_config_fault"):
            try:
                form_fault = form.get_config_fault().to_dict()
                # Preserve signal from memory if form omitted it (legacy UI)
                if "signal" not in form_fault or (
                    not hasattr(form, "txt_signal")
                    and "signal" in memory_fault
                ):
                    form_fault["signal"] = memory_fault.get("signal", 0)
                return normalize_base_fault(form_fault)
            except Exception as e:
                logger.warning("ConfigForm base_fault for export failed: %s", e)

    return normalize_base_fault(memory_fault)


def build_brainlink_export(main_window: "MainWindow") -> dict[str, Any]:
    """Snapshot of client settings the game BrainLink panel cares about (export_version=1)."""
    cw = getattr(main_window.ml_trainer.config, "class_weights", None) or {}
    # Game panel historically expects 4 weights (ml, mr, mu, md); include stop as 5th if present.
    weights = [
        float(cw.get("ml", 1.0)),
        float(cw.get("mr", 1.0)),
        float(cw.get("mu", 1.0)),
        float(cw.get("md", 1.0)),
    ]
    stop_w = cw.get("stop")
    if stop_w is not None:
        weights.append(float(stop_w))

    model_path = getattr(main_window.ml_trainer.config, "model_path", "") or ""
    history_path = getattr(main_window, "_history_path", "") or ""
    if history_path:
        try:
            history_path = str(Path(history_path).expanduser().resolve())
        except Exception:
            history_path = str(history_path)
    if model_path:
        try:
            model_path = str(Path(model_path).expanduser().resolve())
        except Exception:
            model_path = str(model_path)

    multi_fault = {}
    multi_count = 1
    if getattr(main_window, "config", None):
        if main_window.config.eeg_fault_multi:
            multi_fault = normalize_base_fault(main_window.config.eeg_fault_multi.to_dict())
        multi_count = max(1, int(getattr(main_window.config, "multi_count", 1) or 1))

    return {
        "export_version": EXPORT_VERSION,
        "updated_at": time.time(),
        "client_cwd": str(Path.cwd()),
        "fault_config_path": _resolve_fault_config_path(main_window),
        "brainlink": {
            "prediction_mode": "ml" if getattr(main_window, "_use_ml_prediction", False) else "base",
            "model_path": model_path,
            "history_path": history_path,
            "confidence_threshold": float(main_window.ml_trainer.config.confidence_threshold),
            "prediction_weights": weights,
            "base_fault": _base_fault_for_export(main_window),
            "multi_fault": multi_fault,
            "multi_count": multi_count,
        },
    }


def write_brainlink_export(main_window: "MainWindow") -> bool:
    """
    Write %APPDATA%\\BrainLink\\brainlink_export_for_game.json (atomic replace).
    Returns True on success.
    """
    try:
        payload = build_brainlink_export(main_window)
        path = get_export_path()
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
        logger.info(
            "Wrote BrainLink export for game: %s (base_fault.low_alpha=%s)",
            path,
            payload.get("brainlink", {}).get("base_fault", {}).get("low_alpha"),
        )
        return True
    except Exception as e:
        logger.warning("Failed to write BrainLink export for game: %s", e)
        return False
