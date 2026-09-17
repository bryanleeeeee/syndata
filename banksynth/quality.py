import numpy as np
import pandas as pd

def evaluate(tables):
    c, a, t, l = [tables[k] for k in ("customers", "accounts", "transactions", "loans")]
    checks = []
    def check(name, passed, detail):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})
    for name, frame in tables.items():
        key = {"customers": "customer_id", "accounts": "account_id", "transactions": "transaction_id", "loans": "loan_id"}[name]
        check(f"{name.title()}: unique primary keys", frame[key].is_unique and frame[key].notna().all(), f"{len(frame):,} rows inspected")
        check(f"{name.title()}: complete fields", not frame.isna().any().any(), "No missing values")
    for name, child, key, parent in [("Account owners", a, "customer_id", c), ("Transaction accounts", t, "account_id", a), ("Loan borrowers", l, "customer_id", c)]:
        check(name, child[key].isin(parent[key]).all(), "All foreign keys resolve")
    cents = lambda series: (series * 100).round().astype("int64")
    ordered = t.sort_values(["account_id", "timestamp", "transaction_id"])
    signed = cents(ordered.amount).where(ordered.direction == "Credit", -cents(ordered.amount))
    expected = signed.groupby(ordered.account_id).cumsum() + cents(ordered.account_id.map(a.set_index("account_id").opening_balance))
    check("Running balances reconcile", np.array_equal(expected.to_numpy(), cents(ordered.balance_after).to_numpy()), "Every debit and credit reconciles to cents")
    closing = ordered.groupby("account_id").balance_after.last().reindex(a.account_id).to_numpy()
    check("Closing balances reconcile", np.allclose(closing, a.closing_balance, atol=.001, rtol=0), "Last transaction equals account closing balance")
    check("Positive transaction amounts", (t.amount > 0).all(), "Amounts are positive; direction specifies movement")
    check("No unintended overdrafts", (t.balance_after >= 0).all(), "Opening funding covers the generated ledger")
    opened = pd.to_datetime(t.account_id.map(a.set_index("account_id").opened_at))
    check("Account chronology", (pd.to_datetime(t.timestamp) >= opened).all(), "Transactions occur after account opening")
    check("Customer ranges", c.age.between(18, 85).all() and c.credit_score.between(300, 850).all() and c.annual_income.between(12000, 500000).all(), "Configured adult retail customer bounds")
    check("Currency consistency", (t.currency.to_numpy() == t.account_id.map(a.set_index("account_id").currency).to_numpy()).all(), "Transactions use their account currency")
    return checks
