from dataclasses import asdict, dataclass
from datetime import date, timedelta
import numpy as np
import pandas as pd
from banksynth.limits import get_limits

MARKETS = {"Singapore": "SGD", "United Kingdom": "GBP", "United States": "USD", "European Union": "EUR"}
PRESETS = {
    "Everyday banking": {"fraud_rate": 0.005, "loan_rate": 0.30, "description": "A balanced retail portfolio for analytics, demos and integration testing."},
    "Fraud sandbox": {"fraud_rate": 0.08, "loan_rate": 0.20, "description": "Enriched transaction anomalies with explicit scenario labels for pipeline testing."},
    "Credit stress": {"fraud_rate": 0.01, "loan_rate": 0.65, "description": "A lending-heavy portfolio with elevated simulated defaults."},
}

@dataclass(frozen=True)
class Config:
    customers: int = 1000
    transactions_per_account: int = 20
    days: int = 90
    end_date: str = "2026-08-31"
    market: str = "Singapore"
    scenario: str = "Everyday banking"
    fraud_rate: float = 0.005
    loan_rate: float = 0.30
    seed: int = 42
    selected_fields: tuple[str, ...] | None = None
    field_options: dict | None = None

    def validate(self):
        limits = get_limits()
        for field, low, high in [("customers", 10, limits["customers"]), ("transactions_per_account", 1, 100), ("days", 7, 730), ("seed", 0, 2**32 - 1)]:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise ValueError(f"{field} must be an integer between {low} and {high}.")
        if self.customers * 2 * self.transactions_per_account > limits["transactions"]:
            raise ValueError(f"Choose fewer customers or transactions. This deployment supports up to {limits['transactions']:,} backing transactions.")
        if self.market not in MARKETS or self.scenario not in PRESETS:
            raise ValueError("Choose a supported market and scenario.")
        if not 0 <= self.fraud_rate <= 0.5 or not 0 <= self.loan_rate <= 1:
            raise ValueError("Fraud rate must be 0–50%; loan rate must be 0–100%.")
        date.fromisoformat(self.end_date)
        if self.selected_fields is not None:
            from banksynth.catalog import resolve_fields
            resolve_fields(self.selected_fields)
        if self.field_options:
            from banksynth.schema import validate_formats
            validate_formats(self.field_options, self.selected_fields or ())


