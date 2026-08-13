"""Cryptic sarcomas of one TCGA cancer type; a row click opens that sample's page."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from cryptic import CANCER_TYPES, Z_SCORE, cases  # noqa: E402

# relative to the current page, so it survives the app being served under a base path
SAMPLE_PAGE = "cryptic_sarcoma_sample"


def main():
    st.title("Cryptic sarcomas")
    cancer_type = st.sidebar.selectbox(
        "Cancer type",
        ["All"] + sorted(CANCER_TYPES),
        help=(
            "TCGA study abbreviations, see "
            "[TCGA study abbreviations](https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/tcga-study-abbreviations)."
        ),
    )
    df = cases()
    if cancer_type != "All":
        df = df[df.histological_type == cancer_type]
    if df.empty:
        st.info(f"No sample of type {cancer_type}.")
        return

    df = df.sort_values("z_score", ascending=False)
    table = pd.DataFrame({
        # a link, not a row selection: a dataframe link is what opens in a new tab
        "Sample": SAMPLE_PAGE + "?case=" + df.case_id.values,
        "Cancer type": df.histological_type.values,
        "Sarcoma score": df.sarcoma_score.values,
        "Z score": df.z_score.values,
    })

    st.caption(f"{len(table)} sample(s) scoring z ≥ {Z_SCORE}, highest first. "
               "Click a sample to open its page in a new tab.")
    st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        column_config={
            "Sample": st.column_config.LinkColumn(display_text=r"\?case=(.*)"),
            "Sarcoma score": st.column_config.NumberColumn(format="%.3f"),
            "Z score": st.column_config.NumberColumn(format="%.2f"),
        },
    )


main()
