"""Smallest check that the cryptic sarcoma list filters and that a sample page renders.

The row click itself is not reachable from AppTest (st.dataframe selections are not
scriptable), so the sample page is driven through the `case` query parameter it reads.

Run it from the repo root: python test_cryptic_sarcomas.py
"""
import sys

from streamlit.testing.v1 import AppTest

sys.path.insert(0, "app")
from cryptic import images  # noqa: E402


def table(at):
    """Rows of the sample list."""
    return at.dataframe[0].value


def test_list():
    at = AppTest.from_file("app/cryptic_sarcomas.py", default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]
    everything = table(at)
    assert {"Sample", "Cancer type", "Sarcoma score", "Z score"} <= set(everything.columns)
    # highest z score first, so the interesting samples are on top
    assert everything["Z score"].is_monotonic_decreasing

    at.sidebar.selectbox[0].set_value("BRCA").run()
    filtered = table(at)
    assert set(filtered["Cancer type"]) == {"BRCA"}
    assert 0 < len(filtered) < len(everything)

    # a type absent from the data leaves an info box and no table
    at.sidebar.selectbox[0].set_value("UVM").run()
    assert not at.dataframe, len(at.dataframe)
    assert at.info


def test_sample():
    slides, tiles = images("slides"), images("tiles")
    at = AppTest.from_file("app/cryptic_sarcoma_sample.py", default_timeout=300)
    # a sample holding both a slide heatmap and tiles of its own, so nothing is a placeholder
    at.query_params["case"] = slides[slides.case_id.isin(tiles.case_id)].case_id.iloc[0]
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    # cancer type, sarcoma score, z score
    assert len(at.metric) == 3, len(at.metric)
    assert at.get("image"), "no slide heatmap"
    # the community bars, and one tile strip per community of the sample
    assert at.get("vega_lite_chart"), "no community chart"
    assert at.get("html"), "no tiles"
    assert not at.warning, [w.value for w in at.warning]

    # no sample selected is a message, not a crash
    at.query_params.clear()
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.error


if __name__ == "__main__":
    test_list()
    test_sample()
    print("OK")
