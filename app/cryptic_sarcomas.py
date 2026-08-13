"""Cryptic sarcomas of one TCGA cancer type; a row click opens that sample's page."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from cryptic import CANCER_TYPES, cases, images  # noqa: E402

SAMPLE_PAGE = "cryptic_sarcoma_sample.py"


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
    # the samples the community explorer holds images for; the others only get placeholders
    detailed = set(images("tiles").case_id)
    table = pd.DataFrame({
        "Sample": df.case_id.values,
        "Cancer type": df.histological_type.values,
        "Sarcoma score": df.sarcoma_score.values,
        "Z score": df.z_score.values,
        "Details": df.case_id.isin(detailed).values,
    })

    st.caption(f"{len(table)} sample(s), highest z score first. Click a row to open its page.")
    event = st.dataframe(
        table,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Sarcoma score": st.column_config.NumberColumn(format="%.3f"),
            "Z score": st.column_config.NumberColumn(format="%.2f"),
            "Details": st.column_config.CheckboxColumn(help="Tiles and slide heatmap available."),
        },
    )
    selected = event.selection["rows"]
    if selected:
        st.query_params["case"] = table.iloc[selected[0]]["Sample"]
        st.switch_page(SAMPLE_PAGE)


main()
