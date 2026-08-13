"""One cryptic sarcoma sample: its slide heatmap, community composition and representative tiles.

The sample is read from the `case` query parameter, so a sample page can be linked or reloaded.
"""

import random
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from cryptic import IMG_PATH, cases, community_color, images  # noqa: E402

LIST_PAGE = "cryptic_sarcomas.py"
TILES_PER_COMMUNITY = 3


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


def plot_communities(percentages):
    df = pd.DataFrame({"community": [str(c) for c in percentages.index],
                       "percentage": percentages.values})
    bars = alt.Chart(df, height=alt.Step(24)).mark_bar(cornerRadiusEnd=4).encode(
        alt.X("percentage:Q").title("% of tiles"),
        alt.Y("community:N").sort("-x").title("community"),
        alt.Color("community:N").scale(
            domain=df.community.tolist(),
            range=[community_color(c) for c in percentages.index],
        ).legend(None),
        tooltip=[alt.Tooltip("community:N"),
                 alt.Tooltip("percentage:Q", format=".1f", title="% of tiles")],
    )
    labels = bars.mark_text(align="left", dx=4, color="gray").encode(
        text=alt.Text("percentage:Q", format=".1f")
    )
    return bars + labels


def tile_strip(paths, color, width=180):
    """A row of tiles bordered in their community color.

    Raw html rather than st.image, which has no border option; the files are reachable
    because static serving is on (see .streamlit/config.toml).
    """
    st.html(
        '<div style="display:flex;flex-wrap:wrap;gap:8px">'
        + "".join(f'<img src="{IMG_PATH}/{path}" style="width:{width}px;'
                  f'border:4px solid {color};border-radius:4px">' for path in paths)
        + "</div>"
    )


def representative_tiles(case_id, community, tiles):
    """Up to 3 tiles of that community, the sample's own if it has any, borrowed otherwise."""
    own = tiles[(tiles.case_id == case_id) & (tiles.community == community)]
    if not own.empty:
        return own.image.head(TILES_PER_COMMUNITY).tolist(), True
    pool = tiles[tiles.community == community]
    return pool.image.head(TILES_PER_COMMUNITY).tolist(), False


def show_slide_heatmap(case_id, slides):
    st.subheader("Slide heatmap")
    own = slides[slides.case_id == case_id]
    if own.empty:
        st.info("No slide heatmap for this sample yet.")
        return
    row = own.iloc[0]
    st.image(f"{IMG_PATH}/{row.image}", width="stretch")
    if isinstance(row.get("viewer_url"), str):
        st.markdown(f"[Open the slide in the IDC viewer]({row.viewer_url})")


def main():
    case_id = st.query_params.get("case")
    df = cases()
    if st.button("← Back to the sample list"):
        st.query_params.clear()
        st.switch_page(LIST_PAGE)
    if case_id is None or case_id not in set(df.case_id):
        st.error("Pick a sample from the cryptic sarcomas list.")
        return

    row = df[df.case_id == case_id].iloc[0]
    st.title(case_id)
    left, middle, right = st.columns(3)
    left.metric("Cancer type", row.histological_type)
    middle.metric("Sarcoma score", f"{row.sarcoma_score:.3f}")
    right.metric("Z score", f"{row.z_score:.2f}")

    tiles, slides = images("tiles"), images("slides")
    percentages, real = community_percentages(case_id, tiles)
    if not real:
        st.warning("Placeholder: this sample has no tiles yet, so the composition below is "
                   "made up and the tiles are borrowed from other samples of each community.")

    left_column, right_column = st.columns(2)
    with left_column:
        show_slide_heatmap(case_id, slides)
    with right_column:
        st.subheader("Communities")
        st.altair_chart(plot_communities(percentages), width="stretch")

    st.subheader("Representative tiles")
    for community, percentage in percentages.items():
        paths, own = representative_tiles(case_id, community, tiles)
        st.markdown(f"**Community {community}** — {percentage:.1f}% of the tiles"
                    + ("" if own else " _(borrowed)_"))
        if paths:
            tile_strip(paths, community_color(community))
        else:
            st.info(f"No tile for community {community}.")


main()
