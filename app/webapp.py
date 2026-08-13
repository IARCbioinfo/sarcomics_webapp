import streamlit as st

st.set_page_config(layout="wide")

pg = st.navigation(
    [
        st.Page("cancer_inference.py", title="Sarcoma Score on New Samples"),
        st.Page("slide_heatmaps.py", title="Slide Heatmaps"),
        st.Page("community_explorer.py", title="Community Explorer"),
        st.Page("cryptic_sarcomas.py", title="Cryptic Sarcomas"),
        # reached by clicking a sample, not from the nav
        st.Page("cryptic_sarcoma_sample.py", title="Cryptic Sarcoma Sample",
                visibility="hidden"),
    ]
)
pg.run()