from datetime import date
import importlib.util
import json
import pandas as pd
import streamlit as st
from banksynth.catalog import FIELDS, BY_ID, DEFAULT_FIELDS, LABELS, catalog_records, resolve_fields
from banksynth.engine import Config, MARKETS
from banksynth.field_engine import estimate_cells
from banksynth.ui import current, run_generation, result_caption, download
from banksynth.reference import validate_profile
from banksynth.limits import get_limits, is_community
from banksynth.field_picker import render_field_picker, selected_options
from banksynth.schema import validate_formats

limits = get_limits()

STEPS = ["1 · Select fields", "2 · Generate", "3 · Results"]
st.session_state.setdefault("chosen_fields", list(DEFAULT_FIELDS))
if "pending_step" in st.session_state:
    st.session_state.studio_step = st.session_state.pop("pending_step")


def set_step(step):
    st.session_state.studio_step = step


st.caption("WORKSPACE / FIELD STUDIO")
st.title("Your fields. Your dataset.")
st.write("Build exactly the banking data you need. Choose from 500 curated fields across 20 domains.")
step = st.segmented_control("Build your dataset", STEPS, default=STEPS[0], key="studio_step", label_visibility="collapsed") or STEPS[0]

if step == STEPS[0]:
    render_field_picker(lambda: set_step(STEPS[1]))