def generate(config: Config, customer_profile: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Generate a deterministic relational portfolio. Monetary ledgers use integer cents."""
    config.validate()
    rng = np.random.default_rng(config.seed)
    n = config.customers
    start = pd.Timestamp(date.fromisoformat(config.end_date) - timedelta(days=config.days - 1))
    currency = MARKETS[config.market]
    age = rng.integers(18, 86, n)
    income = np.clip(rng.lognormal(10.6, .65, n) * (0.65 + age / 100), 12000, 500000).round(2)
    score = np.clip(590 + 0.001 * income + rng.normal(0, 65, n), 300, 850).astype(int)
    if customer_profile is not None:
        from banksynth.reference import validate_profile
        customer_profile = validate_profile(customer_profile, minimum=n).iloc[:n]
        age = customer_profile.age.to_numpy().astype(int)
        income = customer_profile.annual_income.to_numpy().round(2)
        score = customer_profile.credit_score.to_numpy().astype(int)
    customers = pd.DataFrame({
        "customer_id": [f"SYN-C{i:07d}" for i in range(1, n + 1)],
        "display_name": [f"Synthetic customer {i:07d}" for i in range(1, n + 1)],
        "age": age, "annual_income": income, "credit_score": score,
        "segment": np.where(income >= 120000, "Private", np.where(income >= 60000, "Affluent", "Retail")),
        "market": config.market, "currency": currency,
    })
    owners = np.repeat(np.arange(n), rng.choice([1, 2], n, p=[.65, .35]))
    a = len(owners)
    opening = np.maximum(10000, (income[owners] * rng.uniform(.015, .25, a) * 100).astype(np.int64))
    accounts = pd.DataFrame({
        "account_id": [f"SYN-A{i:07d}" for i in range(1, a + 1)],
        "customer_id": customers.customer_id.to_numpy()[owners],
        "account_type": rng.choice(["Current", "Savings"], a, p=[.7, .3]),
        "currency": currency,
        "opened_at": (start - pd.to_timedelta(rng.integers(1, 3650, a), unit="D")).strftime("%Y-%m-%d"),
        "opening_balance": opening / 100,
    })
    account_idx = np.repeat(np.arange(a), config.transactions_per_account)
    t = len(account_idx)
    seconds = rng.integers(0, config.days * 86400, t)
    order = np.lexsort((seconds, account_idx))
    account_idx, seconds = account_idx[order], seconds[order]
    fraud = rng.random(t) < config.fraud_rate
    direction = rng.choice(["Debit", "Credit"], t, p=[.78, .22])
    amounts = np.maximum(1, (rng.lognormal(3.7, 1.1, t) * (income[owners[account_idx]] / 55000) ** .45 * 100).astype(np.int64))
    amounts[fraud] *= rng.integers(5, 16, fraud.sum())
    signed = np.where(direction == "Credit", amounts, -amounts)
    deltas = pd.Series(signed).groupby(account_idx).cumsum().to_numpy()
    # Fund the opening balance enough for this scenario: no implicit overdrafts.
    lows = pd.Series(deltas).groupby(account_idx).min().reindex(range(a), fill_value=0).to_numpy()
    opening = np.maximum(opening, -lows + 10000)
    accounts["opening_balance"] = opening / 100
    balances = opening[account_idx] + deltas
    accounts["closing_balance"] = balances.reshape(a, config.transactions_per_account)[:, -1] / 100
    transactions = pd.DataFrame({
        "transaction_id": [f"SYN-T{i:09d}" for i in range(1, t + 1)],
        "account_id": accounts.account_id.to_numpy()[account_idx],
        "timestamp": (start + pd.to_timedelta(seconds, unit="s")).strftime("%Y-%m-%dT%H:%M:%S"),
        "direction": direction, "amount": amounts / 100, "currency": currency,
        "category": np.where(direction == "Credit", "Incoming transfer", rng.choice(["Groceries", "Dining", "Shopping", "Transport", "Utilities", "Transfer"], t)),
        "channel": rng.choice(["Mobile", "Card", "Online", "ATM", "Branch"], t, p=[.36, .32, .22, .07, .03]),
        "balance_after": balances / 100,
        "is_fraud": fraud,
        "scenario_label": np.where(fraud, "Injected high-value anomaly", "Baseline"),
    })
    borrowers = np.flatnonzero(rng.random(n) < config.loan_rate)
    l = len(borrowers)
    principal = np.maximum(100000, (income[borrowers] * rng.uniform(.2, 3, l) * 100).astype(np.int64))
    term = rng.choice([12, 24, 36, 60, 120], l)
    apr = np.clip(3 + (850 - score[borrowers]) / 35, 3, 24).round(2)
    default_probability = np.clip((850 - score[borrowers]) / 2200, .005, .30)
    if config.scenario == "Credit stress":
        default_probability = np.minimum(.8, default_probability * 3)
    rate = apr / 1200
    monthly = principal / 100 * rate / (1 - (1 + rate) ** -term)
    loans = pd.DataFrame({
        "loan_id": [f"SYN-L{i:07d}" for i in range(1, l + 1)],
        "customer_id": customers.customer_id.to_numpy()[borrowers],
        "principal": principal / 100, "currency": currency, "term_months": term,
        "apr_percent": apr, "monthly_payment": monthly.round(2),
        "status": np.where(rng.random(l) < default_probability, "Default", "Performing"),
    })
    return {"customers": customers, "accounts": accounts, "transactions": transactions, "loans": loans}
