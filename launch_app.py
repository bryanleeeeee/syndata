"""Entrypoint for Cloudera AI Applications and local development."""
import os
from pathlib import Path
import subprocess
import sys


def command():
    port = int(os.environ.get("CDSW_APP_PORT", os.environ.get("PORT", "8501")))
    if not 1 <= port <= 65535:
        raise ValueError("Application port must be 1–65535")
    return [sys.executable, "-m", "streamlit", "run", str(Path(__file__).with_name("app.py")),
            "--server.address", "0.0.0.0", "--server.port", str(port), "--server.headless", "true"]

if __name__ == "__main__":
    raise SystemExit(subprocess.call(command(), cwd=Path(__file__).parent))
