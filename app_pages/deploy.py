import streamlit as st
st.caption("OPERATE / DEPLOYMENT")
st.title("At home in your environment.")
st.write("A single Python application. No external database, API key or GPU required for the simulator.")
a, b = st.columns(2)
with a:
    with st.container(border=True):
        st.subheader("Cloudera AI / CML")
        st.markdown("1. Upload this project to a Cloudera AI project.\n2. Choose a Python 3.11 runtime and open a terminal.\n3. Install the requirements below.\n4. Create an **Application**, with script **launch_app.py**.\n5. Start with **2 vCPU / 4 GB RAM** and grant access through Cloudera.")
        st.code("python -m pip install -r requirements.txt", language="bash")
        st.caption("The launcher reads CDSW_APP_PORT automatically. SDV and concurrent large runs may need 8 GB or more; size with your workload.")
with b:
    with st.container(border=True):
        st.subheader("Local development")
        st.code("python -m venv .venv\n# Activate your virtual environment\npython -m pip install -r requirements.txt\npython launch_app.py", language="bash")
        st.caption("Default URL: http://localhost:8501")
        st.subheader("Enable SDV")
        st.code("python -m pip install -r requirements-sdv.txt", language="bash")
        st.caption("Use Python 3.11 for the optional SDV dependency set. Restart after installation.")
with st.container(border=True):
    st.subheader("Streamlit Community Cloud")
    st.markdown("Repository: **bryanleeeeee/syndata** / Branch: **codex/field-studio** / Main file: **streamlit_app.py** / App URL: **datasynt**")
    st.caption("Choose Python 3.12 in Advanced settings. No secrets required. This entrypoint enables a simulator-only public profile with smaller memory budgets.")
st.subheader("Operational behavior")
st.markdown("""
- Datasets and uploaded reference profiles live in the current server session memory. No training data is written to disk by the app.
- Downloads include CSV files for selected tables, a manifest, schema, field definitions, selected-field configuration and SHA-256 checksums.
- Use Cloudera application access controls and TLS. The app does not implement a separate user directory.
- Keep the application private when enabling reference uploads. Set your institution's access, retention and disclosure-review policies before operational use.
- Generation runs synchronously; the 500,000-transaction ceiling limits individual interactive runs. Use the CLI with CML Jobs for scheduled batch work within the same limit.
""")
st.link_button("Cloudera application guidance", "https://docs.cloudera.com/machine-learning/cloud/projects/topics/ml-embedded-web-apps.html")
