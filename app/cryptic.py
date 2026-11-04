"""Bits shared by the cryptic sarcoma pages: the TCGA type list, the tsv loaders, community colors.

Not a page - it holds no streamlit calls, so it can be imported without running anything.
"""

from pathlib import Path

import pandas as pd

RUN = "5_cryptic_sarcoma"  # the pipeline run these pages read, data and images alike
DATA_PATH = Path(__file__).parent / "data" / RUN
IMG_PATH = f"app/static/{RUN}"

# TCGA study abbreviations, https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/tcga-study-abbreviations
# ACC, MESO, THYM, GBM, LGG, SKCM, UVM, DLBC, LAML, PCPG and TGCT are left out on purpose:
# they are the studies the project does not report on, so neither a dropdown nor a chart
# built from this list shows them.
CANCER_TYPES = [
    "PAAD", "HNSC", "READ", "COAD", "BRCA", "ESCA", "PRAD", "STAD", "LUSC",
    "LIHC", "BLCA", "THCA", "CESC", "LUAD", "CHOL", "KICH", "OV", "KIRP",
    "Unknown",
]

# matplotlib tab20, indexed by community number as the slide heatmaps are drawn (explainable_WSI
# 695c893), so a community has the same colour here, over the tissue and in every figure
TAB20 = ["#1f77b4", "#aec7e8", "#ff7f0e", "#ffbb78", "#2ca02c", "#98df8a", "#d62728", "#ff9896",
         "#9467bd", "#c5b0d5", "#8c564b", "#c49c94", "#e377c2", "#f7b6d2", "#7f7f7f", "#c7c7c7",
         "#bcbd22", "#dbdb8d", "#17becf", "#9edae5"]


def z_color(z_score):
    """How far above the cryptic sarcoma cut a sample scores: green below it, then orange, red."""
    if z_score >= 3:
        return "red"
    return "orange" if z_score >= Z_SCORE else "green"


def community_colors(communities):
    """Color of every community, keyed by community: the community number indexes the palette."""
    return {community: TAB20[int(community) % len(TAB20)] for community in communities}


Z_SCORE = 2  # a case is a cryptic sarcoma from that z score up


def cases():
    """One row per cryptic sarcoma: case_id, wsi_id, histological_type, sarcoma_score, z_score.

    The tsv holds every pancancer case; only those scoring z >= 2 are cryptic sarcomas, and
    the pages show nothing else, so the cut is made here rather than in each of them.
    """
    df = pd.read_csv(DATA_PATH / "cryptic_sarcomas.tsv", sep="\t")
    return df[df.z_score >= Z_SCORE]


def sample_tiles():
    """Representative tiles of every cryptic sarcoma, one row per tile.

    Per sample, unlike the community-level `tiles.tsv` the explorer reads: about 25 tiles a
    slide, each already labelled with the community it was drawn from.

    Not cached, as in the community explorer: @st.cache_data keys on arguments only and kept
    serving stale rows after the tsvs were regenerated.
    """
    df = pd.read_csv(DATA_PATH / "cryptic_sarcomas_tiles.tsv", sep="\t")
    df["image"] = f"{IMG_PATH}/cryptic_tiles/" + df.tile
    return df


def sample_slides():
    """Slide heatmap of every cryptic sarcoma, one row per slide, `viewer_url` from idc_links."""
    df = pd.read_csv(DATA_PATH / "cryptic_sarcoma_slides.tsv", sep="\t")
    df["image"] = f"{IMG_PATH}/thumbnails/" + df.heatmap
    return df


def compositions():
    """Percentage of each leiden community over a slide's tiles, indexed by wsi_id.

    Holds every leiden label, the noise (-1) and the communities that were not kept for the
    heatmaps included, so a row sums to 100 while the communities shown sum to less.
    """
    return pd.read_csv(DATA_PATH / "cryptic_sarcomas_leiden_embeddings.tsv",
                       sep="\t").set_index("wsi_id")
