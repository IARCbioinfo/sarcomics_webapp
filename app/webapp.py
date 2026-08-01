import streamlit as st

st.set_page_config(layout="wide")

pg = st.navigation(
    [
        st.Page("cancer_inference.py", title="Sarcoma Score on New Samples"),
        st.Page("slide_heatmaps.py", title="Slide Heatmaps"),
        st.Page("community_explorer.py", title="Community Explorer"),
    ]
)
pg.run()