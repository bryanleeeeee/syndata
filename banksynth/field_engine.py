"""Generate the selected catalog schema, with deterministic PK/FK closure."""
import hashlib
from datetime import date, timedelta
import numpy as np
import pandas as pd
from banksynth.catalog import FIELDS, BY_ID, PRIMARY_KEYS, resolve_fields
from banksynth.engine import MARKETS, generate
from banksynth.quality import evaluate
from banksynth.limits import get_limits


def estimate_cells(config, selected):
    resolved = resolve_fields(selected)
    counts = {"transactions": config.customers * 2 * config.transactions_per_account,
              "accounts": config.customers * 2, "cards": config.customers * 2,
              "payments": config.customers * 2, "deposits": config.customers * 2,
              "fx_trades": config.customers * 2, "branches": min(10, config.customers),
              "securities": min(25, config.customers)}
    # Materialization includes dependencies within selected tables, not just exports.
    return sum(counts.get(table, config.customers) * 25 for table in {BY_ID[x].table for x in resolved})


def generate_selected(config, selected, customer_profile=None):
    config.validate()
    resolved = resolve_fields(selected)
    if estimate_cells(config, selected) > get_limits()["working_cells"]:
        raise ValueError(f"This selection exceeds the {get_limits()['working_cells']:,} working-cell limit. Reduce customers or transactions per account.")
    baseline = generate(config, customer_profile)
    frames = {}
    currency = MARKETS[config.market]
    country = {"Singapore": "SG", "United Kingdom": "GB", "United States": "US", "European Union": "DE"}[config.market]
    asof = date.fromisoformat(config.end_date)
    start = asof - timedelta(days=config.days - 1)

    def materialize(table):
        if table in frames:
            return frames[table]
        if table in baseline:
            frame = baseline[table].copy()
        else:
            account_based = table in {"cards", "payments", "deposits", "fx_trades"}
            count = len(baseline["accounts"]) if account_based else config.customers
            if table == "branches":
                count = min(10, config.customers)
            if table == "securities":
                count = min(25, config.customers)
            frame = pd.DataFrame({PRIMARY_KEYS[table]: [f"SYN-{table.upper()}-{i+1:07d}" for i in range(count)]})
        frames[table] = frame
        size = len(frame)
        specs = {f.name: f for f in FIELDS if f.table == table}

        def get(name):
            if name in frame:
                return frame[name].to_numpy()
            f = specs[name]
            digest = int.from_bytes(hashlib.sha256(f.id.encode()).digest()[:8], "big")
            rng = np.random.default_rng([config.seed, digest])
            kind, _, args = f.rule.partition(":")
            parts = args.split(":")
            if kind in ("int", "money", "decimal"):
                low, high = map(float, parts)
                values = rng.integers(int(low), int(high) + 1, size) if kind == "int" else rng.uniform(low, high, size).round(2 if kind == "money" else 4)
            elif kind == "enum":
                values = rng.choice(args.split(";"), size)
            elif kind == "bool":
                values = rng.random(size) < .5
            elif kind == "constant":
                values = np.full(size, args == "true")
            elif kind == "fk":
                parent = materialize(args)
                keys = parent[PRIMARY_KEYS[args]].to_numpy()
                # Deterministic cyclic links keep every child owned by a valid parent.
                values = keys[np.arange(size) % len(keys)]
            elif kind in ("pastdate", "futuredate"):
                sign = -1 if kind == "pastdate" else 1
                values = [(asof + timedelta(days=sign * int(v))).isoformat() for v in rng.integers(1, 366, size)]
            elif kind == "asof":
                values = [asof.isoformat()] * size
            elif kind == "timestamp":
                values = (pd.Timestamp(start) + pd.to_timedelta(rng.integers(0, config.days*86400 - 7200, size), unit="s")).strftime("%Y-%m-%dT%H:%M:%S")
            elif kind in ("currency", "market", "country"):
                values = np.full(size, {"currency": currency, "market": config.market, "country": country}[kind])
            elif kind == "email":
                values = [f"synthetic.{table}.{i+1}@example.invalid" for i in range(size)]
            elif kind == "website":
                values = [f"https://synthetic-{table}-{i+1}.example.invalid" for i in range(size)]
            elif kind == "phone":
                values = [f"TEST-PHONE-{i+1:07d}" for i in range(size)]
            elif kind in ("name", "company", "address", "token", "lastfour", "ip"):
                if kind == "ip":
                    values = [f"192.0.2.{i % 254 + 1}" for i in range(size)]
                elif kind == "lastfour":
                    values = [f"{i % 10000:04d}" for i in range(size)]
                else:
                    prefix = {"name": "Synthetic person", "company": "Synthetic company", "address": "TEST ADDRESS", "token": f"SYN-{args}"}[kind]
                    values = [f"{prefix} {i+1:07d}" for i in range(size)]
            elif kind == "birthdate":
                values = [date(asof.year-int(age), asof.month, min(asof.day, 28)).isoformat() for age in get("age")]
            elif kind == "monthly_income":
                values = (get("annual_income") / 12).round(2)
            elif kind == "available_balance":
                values = (get("closing_balance") - get("hold_amount")).round(2)
            elif kind == "last_activity":
                last = baseline["transactions"].groupby("account_id").timestamp.max().str[:10]
                values = frame.account_id.map(last).to_numpy()
            elif kind == "anomaly_reason":
                values = np.where(get("is_fraud"), "Injected high-value anomaly", "Baseline")
            elif kind in ("settlement_date", "value_date"):
                values = pd.to_datetime(get("timestamp")).strftime("%Y-%m-%d")
            elif kind in ("loan_maturity", "deposit_maturity"):
                source = "start_date" if table == "deposits" else "origination_date"
                values = [(pd.Timestamp(d) + pd.DateOffset(months=int(m))).date().isoformat() for d, m in zip(get(source), get("term_months"))]
            elif kind == "outstanding":
                values = (get("principal") * rng.uniform(.1, 1, size)).round(2)
            elif kind == "repaid":
                values = (get("principal") - get("outstanding_principal")).round(2)
            elif kind == "days_past_due":
                values = np.where(get("status") == "Default", rng.integers(90, 366, size), 0)
            elif kind == "available_credit":
                values = (get("credit_limit") - get("current_balance")).round(2)
            elif kind == "instructed_amount":
                values = get("amount")
            elif kind == "deposit_interest":
                values = (get("principal") * get("interest_rate") / 100 * get("term_months") / 12).round(2)
            elif kind == "deposit_maturity_amount":
                values = (get("principal") + get("interest_amount")).round(2)
            elif kind == "cost_basis":
                values = (get("quantity") * get("unit_cost")).round(2)
            elif kind == "market_value":
                values = (get("quantity") * get("market_price")).round(2)
            elif kind == "unrealized_gain":
                values = (get("market_value") - get("cost_basis")).round(2)
            elif kind == "other_currency":
                values = np.full(size, "EUR" if currency == "USD" else "USD")
            elif kind == "fx_pair":
                values = [f"{buy}/{sell}" for buy, sell in zip(get("buy_currency"), get("sell_currency"))]
            elif kind == "fx_sell_amount":
                values = (get("buy_amount") * get("exchange_rate")).round(2)
            elif kind == "mortgage_ltv":
                values = (get("principal") / get("property_value")).round(4)
            elif kind == "mortgage_payment":
                rate = get("interest_rate") / 1200
                values = (get("principal") * rate / (1 - (1+rate)**-get("term_months"))).round(2)
            elif kind == "trade_utilized":
                values = (get("face_amount") * rng.uniform(0, 1, size)).round(2)
            elif kind == "trade_available":
                values = (get("face_amount") - get("utilized_amount")).round(2)
            elif kind == "logout":
                values = (pd.to_datetime(get("login_at")) + pd.to_timedelta(get("duration_seconds"), unit="s")).strftime("%Y-%m-%dT%H:%M:%S")
            else:
                raise ValueError(f"Unsupported field generator: {f.id}")
            frame[name] = values
            return frame[name].to_numpy()

        for name in specs:
            get(name)
        # Shared attributes follow their referenced record, rather than separate draws.
        if table == "investments":
            securities = materialize("securities").set_index("security_id")
            frame["asset_class"] = frame.security_id.map(securities.asset_class)
            frame["market_price"] = frame.security_id.map(securities.price)
            frame["market_value"] = (frame.quantity * frame.market_price).round(2)
            frame["unrealized_gain"] = (frame.market_value - frame.cost_basis).round(2)
        if table == "aml_alerts":
            tx = baseline["transactions"].set_index("transaction_id")
            frame["created_at"] = frame.transaction_id.map(tx.timestamp)
        if table == "branches":
            frame["timezone"] = {"Singapore": "Asia/Singapore", "United Kingdom": "Europe/London", "United States": "America/New_York", "European Union": "Europe/Berlin"}[config.market]
        return frame

    output = {}
    for table in dict.fromkeys(BY_ID[x].table for x in resolved):
        frame = materialize(table)
        output[table] = frame[[BY_ID[x].name for x in resolved if BY_ID[x].table == table]].copy()
    checks = validate_selected(output, resolved)
    if "transactions" in output or "accounts" in output:
        for check in evaluate(baseline):
            check = dict(check)
            check["check"] = "Backing portfolio / " + check["check"]
            check["detail"] += "; evaluated before field projection"
            checks.append(check)
    return output, checks


def validate_selected(tables, resolved):
    checks = []
    def check(name, passed, detail):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})
    expected_tables = {BY_ID[x].table for x in resolved}
    check("Selected schema", set(tables) == expected_tables and all(set(df) == {BY_ID[x].name for x in resolved if BY_ID[x].table == t} for t, df in tables.items()), "Output contains selected fields and disclosed join keys only")
    for table, df in tables.items():
        pk = PRIMARY_KEYS[table]
        check(f"{table}: primary keys", pk in df and df[pk].is_unique and df[pk].notna().all(), f"{len(df):,} records inspected")
        check(f"{table}: complete fields", not df.isna().any().any(), "Selected fields have no missing values")
        numeric = df.select_dtypes(include="number")
        check(f"{table}: finite numbers", np.isfinite(numeric.to_numpy()).all(), "Numeric values contain no NaN or infinity")
        for col in df:
            f = BY_ID[f"{table}.{col}"]
            if f.rule.startswith("fk:"):
                parent = f.rule[3:]
                check(f"{table}.{col}: foreign key", parent in tables and df[col].isin(tables[parent][PRIMARY_KEYS[parent]]).all(), f"Every reference resolves to {parent}")
    return checks
