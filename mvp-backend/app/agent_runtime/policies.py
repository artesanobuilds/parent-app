"""Admission-time switches; never re-read these during an in-flight turn."""
import os


def shared_execution_enabled(surface: str) -> bool:
    return os.getenv(f"MVP_SHARED_RUNTIME_{surface.upper()}", "0").lower() in {
        "1", "true", "yes",
    }
