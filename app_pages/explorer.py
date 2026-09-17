import streamlit as st
import pandas as pd
from banksynth.catalog import BY_ID, LABELS, PRIMARY_KEYS
from banksynth.ui import current, result_caption, download

st.caption("WORKSPACE / DATA EXPLORER")
st.title("Explore what you selected.")
st.write("Search your generated fields, inspect the schema, or follow a customer's connected records.")
r = current()
result_caption(r)
tables = r["tables"]
views = ["Table browser"] + (["Customer journey"] if "customers" in tables else [])
view = st.segmented_control("View", views, default="Table browser") or "Table browser"
if view == "Customer journey":
    customer_id = st.selectbox("Customer", tables["customers"].customer_id, key=f"journey_customer_{r['id']}")
    subsets = {"customers": tables["customers"][tables["customers"].customer_id == customer_id]}
    changed = True
    while changed:
        changed = False
        for table, frame in tables.items():
            if table in subsets:
                continue
            masks = []
            for col in frame:
                f = BY_ID[f"{table}.{col}"]
                if f.rule.startswith("fk:") and f.rule[3:] in subsets:
                    parent = f.rule[3:]
                    masks.append(frame[col].isin(subsets[parent][PRIMARY_KEYS[parent]]))
            if masks:
                mask = masks[0]
                for extra in masks[1:]:
                    mask &= extra
                subsets[table] = frame[mask]
                changed = True
    for table, frame in subsets.items():
        st.subheader(LABELS[table])
        if frame.empty:
            st.caption("No records generated for this customer in this table.")
        else:
            st.dataframe(frame.head(500), hide_index=True)
            if len(frame) > 500:
                st.caption("First 500 related records. Use the table browser to inspect the rest.")
    st.caption("This view follows the selected customer through child tables. Standalone reference tables are available in the table browser.")
else:
    name = st.selectbox("Table", list(tables), format_func=lambda x: f"{LABELS[x]} · {len(tables[x]):,} rows · {len(tables[x].columns)} fields", key=f"table_{r['id']}")
    frame = tables[name]
    left, right = st.columns([3, 1])
    with left:
        query = st.text_input("Find a record", placeholder="Search any value or synthetic identifier", key=f"query_{name}")
    with right:
        limit = st.selectbox("Rows per page", [25, 50, 100, 250], index=1)
    if "is_fraud" in frame and st.toggle("Show injected anomalies only"):
        frame = frame[frame.is_fraud]
    if query:
        mask = frame.astype(str).apply(lambda col: col.str.contains(query, case=False, regex=False)).any(axis=1)
        frame = frame[mask]
    count = len(frame)
    pages = max(1, (count + limit - 1) // limit)
    page = st.number_input("Page", 1, pages, 1, key=f"page_{name}_{count}_{limit}")
    st.caption(f"{count:,} matching records / page {page} of {pages}")
    if frame.empty:
        st.info("No records match. Clear your search or change the filter.")
    else:
        st.dataframe(frame.iloc[(page-1)*limit:page*limit], hide_index=True, height=410)
    with st.expander("Field definitions & schema"):
        selected = set(r["selected_fields"])
        st.dataframe(pd.DataFrame([{"Field": col, "Type": str(frame[col].dtype), "Source": "Selected" if f"{name}.{col}" in selected else "Supporting join key", "Description": BY_ID[f"{name}.{col}"].description} for col in frame]), hide_index=True)
    st.caption("The package contains all generated rows for the selected fields and supporting keys, independent of this filter.")
    download(r)
