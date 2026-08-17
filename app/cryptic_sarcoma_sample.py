"""One cryptic sarcoma sample: its community composition, representative tiles and slide heatmap.

The sample is read from the `case` query parameter, so a sample page can be linked, opened
in its own tab or reloaded.

The images and the composition are placeholders wherever the sample has none of its own -
the layout is what this page is for until the per-sample data is generated.
"""

import random
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from cryptic import IMG_PATH, cases, community_colors, images, z_color  # noqa: E402

LIST_PAGE = "cryptic_sarcomas.py"
TILE_COLUMNS = 4  # tiles per community, one row of them each


def community_percentages(case_id, tiles):
    """Share of the sample's tiles in each community, as (percentages, is_real).

    ponytail: placeholder. The per-sample community composition is not computed anywhere
    yet, so a sample with no tiles gets a spread seeded by its case id - stable across
    reruns, but made up. Swap this for the real table once it exists.
    """
    own = tiles[tiles.case_id == case_id]
    if not own.empty:
        counts = own.community.value_counts().sort_index()
        return counts / counts.sum() * 100, True
    communities = sorted(tiles.community.unique())
    rng = random.Random(case_id)
    weights = [rng.random() for _ in communities]
    return pd.Series([100 * w / sum(weights) for w in weights], index=communities), False


def plot_communities(percentages, colors):
    """Composition as bars, colored as the tile borders below them."""
    order = sorted(percentages.index)
    df = pd.DataFrame({"community": [str(c) for c in percentages.index],
                       "percentage": percentages.values})
    bars = alt.Chart(df, height=alt.Step(24)).mark_bar(cornerRadiusEnd=4).encode(
        alt.X("percentage:Q").title("% of tiles"),
        # by community, not by size, and as numbers: a nominal sort would put 10 before 2
        alt.Y("community:N").sort([str(c) for c in order]).title("community"),
        alt.Color("community:N").scale(
            domain=[str(c) for c in order],
            range=[colors[c] for c in order],
        ).legend(None),
        tooltip=[alt.Tooltip("community:N"),
                 alt.Tooltip("percentage:Q", format=".1f", title="% of tiles")],
    )
    labels = bars.mark_text(align="left", dx=4, color="gray").encode(
        text=alt.Text("percentage:Q", format=".1f")
    )
    return bars + labels


def tile_row(paths, color):
    """One row of tiles bordered in their community color.

    Raw html rather than st.image, which has no border option; the files are reachable
    because static serving is on (see .streamlit/config.toml).
    """
    st.html(
        f'<div style="display:grid;grid-template-columns:repeat({TILE_COLUMNS},1fr);gap:8px">'
        + "".join(f'<img src="{IMG_PATH}/{path}" style="width:100%;border:4px solid {color};'
                  'border-radius:4px;box-sizing:border-box">' for path in paths)
        + "</div>"
    )


def representative(case_id, df, community=None):
    """Images of the sample, borrowed from the same community when it has none of its own.

    Returns (images, is_real); the borrowed ones keep the page laid out while the per-sample
    images are missing.
    """
    pool = df if community is None else df[df.community == community]
    own = pool[pool.case_id == case_id]
    return (own.image, True) if not own.empty else (pool.image, False)


def show_tiles(case_id, tiles, percentages, colors):
    st.subheader("Representative tiles")
    for community in sorted(percentages.index):
        percentage = percentages[community]
        paths, own = representative(case_id, tiles, community)
        st.markdown(f"**Community {community}** — {percentage:.1f}% of the tiles"
                    + ("" if own else " _(placeholder)_"))
        paths = paths.head(TILE_COLUMNS).tolist()
        if paths:
            tile_row(paths, colors[community])
        else:
            st.info(f"No tile for community {community}.")


def show_slide_heatmap(case_id, slides):
    st.subheader("Slide heatmap")
    paths, own = representative(case_id, slides)
    if paths.empty:
        st.info("No slide heatmap yet.")
        return
    st.image(f"{IMG_PATH}/{paths.iloc[0]}", width="stretch",
             caption=None if own else "Placeholder, this is another sample's heatmap.")
    if own:
        url = slides[slides.case_id == case_id].iloc[0].get("viewer_url")
        if isinstance(url, str):
            st.markdown(f"[Open the slide in the IDC viewer]({url})")


def main():
    # the page opens on its header, without the padding streamlit leaves under the toolbar
    st.html("<style>.stMainBlockContainer {padding-top: 3.5rem;}</style>")
    case_id = st.query_params.get("case")
    df = cases()
    # the title shares the row with the button rather than taking one of its own
    back, heading, _ = st.columns(3, vertical_alignment="center")
    if back.button("← Back to the sample list"):
        st.query_params.clear()
        st.switch_page(LIST_PAGE)
    if case_id is None or case_id not in set(df.case_id):
        st.error("Pick a sample from the cryptic sarcomas list.")
        return

    row = df[df.case_id == case_id].iloc[0]
    heading.html(f'<h1 style="text-align:center;margin:0;padding:0">{case_id}</h1>')
    left, middle, right = st.columns(3)
    left.metric("Cancer type", row.histological_type)
    middle.metric("Sarcoma score", f"{row.sarcoma_score:.3f}")
    # st.metric only ever colors its delta, so the z score is drawn in its shape instead
    right.html(
        '<div style="font-size:0.875rem;opacity:0.6">Z score</div>'
        f'<div style="font-size:2.25rem;font-weight:600;line-height:1.2;'
        f'color:{z_color(row.z_score)}">{row.z_score:.2f}</div>'
    )

    tiles, slides = images("tiles"), images("slides")
    percentages, real = community_percentages(case_id, tiles)
    # over every community, not only the sample's, or its colors would shift with its content
    colors = community_colors(tiles.community.unique())
    with st.sidebar:
        st.markdown("**Communities**")
        st.altair_chart(plot_communities(percentages, colors), width="stretch")
        if not real:
            st.caption("Placeholder composition, seeded by the case id.")

    tiles_column, heatmap_column = st.columns(2)
    with tiles_column:
        show_tiles(case_id, tiles, percentages, colors)
    with heatmap_column:
        show_slide_heatmap(case_id, slides)


main()
