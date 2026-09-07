"""Smallest check that the sidebar barplots describe the community that is selected.

Run it from the repo root: python test_community_sidebar.py
"""
import io

import pyarrow as pa
from streamlit.testing.v1 import AppTest


def barplots(at):
    """The dataframes of the sidebar barplots: cancer subtypes, then one per cell taxonomy."""
    charts = [e for e in at.sidebar if getattr(e, "type", "") == "vega_lite_chart"]
    return [pa.ipc.open_stream(io.BytesIO(c.proto.datasets[0].data.data)).read_pandas()
            for c in charts]


def test():
    at = AppTest.from_file("app/community_explorer.py", default_timeout=300).run()
    assert not at.exception, [e.value for e in at.exception]

    plots = barplots(at)
    assert len(plots) == 3, len(plots)
    for plot in plots:  # each is a full composition of the community
        assert abs(plot.proportion.sum() - 1) < 1e-6, plot.proportion.sum()
    subtypes = plots[0]
    assert len(subtypes) > 1, subtypes

    # another community is described by its own numbers
    other = int(at.sidebar.selectbox[0].options[2])
    at.sidebar.selectbox[0].set_value(other).run()
    assert not barplots(at)[0].proportion.equals(subtypes.proportion), other


if __name__ == "__main__":
    test()
    print("OK")
