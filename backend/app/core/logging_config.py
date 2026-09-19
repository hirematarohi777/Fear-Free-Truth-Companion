import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict


class PrivacySafeJsonFormatter(logging.Formatter):
    """Structured JSON formatter that strictly strips or redacts sensitive keys."""
    SENSITIVE_KEYS = {
        "password", "password_hash", "token", "token_hash", "csrf_token",
        "secret", "cookie", "authorization", "document_text", "raw_content"
    }

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = record.correlation_id
        if hasattr(record, "job_id"):
            log_obj["job_id"] = record.job_id
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Sanitize extra fields
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            clean_extra = {}
            for k, v in record.extra.items():
                if k.lower() in self.SENSITIVE_KEYS:
                    clean_extra[k] = "[REDACTED]"
                else:
                    clean_extra[k] = v
            log_obj["extra"] = clean_extra

        return json.dumps(log_obj)


def setup_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PrivacySafeJsonFormatter())
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = [handler]
    
    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)


logger = logging.getLogger("fear_free_companion")
