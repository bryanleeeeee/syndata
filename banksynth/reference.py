"""Optional SDV customer-profile modeling. No reference records are persisted."""
import numpy as np
import pandas as pd

COLUMNS = {"age": (18, 85), "annual_income": (12000, 500000), "credit_score": (300, 850)}

def validate_profile(data: pd.DataFrame, minimum=100):
    if set(data.columns) != set(COLUMNS):
        raise ValueError("The CSV must contain exactly age, annual_income, credit_score. Remove identifiers and other columns before upload.")
    if not minimum <= len(data) <= 50000:
        raise ValueError(f"Provide {minimum:,}–50,000 rows.")
    clean = data[list(COLUMNS)].copy()
    for col, (low, high) in COLUMNS.items():
        clean[col] = pd.to_numeric(clean[col], errors="coerce")
        if not np.isfinite(clean[col]).all() or not clean[col].between(low, high).all():
            raise ValueError(f"{col} must contain finite numbers between {low:,} and {high:,}, without missing values.")
        if col != "annual_income" and not (clean[col] % 1 == 0).all():
            raise ValueError(f"{col} must contain whole numbers.")
    return clean

def fit_sample(data: pd.DataFrame, rows: int):
    """Isolate optional native libraries; terminate stalled training after 180 seconds."""
    import json
    from pathlib import Path
    import subprocess
    import sys
    clean = validate_profile(data)
    payload = json.dumps({"records": clean.to_dict(orient="records"), "rows": rows})
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "banksynth.sdv_worker"], input=payload,
            text=True, capture_output=True, timeout=180,
            cwd=Path(__file__).resolve().parents[1],
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("SDV exceeded the 180-second training limit. Try a smaller reference or a compatible Linux runtime.") from exc
    if completed.returncode:
        raise ValueError("SDV could not train in this runtime. Verify requirements-sdv.txt and native library support; your previous result is unchanged.")
    try:
        return validate_profile(pd.DataFrame(json.loads(completed.stdout)), minimum=rows)
    except (ValueError, TypeError) as exc:
        raise ValueError("SDV returned an invalid customer profile.") from exc


def _fit_sample_in_worker(data: pd.DataFrame, rows: int):
    from sdv.metadata import Metadata
    from sdv.single_table import GaussianCopulaSynthesizer
    clean = validate_profile(data)
    metadata = Metadata.detect_from_dataframe(data=clean)
    model = GaussianCopulaSynthesizer(metadata, enforce_min_max_values=True, enforce_rounding=True)
    model.fit(clean)
    model.reset_sampling()
    sample = model.sample(num_rows=rows)
    for col, (low, high) in COLUMNS.items():
        sample[col] = sample[col].clip(low, high)
        if col != "annual_income":
            sample[col] = sample[col].round().astype(int)
    return validate_profile(sample, minimum=rows)

def compare_profiles(reference, synthetic):
    """Descriptive evidence, not a privacy or generalization certification."""
    rows = []
    for col in COLUMNS:
        ref, syn = reference[col].to_numpy(), synthetic[col].to_numpy()
        grid = np.sort(np.unique(np.concatenate([ref, syn])))
        distance = np.max(np.abs(np.searchsorted(np.sort(ref), grid, side="right") / len(ref) - np.searchsorted(np.sort(syn), grid, side="right") / len(syn)))
        rows.append({"column": col, "reference_mean": float(ref.mean()), "synthetic_mean": float(syn.mean()), "KS_distance": float(distance)})
    return rows
