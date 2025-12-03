import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # custom extra fields
        for key in ("agent", "stage", "event", "status", "runtime_ms"):
            if hasattr(record, key):
                base[key] = getattr(record, key)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            base.update(record.extra_fields)
        return json.dumps(base)


def setup_logger(log_file: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger("kasparro")
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    handler: logging.Handler
    if log_file:
        handler = logging.FileHandler(log_file, encoding="utf-8")
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)
    return logger


def log_event(
    logger: logging.Logger,
    *,
    level: int = logging.INFO,
    agent: str,
    stage: str,
    event: str,
    status: str = "ok",
    runtime_ms: Optional[float] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    extra_fields = {
        "agent": agent,
        "stage": stage,
        "event": event,
        "status": status,
    }
    if runtime_ms is not None:
        extra_fields["runtime_ms"] = runtime_ms
    if extra:
        extra_fields.update(extra)

    logger.log(level, event, extra={"extra_fields": extra_fields})
