import io
import json
import zipfile
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from banksynth.catalog import FIELDS, BY_ID, LABELS, PRIMARY_KEYS, DEFAULT_FIELDS, resolve_fields
from banksynth.engine import Config
from banksynth.field_engine import generate_selected, validate_selected
from banksynth.export import bundle

ALL = tuple(f.id for f in FIELDS)


def test_exactly_500_defined_fields():
    assert len(FIELDS) == len(BY_ID) == 500
    assert len(LABELS) == 20
    for table in LABELS:
        assert sum(f.table == table for f in FIELDS) == 25
    assert all(f.description and f.dtype for f in FIELDS)


def test_every_generator_and_derived_arithmetic():
    tables, checks = generate_selected(Config(customers=20, transactions_per_account=2), ALL)
    assert sum(len(frame.columns) for frame in tables.values()) == 500
    assert all(c["passed"] for c in checks)
    c, a, cards = tables["customers"], tables["accounts"], tables["cards"]
    assert np.allclose(c.monthly_income, (c.annual_income/12).round(2))
    assert np.allclose(a.available_balance, a.closing_balance-a.hold_amount)
    assert np.allclose(cards.available_credit, cards.credit_limit-cards.current_balance)
    loans = tables["loans"]
    assert np.allclose(loans.amount_repaid+loans.outstanding_principal, loans.principal)
    dep = tables["deposits"]
    assert np.allclose(dep.maturity_amount, dep.principal+dep.interest_amount)
    inv = tables["investments"]
    assert np.allclose(inv.unrealized_gain, inv.market_value-inv.cost_basis)
    assert (inv.market_price == inv.security_id.map(tables["securities"].set_index("security_id").price)).all()
    fx = tables["fx_trades"]
    assert np.allclose(fx.sell_amount, (fx.buy_amount*fx.exchange_rate).round(2))
    sessions = tables["digital_sessions"]
    assert ((pd.to_datetime(sessions.logout_at)-pd.to_datetime(sessions.login_at)).dt.total_seconds() == sessions.duration_seconds).all()
    assert tables["customers"].email.str.endswith("@example.invalid").all()


@pytest.mark.parametrize("table", list(LABELS))
def test_one_field_from_every_domain_and_fk_closure(table):
    field = next(f.id for f in reversed(FIELDS) if f.table == table)
    resolved = resolve_fields([field])
    tables, checks = generate_selected(Config(customers=10, transactions_per_account=1), [field])
    actual = {f"{t}.{col}" for t, df in tables.items() for col in df}
    assert actual == set(resolved)
    assert all(c["passed"] for c in checks)
    assert field in actual


def test_selection_does_not_change_generated_values():
    cfg = Config(customers=20)
    one, _ = generate_selected(cfg, ["cards.available_credit"])
    all_tables, _ = generate_selected(cfg, ALL)
    for table, frame in one.items():
        pd.testing.assert_frame_equal(frame, all_tables[table][list(frame)])


def test_export_includes_only_selected_and_keys():
    chosen = ("payments.amount",)
    cfg = Config(customers=10, selected_fields=chosen)
    tables, checks = generate_selected(cfg, chosen)
    with zipfile.ZipFile(io.BytesIO(bundle(tables, cfg, checks))) as z:
        m = json.loads(z.read("manifest.json"))
        assert m["selected_fields"] == list(chosen)
        assert set(m["supporting_keys"]) == set(resolve_fields(chosen)) - set(chosen)
        assert "cards.csv" not in z.namelist()
        assert list(pd.read_csv(z.open("customers.csv"))) == ["customer_id"]
        assert "field_definitions.json" in z.namelist()


def test_unknown_empty_duplicate_and_cell_limit():
    for fields in [[], ["unknown"], ["customers.age", "customers.age"]]:
        with pytest.raises(ValueError):
            resolve_fields(fields)
    with pytest.raises(ValueError, match="working-cell"):
        generate_selected(Config(customers=10000, transactions_per_account=25), ALL)


def test_selected_validator_finds_broken_foreign_key():
    t, _ = generate_selected(Config(customers=10), ["cards.credit_limit"])
    t["cards"].loc[0, "account_id"] = "bad"
    assert not all(c["passed"] for c in validate_selected(t, resolve_fields(["cards.credit_limit"])))
