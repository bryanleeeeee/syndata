from dataclasses import asdict
import json
import pandas as pd
import streamlit as st
from banksynth.ui import run_generation

st.caption("WORKSPACE / RUN HISTORY")
st.title("A record of your experiments.")
st.write("Compare recent configurations and replay a simulator run with the same settings.")
st.caption("Last 20 runs in this browser session. History resets when the session ends; exported manifests provide the durable record. Only the latest dataset is held in memory.")
history = st.session_state.get("history", [])
if not history:
    st.info("Your first experiment starts in the field studio. The example dataset is not recorded as a run.")
    st.page_link("app_pages/studio.py", label="Open field studio", icon=":material/arrow_forward:")
else:
    st.dataframe(pd.DataFrame([{k: v for k, v in h.items() if k != "config"} for h in history]), hide_index=True)
    selected = st.selectbox("Run to inspect", [h["Run"] for h in history])
    chosen = next(h for h in history if h["Run"] == selected)
    st.json(asdict(chosen["config"]))
    st.download_button("Download configuration", json.dumps(asdict(chosen["config"]), indent=2), f"{selected}-config.json", "application/json")
    if chosen["Engine"] == "Simulator":
        if st.button("Replay this configuration", icon=":material/replay:"):
            with st.spinner("Replaying simulator..."):
                run_generation(chosen["config"])
            st.success("Replay complete. The result is available in the explorer.")
    else:
        st.caption("To repeat SDV training, return to the studio and upload the same approved reference. Reference uploads are not stored in history.")
