import pandas as pd
import streamlit as st
from banksynth.ui import current, result_caption

st.caption("WORKSPACE / QUALITY & TRUST")
st.title("Evidence, not guesswork.")
st.write("Review the checks, assumptions and limits behind this dataset before using it. Checks marked Backing portfolio apply before field projection.")
r = current()
result_caption(r)
checks = r["checks"]
a, b, c = st.columns(3)
a.metric("Integrity checks", f"{sum(x['passed'] for x in checks)} / {len(checks)}", border=True)
b.metric("Source data", "None" if r["mode"] == "Simulator" else "Reference CSV", border=True)
c.metric("Differential privacy", "Not applied", border=True)
check_frame = pd.DataFrame(checks).rename(columns={"check": "Check", "detail": "Scope"})
check_frame["Result"] = check_frame.pop("passed").map({True: "PASS", False: "FAIL"})
st.subheader("Selected schema & data integrity")
st.dataframe(check_frame, hide_index=True, height=400)
a, b = st.columns(2)
with a:
    with st.container(border=True):
        st.subheader("Statistical fidelity")
        if r["comparison"]:
            st.dataframe(pd.DataFrame(r["comparison"]), hide_index=True)
            st.caption("KS distance: 0 is an identical empirical distribution, 1 is maximum separation. These in-sample, single-column diagnostics do not establish joint fidelity, predictive utility or disclosure safety.")
        else:
            st.write("No reference comparison for this run.")
            st.caption("Simulator distributions are designed assumptions. To measure customer marginal fidelity, choose SDV customer profiles and supply an approved reference CSV.")
with b:
    with st.container(border=True):
        st.subheader("Privacy & intended use")
        st.write("Simulator identities are visibly fictional; no real records are needed. SDV training uses approved reference profiles and does not provide a differential privacy guarantee.")
        st.caption("Neither an integrity pass nor removing direct identifiers establishes anonymity or regulatory compliance. Assess reference-trained output for disclosure risk and intended-use fitness.")
with st.expander("Model assumptions & boundaries", expanded=True):
    st.markdown("""
- Adult retail profiles: ages 18–85, annual income 12,000–500,000, score 300–850. Score scales are illustrative across all markets.
- Market sets currency only. Income and transaction distributions are not calibrated to each market.
- 1–2 accounts per customer. Transaction amounts are correlated with income; timestamps are uniformly sampled and sorted.
- Opening balances are funded to avoid overdrafts. This changes the balance distribution; it is a testing constraint.
- Loan records are standalone snapshots. They do not create disbursement or repayment entries in transaction ledgers.
- Fraud means injected high-value anomalies. It is not a validated AML typology or real fraud ground truth. Exclude anomaly_reason and is_fraud from model features.
- The catalog contains 500 curated fields across 20 domains, not an industry ranking. Additional domains are illustrative test snapshots: not every business rule or cross-field constraint is modeled.
- Exports contain only selected fields and supporting join keys.
- SDV models only age, income and credit score. Relationships and transaction behavior use the simulator in both modes.
- The seed replays the simulator. SDV uses its own reset sampling state; model reproducibility depends on the SDV version and input.
""")
st.download_button("Download validation report", pd.DataFrame(checks).to_csv(index=False), "validation.csv", "text/csv", icon=":material/download:")
