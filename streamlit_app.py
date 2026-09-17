"""Streamlit Community Cloud entrypoint (choose this file when deploying)."""
import os
import runpy
from pathlib import Path

os.environ["BANKSYNTH_DEPLOYMENT"] = "community"
runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
