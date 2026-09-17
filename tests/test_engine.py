import hashlib
import io
import json
import zipfile
from dataclasses import replace
import pandas as pd
import pytest
from banksynth.engine import Config, generate, PRESETS
from banksynth.quality import evaluate
from banksynth.export import bundle
from banksynth.reference import validate_profile, fit_sample, compare_profiles

@pytest.mark.parametrize("scenario", list(PRESETS))
@pytest.mark.parametrize("seed", [0, 42, 999])
def test_portfolio_integrity(scenario, seed):
    cfg = Config(customers=100, transactions_per_account=15, scenario=scenario, seed=seed)
    tables = generate(cfg)
    assert all(c["passed"] for c in evaluate(tables))
    assert len(tables["transactions"]) == len(tables["accounts"]) * 15
    tx = pd.to_datetime(tables["transactions"].timestamp)
    assert tx.min() >= pd.Timestamp(cfg.end_date) - pd.Timedelta(days=cfg.days - 1)
    assert tx.max() < pd.Timestamp(cfg.end_date) + pd.Timedelta(days=1)


def test_reproducibility_and_seed_difference():
    cfg = Config(customers=20)
    a, b, c = generate(cfg), generate(cfg), generate(replace(cfg, seed=77))
    for key in a:
        pd.testing.assert_frame_equal(a[key], b[key])
    assert not a["customers"].equals(c["customers"])


def test_no_loans_or_fraud_and_all_loans():
    t = generate(Config(customers=10, loan_rate=0, fraud_rate=0))
    assert t["loans"].empty
    assert not t["transactions"].is_fraud.any()
    assert all(c["passed"] for c in evaluate(t))
    assert len(generate(Config(customers=10, loan_rate=1))["loans"]) == 10

@pytest.mark.parametrize("changes", [{"customers": -1}, {"customers": 10000, "transactions_per_account": 100}, {"seed": -1}, {"fraud_rate": float("nan")}, {"market": "bad"}, {"days": 0}, {"end_date": "bad"}, {"customers": True}])
def test_invalid_configuration(changes):
    with pytest.raises(ValueError):
        generate(replace(Config(), **changes))


def test_validator_detects_corruption():
    tables = generate(Config(customers=10))
    tables["transactions"].loc[0, "balance_after"] += .01
    assert not next(c for c in evaluate(tables) if c["check"] == "Running balances reconcile")["passed"]
    tables["loans"].loc[0, "customer_id"] = "unknown"
    assert not next(c for c in evaluate(tables) if c["check"] == "Loan borrowers")["passed"]


def test_export_roundtrip():
    cfg = Config(customers=10)
    t = generate(cfg)
    with zipfile.ZipFile(io.BytesIO(bundle(t, cfg, evaluate(t)))) as z:
        m = json.loads(z.read("manifest.json"))
        for name in t:
            assert hashlib.sha256(z.read(f"{name}.csv")).hexdigest() == m["tables"][name]["sha256"]
            assert len(pd.read_csv(z.open(f"{name}.csv"))) == len(t[name])
        assert m["config"]["seed"] == 42


def test_reference_rejects_identifiers_missing_and_infinite():
    d = generate(Config(customers=100))["customers"][["age", "annual_income", "credit_score"]]
    with pytest.raises(ValueError):
        validate_profile(d.assign(name="Private"))
    with pytest.raises(ValueError):
        validate_profile(d.assign(age=float("inf")))
    assert len(validate_profile(d)) == 100


def test_sdv_end_to_end():
    from importlib.util import find_spec
    if find_spec("sdv") is None:
        pytest.skip("SDV is not installed")
    d = generate(Config(customers=150))["customers"][["age", "annual_income", "credit_score"]]
    sample = fit_sample(d, 100)
    assert len(sample) == 100
    generated = generate(Config(customers=100), sample)
    assert all(c["passed"] for c in evaluate(generated))
    assert len(compare_profiles(d, sample)) == 3


def test_sdv_timeout_is_actionable(monkeypatch):
    import subprocess
    def stalled(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], kwargs["timeout"])
    monkeypatch.setattr(subprocess, "run", stalled)
    d = generate(Config(customers=100))["customers"][["age", "annual_income", "credit_score"]]
    with pytest.raises(ValueError, match="180-second"):
        fit_sample(d, 100)