elif step == STEPS[1]:
    selected = st.session_state.chosen_fields
    if not selected:
        st.info("Choose at least one field to continue.")
        st.button("Choose fields", on_click=set_step, args=(STEPS[0],))
        st.stop()
    resolved = resolve_fields(selected)
    try:
        validate_formats(selected_options(), selected)
    except ValueError as exc:
        st.error(str(exc))
        st.button("Edit field selection", on_click=set_step, args=(STEPS[0],))
        st.stop()
    st.subheader("Make it the right size.")
    st.caption(f"{len(selected)} selected fields + {len(set(resolved)-set(selected))} supporting keys / {len({BY_ID[x].table for x in resolved})} tables")
    left, right = st.columns([2, 1], gap="large")
    reference = None
    ready = True
    with left:
        mode = st.selectbox("Generation engine", (["Simulator"] if is_community() else ["Simulator", "SDV customer profiles"]), key="engine", help="SDV learns age, annual income and credit score only. Other fields use documented synthetic rules.")
        if is_community():
            st.caption("Public demo / Simulator only. Reference-trained SDV is available in private Cloudera/local deployments.")
        if mode != "Simulator":
            if importlib.util.find_spec("sdv") is None:
                st.warning("Install requirements-sdv.txt and restart to enable SDV.")
                ready = False
            st.caption("Approved CSV: exactly age, annual_income, credit_score. 100–50,000 rows; 5 MB maximum. SDV models only these three customer fields.")
            uploaded = st.file_uploader("Customer reference profiles", type="csv")
            if uploaded:
                try:
                    reference = validate_profile(pd.read_csv(uploaded))
                    st.success(f"{len(reference):,} reference profiles validated.")
                except (ValueError, pd.errors.ParserError, UnicodeDecodeError):
                    st.error("Use the three required numeric fields, without missing values. Age: 18–85; income: 12,000–500,000; score: 300–850.")
                    ready = False
            else:
                ready = False
            approved = st.checkbox("This reference is approved for modeling in this workspace.")
            ready = ready and approved
            st.caption("No differential privacy guarantee. SDV runs in session memory with a 180-second training limit.")
        with st.form("generate_form", border=True):
            a, b = st.columns(2)
            with a:
                customers = st.number_input("Customers", 10, limits["customers"], 1000, step=10, key="customers")
                market = st.selectbox("Market / currency", list(MARKETS), format_func=lambda x: f"{x} / {MARKETS[x]}")
                days = st.select_slider("History (days)", options=[7, 30, 60, 90, 180, 365, 730], value=90)
            with b:
                per_account = st.number_input("Transactions per account", 1, 100, 20, key="tx_count")
                end_date = st.date_input("History end date", date(2026, 8, 31))
                seed = st.number_input("Random seed", 0, 2**32 - 1, 42)
            with st.expander("Advanced generation settings", icon=":material/tune:"):
                fraud = st.slider("Injected transaction anomalies (%)", 0.0, 50.0, .5, .1)
                loan = st.slider("Customers with a loan (%)", 0, 100, 30)
            st.caption(f"Deployment limits: {limits['customers']:,} customers / {limits['transactions']:,} backing transactions / {limits['working_cells']:,} working cells.")
            st.caption("Customers sets portfolio size, not identical rows per table. Accounts: 1–2/customer. Loans: selected prevalence. Other customer domains: one/customer. Account domains: one/account. Branches: up to 10; securities: up to 25.")
            submitted = st.form_submit_button("Generate selected fields", type="primary", icon=":material/auto_awesome:", width="stretch", disabled=not ready)
        if submitted:
            cfg = Config(customers=int(customers), transactions_per_account=int(per_account), days=int(days), end_date=end_date.isoformat(), market=market, fraud_rate=fraud/100, loan_rate=loan/100, seed=int(seed), selected_fields=tuple(selected), field_options=selected_options())
            try:
                cfg.validate()
                if estimate_cells(cfg, selected) > limits["working_cells"]:
                    raise ValueError(f"Reduce portfolio size: this selection exceeds the {limits['working_cells']:,} working-cell limit.")
                with st.status("Generating your selected dataset…", expanded=True) as status:
                    st.write("Building fields and resolving relationships")
                    result = run_generation(cfg, mode, reference)
                    status.update(label=f"Ready in {result['elapsed']:.2f}s", state="complete", expanded=False)
                st.session_state.pending_step = STEPS[2]
                st.rerun()
            except (ValueError, ImportError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Generation could not finish. Check runtime dependencies and available memory. Your previous result is still available.")
    with right:
        with st.container(border=True):
            st.subheader("Your output schema")
            st.dataframe(pd.DataFrame([{"Table": t, "Fields": sum(BY_ID[x].table == t for x in resolved)} for t in LABELS if any(BY_ID[x].table == t for x in resolved)]), hide_index=True, height=300)
            if selected_options():
                with st.expander("Customized output formats", expanded=True):
                    st.dataframe(pd.DataFrame([{"Field": k, **v} for k, v in selected_options().items()]), hide_index=True)
            st.caption("Values outside your selection are excluded. Supporting primary/foreign keys are always included.")
            st.button("Edit field selection", on_click=set_step, args=(STEPS[0],), icon=":material/edit:")
        st.info("All values are synthetic. Simulated fields follow illustrative rules; market selection sets currency, not real population statistics.", icon=":material/shield:")
else:
    result = current()
    st.subheader("Your dataset is ready.")
    result_caption(result)
    if tuple(st.session_state.chosen_fields) != tuple(result["selected_fields"]) or selected_options() != (result["config"].field_options or {}):
        st.info("This is the last generated dataset. Your selection or field formats have changed; generate again to apply it.")
    with st.container(horizontal=True):
        st.metric("Selected fields", len(result["selected_fields"]), border=True)
        st.metric("Output columns", len(result["resolved_fields"]), border=True)
        st.metric("Tables", len(result["tables"]), border=True)
        st.metric("Records", f"{sum(map(len,result['tables'].values())):,}", border=True)
    left, right = st.columns([2, 1], gap="large")
    with left:
        table = st.selectbox("Preview a table", list(result["tables"]), key=f"preview_{result['id']}")
        st.dataframe(result["tables"][table].head(50), hide_index=True, height=350)
        st.caption("First 50 rows. Open the explorer to search, page through data and follow relationships.")
        st.page_link("app_pages/explorer.py", label="Open data explorer", icon=":material/arrow_forward:")
    with right:
        with st.container(border=True):
            checks = result["checks"]
            st.metric("Validation checks passed", f"{sum(x['passed'] for x in checks)} / {len(checks)}")
            st.caption("Schema, join keys, completeness and numeric checks. Ledger checks run on the backing portfolio before field projection.")
            download(result)
            st.page_link("app_pages/quality.py", label="Review quality & trust", icon=":material/verified_user:")
        st.button("Change fields", on_click=set_step, args=(STEPS[0],))
        st.button("Generate another dataset", on_click=set_step, args=(STEPS[1],))
