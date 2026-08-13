"""Bits shared by the cryptic sarcoma pages: the TCGA type list, the tsv loaders, community colors.

Not a page - it holds no streamlit calls, so it can be imported without running anything.
"""

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data"
IMG_PATH = "app/static"

# TCGA study abbreviations, https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/tcga-study-abbreviations
CANCER_TYPES = [
    "GBM", "SKCM", "PAAD", "LGG", "HNSC", "DLBC", "UVM", "READ", "PCPG",
    "MESO", "COAD", "BRCA", "ESCA", "ACC", "PRAD", "STAD", "LUSC", "LIHC",
    "THYM", "BLCA", "THCA", "CESC", "LUAD", "CHOL", "TGCT", "KICH", "OV",
    "KIRP", "Unknown",
]

# observable10, the palette the cell proportion bars already use
PALETTE = ["#4269d0", "#efb118", "#ff725c", "#6cc5b0", "#3ca951", "#ff8ab7",
           "#a463f2", "#97bbf5", "#9c6b4e", "#9498a0"]


def community_color(community):
    """Same color for a community wherever it is drawn."""
    return PALETTE[int(community) % len(PALETTE)]


def cases():
    """One row per pancancer case: case_id, wsi_id, histological_type, sarcoma_score, z_score."""
    return pd.read_csv(DATA_PATH / "cryptic_sarcomas.tsv", sep="\t")


def images(kind):
    """Tiles or slide heatmaps of every community, one row per image, with their case id.

    `kind` is "tiles" or "slides". Not cached, as in the community explorer: @st.cache_data
    keys on arguments only and kept serving stale rows after the tsvs were regenerated.
    """
    df = pd.read_csv(DATA_PATH / f"{kind}_cryptic_sarcoma.tsv", sep="\t")
    df["case_id"] = [x[:12] for x in df.image]
    return df
