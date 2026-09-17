# Forma — banking synthetic data field studio

A Python/Streamlit workspace for choosing and generating banking test data. Browse **500 curated fields across 20 domains**, select one or many, and export only the fields you need with supporting relational keys. Run locally or as a Cloudera AI/CML Application; no external API or database is required.

## Publish on Streamlit Community Cloud

See [STREAMLIT_CLOUD.md](STREAMLIT_CLOUD.md) for the exact settings for **datasynthetic.streamlit.app**. Deploy `streamlit_app.py` from branch `codex/field-studio` with Python 3.12 and no secrets. This public profile keeps all 500 fields, uses simulator-only generation, and applies smaller resource budgets.

## Quick start

```bash
python -m venv .venv
# Linux / Cloudera
source .venv/bin/activate
# Windows: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python launch_app.py
```

Open http://localhost:8501. The launcher honors `CDSW_APP_PORT` first, then `PORT`, then 8501. Python 3.11+ is recommended. Development has been tested on Windows Python 3.14; validate your Cloudera runtime before operational use.

## Field-first workflow

1. **Select fields.** Search by name, field ID, domain or description. Filter by banking domain and data type. Use the searchable multiselect for one or multiple fields, add all matching fields, select all 500, or clear the selection. Selections persist across filters and page changes.
2. **Generate.** Choose portfolio size, currency, history window and seed. Advanced settings control loan prevalence and injected transaction anomalies. SDV customer profiles are optional.
3. **Results.** Preview any output table, inspect validation, and download the dataset. The explorer supports search, pagination, field definitions and customer relationship drilldown.

A starter selection of 12 fields is provided; it is editable and not a scenario preset. The review panel lists selected counts and every automatically included join key. You can download the full catalog as CSV, save a selection as JSON, or paste comma-separated/newline-separated field IDs or a JSON string array to restore a selection.

### Catalog

The term “500” refers to 500 unique, table-qualified field IDs: exactly 25 fields in each domain. This is a practical curated catalog, **not an empirically ranked top-500 list or a regulatory standard**.

| Domain | Table | Fields |
|---|---|---:|
| Customer profiles | customers | 25 |
| Accounts & balances | accounts | 25 |
| Transactions | transactions | 25 |
| Lending | loans | 25 |
| Cards | cards | 25 |
| Payments | payments | 25 |
| Beneficiaries | beneficiaries | 25 |
| Term deposits | deposits | 25 |
| Investment holdings | investments | 25 |
| Security master | securities | 25 |
| Foreign exchange | fx_trades | 25 |
| Mortgages | mortgages | 25 |
| Business banking | businesses | 25 |
| Trade finance | trade_finance | 25 |
| KYC & onboarding | kyc | 25 |
| AML monitoring | aml_alerts | 25 |
| Digital banking | digital_sessions | 25 |
| Branch network | branches | 25 |
| Service & complaints | complaints | 25 |
| Consent & preferences | consents | 25 |

Definitions live in `banksynth/catalog.py`; `catalog/fields.csv` provides a spreadsheet-readable copy. Each definition includes its type, description, and generation rule. Field IDs are qualified, e.g. `customers.age`, `payments.amount`, or `cards.credit_limit`.

### What gets exported

Only requested fields and the PK/FK closure needed to join their records are exported. Choosing `cards.credit_limit`, for example, adds `cards.card_id`, `cards.account_id`, `accounts.account_id`, `accounts.customer_id`, and `customers.customer_id`. It does not export customer income, names or transaction values. The UI identifies supporting keys before generation.

The ZIP contains CSV files for the resulting tables, `manifest.json`, `field_definitions.json`, and a README. The manifest captures selected fields, added keys, relationships, configuration, dependency versions, validation and SHA-256 hashes. All records are included, independent of explorer filters.

### Row counts and reproducibility

“Customers” controls the portfolio scale. It does not force identical row counts:

- Customers and additional customer domains: one record/customer.
- Accounts: one or two/customer. Cards, payments, deposits and FX trades: one/account.
- Transactions: selected number/account. Loans: sampled according to loan prevalence.
- AML alerts: one illustrative test alert/customer, linked to a generated transaction; not a realistic alert-frequency model.
- Security master: up to 25 securities. Branch network: up to 10 branches.

Field-specific deterministic random streams make a field's values stable when other fields are selected or removed. For simulator replay, retain the same configuration and dependency versions. Run history stores the latest 20 configurations and their field selections, not all generated datasets.

## Cloudera AI / CML deployment

1. Create a project from this Git repository, or upload the source files. Exclude `.venv`, logs, caches, secrets and generated data.
2. Select a Python 3.11+ runtime and run `python -m pip install -r requirements.txt` in the project terminal.
3. Open **Applications → New Application** and select **launch_app.py** as the script.
4. Initially allocate **2 vCPU / 4 GB RAM** for modest simulator runs. Use more memory for larger selections, SDV or concurrent users.
5. Launch the application. Use Cloudera's private application access controls and TLS for the intended users.

