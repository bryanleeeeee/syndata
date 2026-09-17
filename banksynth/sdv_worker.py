"""Private SDV subprocess protocol; receives and returns in-memory JSON only."""
import contextlib
import json
import sys
import pandas as pd
from banksynth.reference import _fit_sample_in_worker

if __name__ == "__main__":
    request = json.load(sys.stdin)
    with contextlib.redirect_stdout(sys.stderr):
        sample = _fit_sample_in_worker(pd.DataFrame(request["records"]), request["rows"])
    sys.stdout.write(sample.to_json(orient="records"))
