from datetime import datetime, timezone
from dataclasses import replace
from time import perf_counter
import uuid
import streamlit as st
from banksynth.catalog import DEFAULT_FIELDS, resolve_fields
from banksynth.engine import Config
from banksynth.field_engine import generate_selected
from banksynth.export import bundle


def run_generation(config, mode="Simulator", reference=None, demo=False):
    start = perf_counter()
    selected = tuple(config.selected_fields) if config.selected_fields is not None else DEFAULT_FIELDS
    config = replace(config, selected_fields=selected)
    config.validate()
    comparison = None
    profile = None
    if reference is not None:
        from banksynth.reference import fit_sample, compare_profiles
        profile = fit_sample(reference, config.customers)
        comparison = compare_profiles(reference, profile)
    tables, checks = generate_selected(config, selected, profile)
    result = {"id": uuid.uuid4().hex[:8], "config": config, "tables": tables, "checks": checks,
              "mode": mode, "comparison": comparison, "demo": demo, "schema_version": 2,
              "selected_fields": selected, "resolved_fields": resolve_fields(selected),
              "elapsed": round(perf_counter() - start, 2), "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    st.session_state.result = result
    st.session_state.pop("archive", None)
    if not demo:
        history = st.session_state.get("history", [])
        history.insert(0, {"Run": result["id"], "Created (UTC)": result["at"], "Selected fields": len(selected),
                           "Tables": len(tables), "Engine": mode, "Customers": config.customers,
                           "Rows": sum(map(len, tables.values())), "Checks passed": sum(c["passed"] for c in checks),
                           "Seconds": result["elapsed"], "config": config})
        st.session_state.history = history[:20]
    return result


def current():
    if st.session_state.get("result", {}).get("schema_version") != 2:
        run_generation(Config(customers=250, transactions_per_account=12), demo=True)
    return st.session_state.result


def result_caption(result):
    cfg = result["config"]
    prefix = "Example dataset" if result["demo"] else f"Run {result['id']}"
    st.caption(f"{prefix} / {result['mode']} / {len(result['selected_fields'])} selected fields / {cfg.market} / seed {cfg.seed}")


def download(result):
    if not all(c["passed"] for c in result["checks"]):
        st.error("Export is blocked because validation checks failed. Review Quality & trust.")
        return
    if "archive" not in st.session_state:
        if st.button("Prepare download", icon=":material/package_2:", key="prepare_export"):
            with st.spinner("Packaging your selected schema and validation evidence..."):
                st.session_state.archive = bundle(result["tables"], result["config"], result["checks"], result["mode"], result["comparison"])
    if "archive" in st.session_state:
        st.download_button("Download dataset .zip", st.session_state.archive, f"forma-{result['id']}.zip", "application/zip", type="primary", icon=":material/download:")