The app binds to `0.0.0.0` and the assigned `CDSW_APP_PORT`. Streamlit XSRF and CORS defaults remain enabled. Reverse proxies must support WebSockets. There is no separate app-managed identity system.

A Cloudera workspace was not available for end-to-end deployment verification. Launcher port routing is tested locally. For air-gapped operation, prebuild a wheelhouse for the target Linux/Python architecture, then install with `--no-index --find-links`.

### Batch jobs

```bash
python -m banksynth.cli --config my-config.json --output portfolio.zip
```

Export a complete configuration from Run history. `selected_fields` is a JSON list of qualified IDs. Omitting the config uses the 12 starter fields. Existing output paths are rejected to avoid overwrites. The CLI uses the simulator and enforces the same limits.

### Container

```bash
docker build -t forma .
docker run --rm -p 8501:8501 forma
```

The image installs simulator dependencies and runs as a non-root user. Test Docker and Cloudera deployment in your target environment.

## Optional SDV path

```bash
python -m pip install -r requirements-sdv.txt
```

Restart, choose **SDV customer profiles**, and upload an approved CSV with exactly `age`, `annual_income`, and `credit_score`. Supply 100–50,000 complete numeric rows under 5 MB. Age must be an integer 18–85, income 12,000–500,000 in the chosen currency, and score an integer 300–850.

SDV's Gaussian Copula learns these three fields only. It does not learn arbitrary selected fields or all 20 banking domains. Other fields still use simulator rules. The report compares customer marginal means and empirical KS distances, not joint fidelity or predictive utility. No real bank source data was supplied; tests use synthetic reference profiles.

SDV runs in an isolated subprocess with a 180-second startup/training limit. First Windows startup can be slow while PyTorch loads native libraries. On failure the app retains the previous dataset. Reference records and trained models are not written to disk by the application or cached globally; buffers remain in server-session memory until removed/expired. Export/history never contains the uploaded CSV. Closing a tab does not guarantee immediate secure memory erasure.

## Model boundaries

- This is a functional test-data generator, not a certified privacy or production banking platform.
- The catalog is curated. Generated distributions and ranges are explicit illustrative assumptions, not calibrated estimates of a real bank.
- Core account transactions reconcile using integer cents. Opening balances are funded to prevent implicit overdrafts. These backing-ledger checks run before field projection and are labeled accordingly in the report.
- Derived fields include monthly income, available credit, loan principal repaid, term-deposit interest/maturity value, investment cost/value/gain, FX conversion, mortgage payment/LTV, trade utilization and session duration. Tests verify these relationships.
- Additional domains are illustrative snapshots, not a complete accounting or lifecycle model. Independent status/category attributes are not all mutually constrained. Loans, deposits, payments, investments and mortgages do not post disbursements or settlements to the account ledger.
- Market sets currency and a representative country/timezone. It does not calibrate demographics, product behavior or local credit-score conventions. Dates do not model real seasonality or payroll schedules.
- Names, addresses, phones and credential-like fields use explicit synthetic/test markers. Email/website examples use `.invalid`; IP addresses use the documentation range. Card references are not real payment card numbers; no CVV is produced.
- Fraud/AML fields are injected test labels and workflow snapshots, not proven real-world fraud typologies. Do not use `is_fraud` or `anomaly_reason` as predictive features.
- SDV here is **not differentially private**. No regulatory compliance, anonymity, fairness or disclosure-safety certification is claimed. Evaluate reference-trained output before sharing.
- Interactive generation is synchronous, limited to a worst-case 500,000 backing transactions and 8 million working cells in selected domains. Values needed for dependencies can be generated internally even if not exported. Memory scales with concurrent sessions; this is not a distributed service.
- History is session-local, not a durable audit log. Export the manifest to retain generation evidence.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The suite verifies all 500 field generators, selection closure, every domain, reproducibility under selection changes, derived arithmetic, key integrity, invalid/empty selections, working limits, schema-restricted exports, SDV and UI flows. SDV integration skips only when the optional package is absent. Browser review covers the field studio's rendered layout.

## Design references

[SDV](https://docs.sdv.dev/sdv) informs local statistical modeling. [Cloudera application guidance](https://docs.cloudera.com/machine-learning/cloud/projects/topics/ml-embedded-web-apps.html) informs application port routing. [Syntheticus](https://syntheticus.ai/synthetic-data-for-finance-and-banking) and [Betterdata](https://www.betterdata.ai/) informed the original banking workflows and deployment approach. These references are not equivalence claims; MOSTLY AI is not integrated. Review dependency licenses before institutional distribution.
