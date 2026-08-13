"""Smallest check that the cryptic sarcoma list filters and that a sample page renders.

The row click itself is not reachable from AppTest (st.dataframe selections are not
scriptable), so the sample page is driven through the `case` query parameter it reads.

Run it from the repo root: python test_cryptic_sarcomas.py
"""
import sys

from streamlit.testing.v1 import AppTest

sys.path.insert(0, "app")
from cryptic import Z_SCORE, cases, images  # noqa: E402


def table(at):
    """Rows of the sample list."""
    return at.dataframe[0].value


def test_list():
    at = AppTest.from_file("app/cryptic_sarcomas.py", default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]
    everything = table(at)
    assert {"Sample", "Cancer type", "Sarcoma score", "Z score"} <= set(everything.columns)
    # the sample cell is the link its page opens from, not the bare case id
    assert everything["Sample"].str.startswith("cryptic_sarcoma_sample?case=TCGA-").all()
    # highest z score first, so the interesting samples are on top
    assert everything["Z score"].is_monotonic_decreasing
    # cryptic sarcomas only, the rest of the pancancer cases are not listed
    assert everything["Z score"].min() >= Z_SCORE, everything["Z score"].min()

    at.sidebar.selectbox[0].set_value("BRCA").run()
    filtered = table(at)
    assert set(filtered["Cancer type"]) == {"BRCA"}
    assert 0 < len(filtered) < len(everything)

    # the studies the project leaves out are not offered at all
    assert not {"ACC", "MESO", "THYM", "GBM", "LGG", "SKCM", "UVM", "DLBC", "LAML",
                "PCPG", "TGCT"} & set(at.sidebar.selectbox[0].options)

    # a type absent from the data leaves an info box and no table
    at.sidebar.selectbox[0].set_value("Unknown").run()
    assert not at.dataframe, len(at.dataframe)
    assert at.info


def test_sample():
    slides, tiles = images("slides"), images("tiles")
    at = AppTest.from_file("app/cryptic_sarcoma_sample.py", default_timeout=300)
    # a cryptic sample holding both a slide heatmap and tiles of its own, no placeholder
    with_images = slides[slides.case_id.isin(tiles.case_id)].case_id
    case = with_images[with_images.isin(cases().case_id)].iloc[0]
    at.query_params["case"] = case
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    # cancer type, sarcoma score, z score
    assert len(at.metric) == 3, len(at.metric)
    assert at.get("image"), "no slide heatmap"
    # the composition donut sits in the sidebar, next to nothing else
    assert at.sidebar.get("vega_lite_chart"), "no community chart"
    # one row of tiles per community of the sample, and its own tiles, not borrowed ones
    own = tiles[tiles.case_id == case]
    rows = at.get("html")
    assert len(rows) == own.community.nunique(), (len(rows), own.community.nunique())
    assert all(case in row.body for row in rows), "borrowed tiles for a sample that has its own"

    # no sample selected is a message, not a crash
    at.query_params.clear()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.error

    # so is a case that exists but is not a cryptic sarcoma
    at.query_params["case"] = "TCGA-2F-A9KO"
    at.run()
    assert at.error, "a case below the z score cut must not have a page"


if __name__ == "__main__":
    test_list()
    test_sample()
    print("OK")
