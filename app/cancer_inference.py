import pickle
import sys
from pathlib import Path
import altair as alt
import h5py
import numpy as np
import pandas as pd
import streamlit as st

# pca_model.pkl/min_max_norm.pkl were pickled with `linear_transformers` as a
# top-level module; unpickling needs it importable as such regardless of cwd.
sys.path.insert(0, str(Path(__file__).parent))
from cryptic import CANCER_TYPES  # noqa: E402

alt.data_transformers.disable_max_rows()


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def compute_sarcoma_scores(h5_files):
    """PCA -> rotation -> min-max norm, mirroring linear_transformers pipeline in sarcomics_wsi.
    Each h5 file holds one case's embedding; case id is the filename without extension (no "ids" dataset).
    """
    ids = []
    embeddings = []
    for h5_file in h5_files:
        ids.append(Path(h5_file.name).stem[:12])
        with h5py.File(h5_file, "r") as f:
            embeddings.append(np.expand_dims(f["features"][:], axis=0))
    embeddings = np.vstack(embeddings)

    data_dir = Path(__file__).parent / "data"
    pca = load_pickle(data_dir / "pca_model.pkl")
    rotation = load_pickle(data_dir / "rotation_matrix.pkl")
    normaliser = load_pickle(data_dir / "min_max_norm.pkl")

    pcs = pca.transform(embeddings)[:, :2]
    rotated = -pcs @ rotation
    scores = normaliser.transform(-rotated[:, 1].reshape(-1, 1)).flatten()
    return pd.DataFrame({"case_id": ids, "sarcoma_score": scores})


def score_color(p):
    """Color by empirical percentile rank: green if not significant, orange/red/darker red as p drops."""
    if p < 0.001:
        return "darkred"
    if p < 0.01:
        return "red"
    if p < 0.05:
        return "orange"
    return "green"


def plot_boxplot(hist_df, new_df):
    """Boxplot per histological type, as l.44 of extract_sarcomas_scores.py (no palette/stat annotations), with new scores overlaid."""
    order = (
        hist_df.groupby("cancer_type")["sarcoma_score"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    box = alt.Chart(hist_df).mark_boxplot().encode(
        y=alt.Y("cancer_type:N", sort=order),
        x=alt.X("sarcoma_score:Q"),
        color=alt.Color("cancer_type:N", legend=None),
        tooltip=["case_id:N", "sarcoma_score:Q"],
    )
    new_df = new_df.assign(point_color=new_df["empirical_percentile_rank"].apply(score_color))
    points = alt.Chart(new_df).mark_point(
        size=100, filled=True, shape="cross", stroke="black", strokeWidth=1, opacity=1
    ).encode(
        y="cancer_type:N",
        x="sarcoma_score:Q",
        color=alt.Color("point_color:N", scale=None, legend=None),
        tooltip=["case_id:N", "sarcoma_score:Q"],
    )
    return box + points


def main():
    st.title("Sarcoma score inference")
    if "submitted" not in st.session_state:
        st.session_state.submitted = False

    with st.expander("Input", expanded=not st.session_state.submitted):
        with st.form("inference_form"):
            h5_files = st.file_uploader(
                "Upload h5 file(s)",
                type="h5",
                accept_multiple_files=True,
                help=(
                    "Upload the h5 file(s) containing the TITAN slide embedding for each WSI "
                    "(not the patch/tile-level embeddings).\n\n"
                    "Generate these with [TRIDENT](https://github.com/mahmoodlab/TRIDENT/tree/main), "
                    "e.g. `python run_batch_of_slides.py --task all --wsi_dir wsis --job_dir results "
                    "--patch_encoder conch_v15 --mag 20 --patch_size 512 --slide_encoder titan`.\n\n"
                    "The slide embedding h5 file is written to "
                    "`results/slide_features_titan/<slide_id>.h5`."
                ),
            )
            cancer_type = st.selectbox(
                "Cancer type",
                sorted(CANCER_TYPES),
                help=(
                    "TCGA study abbreviations, see "
                    "[TCGA study abbreviations](https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/tcga-study-abbreviations)."
                ),
            )
            submitted = st.form_submit_button("Submit")

    if submitted:
        if not h5_files:
            st.error("Upload at least one h5 file.")
        else:
            st.session_state.submitted = True
            st.rerun()

    if st.session_state.submitted:
        if not h5_files:
            st.session_state.submitted = False
        else:
            df = compute_sarcoma_scores(h5_files)
            df["cancer_type"] = cancer_type

            data_dir = Path(__file__).parent / "data"
            hist_df = pd.read_csv(data_dir / "sarcoma_score_inference.tsv", sep="\t").rename(
                columns={"histological_type": "cancer_type"}
            )
            subset = hist_df.loc[hist_df.cancer_type == cancer_type, "sarcoma_score"]

            reference = hist_df["sarcoma_score"] if cancer_type == "Unknown" else subset
            df["empirical_percentile_rank"] = df["sarcoma_score"].apply(
                lambda score: ((reference >= score).sum() - 0.5 * (reference == score).sum()) / len(reference)
            )

            styled = (
                df.rename(
                    columns={
                        "case_id": "Case ID",
                        "sarcoma_score": "Sarcoma Score",
                        "cancer_type": "Cancer Type",
                        "empirical_percentile_rank": "Empirical percentile rank",
                    }
                )
                .style.apply(
                    lambda row: [
                        f"color: {score_color(row['Empirical percentile rank'])}; font-weight: bold"
                        if col in ("Sarcoma Score", "Empirical percentile rank")
                        else ""
                        for col in row.index
                    ],
                    axis=1,
                )
            )
            st.dataframe(styled, hide_index=True)
            if cancer_type != "Unknown":
                st.altair_chart(plot_boxplot(hist_df, df), use_container_width=True)

main()
