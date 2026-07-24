import streamlit as st

pg = st.navigation(
    [
        st.Page("cancer_inference.py", title="Sarcoma Score on New Samples"),
        st.Page("slide_heatmaps.py", title="Slide Heatmaps"),
    ]
)
pg.run()