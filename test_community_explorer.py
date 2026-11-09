"""Smallest check that the tiles grid pages and stays inside its community.

Run it from the repo root: python test_community_explorer.py
"""
import io

import pyarrow as pa
from streamlit.testing.v1 import AppTest


def tiles_grid(at):
    """Rows of the tiles grid, the first vega chart of the main body."""
    chart = [e for e in at.main if getattr(e, "type", "") == "vega_lite_chart"][0]
    data = chart.proto.datasets[0].data.data
    return pa.ipc.open_stream(io.BytesIO(data)).read_pandas()


def test():
    at = AppTest.from_file("app/community_explorer.py", default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]

    community = at.sidebar.selectbox[0].value
    grid = tiles_grid(at)
    assert len(grid) == 24, len(grid)  # community_explorer.PAGE
    assert set(grid.community) == {community}, set(grid.community)

    # another community shows its own tiles
    other = int(at.sidebar.selectbox[0].options[2])
    at.sidebar.selectbox[0].set_value(other).run()
    grid = tiles_grid(at)
    assert len(grid) == 24, len(grid)  # community_explorer.PAGE
    assert set(grid.community) == {other}, set(grid.community)

    # a cryptic sarcoma sample page links here with ?community=N, one link per community
    at = AppTest.from_file("app/community_explorer.py", default_timeout=300)
    at.query_params["community"] = str(other)
    at.run()
    assert at.sidebar.selectbox[0].value == other, at.sidebar.selectbox[0].value
    assert set(tiles_grid(at).community) == {other}, set(tiles_grid(at).community)


if __name__ == "__main__":
    test()
    print("OK")
