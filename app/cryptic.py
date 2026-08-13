"""Bits shared by the cryptic sarcoma pages: the TCGA type list, the tsv loaders, community colors.

Not a page - it holds no streamlit calls, so it can be imported without running anything.
"""

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data"
IMG_PATH = "app/static"

# TCGA study abbreviations, https://gdc.cancer.gov/resources-tcga-users/tcga-code-tables/tcga-study-abbreviations
# ACC, MESO, THYM, GBM, LGG, SKCM, UVM, DLBC, LAML, PCPG and TGCT are left out on purpose:
# they are the studies the project does not report on, so neither a dropdown nor a chart
# built from this list shows them.
CANCER_TYPES = [
    "PAAD", "HNSC", "READ", "COAD", "BRCA", "ESCA", "PRAD", "STAD", "LUSC",
    "LIHC", "BLCA", "THCA", "CESC", "LUAD", "CHOL", "KICH", "OV", "KIRP",
    "Unknown",
]

# observable10, the palette the cell proportion bars already use
PALETTE = ["#4269d0", "#efb118", "#ff725c", "#6cc5b0", "#3ca951", "#ff8ab7",
           "#a463f2", "#97bbf5", "#9c6b4e", "#9498a0"]


def community_color(community):
    """Same color for a community wherever it is drawn."""
    return PALETTE[int(community) % len(PALETTE)]


Z_SCORE = 2  # a case is a cryptic sarcoma from that z score up


def cases():
    """One row per cryptic sarcoma: case_id, wsi_id, histological_type, sarcoma_score, z_score.

    The tsv holds every pancancer case; only those scoring z >= 2 are cryptic sarcomas, and
    the pages show nothing else, so the cut is made here rather than in each of them.
    """
    df = pd.read_csv(DATA_PATH / "cryptic_sarcomas.tsv", sep="\t")
    return df[df.z_score >= Z_SCORE]


def images(kind):
    """Tiles or slide heatmaps of every community, one row per image, with their case id.

    `kind` is "tiles" or "slides". Not cached, as in the community explorer: @st.cache_data
    keys on arguments only and kept serving stale rows after the tsvs were regenerated.
    """
    df = pd.read_csv(DATA_PATH / f"{kind}_cryptic_sarcoma.tsv", sep="\t")
    df["case_id"] = [x[:12] for x in df.image]
    return df
