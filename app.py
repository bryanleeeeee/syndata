import streamlit as st
from banksynth.limits import is_community

st.set_page_config(page_title="Forma | Banking data studio", page_icon=":material/account_balance:", layout="wide")
with st.sidebar:
    st.logo("logo.svg", size="large")
    st.caption("BANKING DATA STUDIO")
    st.space("small")
page = st.navigation({"Workspace": [
    st.Page("app_pages/studio.py", title="Field studio", icon=":material/auto_awesome:", default=True),
    st.Page("app_pages/explorer.py", title="Data explorer", icon=":material/table_chart:"),
    st.Page("app_pages/quality.py", title="Quality & trust", icon=":material/verified_user:"),
    st.Page("app_pages/history.py", title="Run history", icon=":material/history:"),
], "Operate": [st.Page("app_pages/deploy.py", title="Deployment guide", icon=":material/cloud_upload:")]})
with st.sidebar:
    st.space("large")
    st.badge("Community Cloud" if is_community() else "Server execution", color="green", icon=":material/lock:")
    st.caption("Synthetic data only. No reference uploads." if is_community() else "Your workspace. Your data.\n\nGeneration runs on this server without vendor API calls.")
    st.caption("FORMA / v2.0")
page.run()
