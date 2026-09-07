"""Smallest check that the cryptic sarcoma list filters and that a sample page renders.

The row click itself is not reachable from AppTest (st.dataframe selections are not
scriptable), so the sample page is driven through the `case` query parameter it reads.

Run it from the repo root: python test_cryptic_sarcomas.py
"""
import re
import sys

from streamlit.testing.v1 import AppTest

sys.path.insert(0, "app")
from cryptic import (Z_SCORE, cases, community_colors, compositions,  # noqa: E402
                     sample_slides, sample_tiles, z_color)


def test_community_colors():
    # tab10 in the order of the communities, as the slide heatmaps were drawn: 1 is blue,
    # 3 green, 6 purple, 11 gray - checked against the overlays in app/static
    colors = community_colors(sample_tiles().community.unique())
    assert [colors[c] for c in (1, 3, 6, 11)] == ["#1f77b4", "#2ca02c", "#9467bd", "#7f7f7f"]


def test_z_color():
    assert [z_color(z) for z in (1.99, 2, 2.99, 3, 7)] == [
        "green", "orange", "orange", "red", "red"]


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

    # the z score column carries the same bands as the sample page
    css = at.dataframe[0].proto.arrow_data.styler.styles
    assert all(f"color: {z_color(z)}" in css for z in everything["Z score"])
    assert "color: green" not in css, "nothing under the cut is listed, so nothing is green"

    # the studies the project leaves out are not offered at all
    assert not {"ACC", "MESO", "THYM", "GBM", "LGG", "SKCM", "UVM", "DLBC", "LAML",
                "PCPG", "TGCT"} & set(at.sidebar.selectbox[0].options)

    # a type absent from the data leaves an info box and no table
    at.sidebar.selectbox[0].set_value("Unknown").run()
    assert not at.dataframe, len(at.dataframe)
    assert at.info


def composition(at):
    """The sidebar composition bars, as {community: (percentage, url)}, read from their html."""
    html = "".join(e.body for e in at.sidebar if getattr(e, "type", "") == "html")
    bars = re.findall(r'href="([^"]*community=(\d+))"[^>]*?: ([\d.]+)% of', html)
    return {int(community): (float(percentage), url)
            for url, community, percentage in bars}


def test_sample():
    slides, tiles = sample_slides(), sample_tiles()
    at = AppTest.from_file("app/cryptic_sarcoma_sample.py", default_timeout=300)
    # a cryptic sample holding both a slide heatmap and tiles of its own
    with_images = slides[slides.case_id.isin(tiles.case_id)].case_id
    case = with_images[with_images.isin(cases().case_id)].iloc[0]
    at.query_params["case"] = case
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    # cancer type and sarcoma score; the z score is html, so it can carry its color
    assert len(at.metric) == 2, len(at.metric)
    z_score = cases().set_index("case_id").z_score[case]
    z_block = [e for e in at.get("html") if "Z score" in e.body]
    assert len(z_block) == 1 and f"color:{z_color(z_score)}" in z_block[0].body, z_block
    assert at.get("image"), "no slide heatmap"
    # one row of tiles per community of the sample, and its own tiles, not borrowed ones
    own = tiles[tiles.case_id == case]
    rows = [e for e in at.get("html") if "<img" in e.body]
    assert len(rows) == own.community.nunique(), (len(rows), own.community.nunique())
    assert all(case in row.body for row in rows), "borrowed tiles for a sample that has its own"
    # the bars are the sample's own embeddings row, not a spread made up from its case id
    bars = composition(at)
    row = compositions().loc[cases().set_index("case_id").wsi_id[case]]
    assert bars, "no community bars"
    # every community links to its explorer page, bars and tile headings alike
    headings = "".join(e.body for e in at.get("html"))
    for community, (percentage, url) in bars.items():
        assert abs(percentage - row[str(community)]) < 0.05, (community, percentage)
        assert url == f"community_explorer?community={community}", url
        assert f'href="{url}" target="_blank"' in headings, (community, url)

    # a listed sample with no data of its own says so rather than borrowing another's
    without = sorted(set(cases().case_id) - set(tiles.case_id))
    assert without, "every sample has tiles, the empty case is no longer covered"
    at.query_params["case"] = without[0]
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    assert len(at.info) == 3, [i.value for i in at.info]

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
    test_community_colors()
    test_z_color()
    test_list()
    test_sample()
    print("OK")
