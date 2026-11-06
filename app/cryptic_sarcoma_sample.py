"""One cryptic sarcoma sample: its community composition, representative tiles and slide heatmap.

The sample is read from the `case` query parameter, so a sample page can be linked, opened
in its own tab or reloaded.

Everything shown belongs to the sample itself: the composition comes from its leiden
embeddings row, the tiles and the heatmap from its own files. 14 of the 105 listed samples
have none of the three, and say so rather than borrowing another sample's images.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
from cryptic import (TYPE_COLORS, cases, community_colors, community_title,  # noqa: E402
                     community_types, compositions, sample_slides, sample_tiles, z_color)
LIST_PAGE = "cryptic_sarcomas.py"
# relative to the current page, as the list page links to this one
EXPLORER_PAGE = "community_explorer"
TILE_COLUMNS = 3  # tiles per community, one row of them each


def explorer_url(community):
    """The community explorer, opened on one community."""
    return f"{EXPLORER_PAGE}?community={community}"


def community_percentages(wsi_id, communities):
    """Share of the slide's tiles in each community, or None when the slide has no row.

    The embeddings hold every leiden label; only the communities that got a heatmap are kept
    here, so the bars total less than 100 - the caption under them says by how much.
    """
    slides = compositions()
    if wsi_id not in slides.index:
        return None
    row = slides.loc[wsi_id]
    return pd.Series([row[str(community)] for community in communities], index=communities)


def composition_bars(percentages, colors):
    """Composition as html bars, colored as the tile borders below them, one link each.

    Html rather than a chart: a vega click only opens a new tab from inside an iframe, and
    an iframe in the sidebar is sized in pixels, so it ends up scrolling instead of fitting.
    The scale runs to 100% of the slide's tiles, not to the widest community: scaled to the
    widest, a community holding 1.5% of a slide filled the row and read as most of it.
    """
    rows = "".join(
        f'<a href="{explorer_url(community)}" target="_blank" '
        f'title="Community {community}: {percentage:.1f}% of the slide\'s tiles" '
        'style="display:grid;grid-template-columns:2.5ch 1fr 3.5ch;gap:8px;'
        'align-items:center;text-decoration:none;color:inherit;font-size:0.875rem">'
        f'<span>{community}</span>'
        '<span style="height:16px">'  # the track is transparent, a full-width one reads as a bar
        f'<span style="display:block;height:100%;border-radius:4px;'
        f'width:{percentage:.1f}%;background:{colors[community]}"></span></span>'
        f'<span style="opacity:0.6;text-align:right">{percentage:.1f}</span></a>'
        for community, percentage in percentages.items()
    )
    return f'<div style="display:flex;flex-direction:column;gap:6px">{rows}</div>'


def tile_row(paths, color):
    """One row of tiles bordered in their community color.

    Raw html rather than st.image, which has no border option; the files are reachable
    because static serving is on (see .streamlit/config.toml).
    """
    st.html(
        f'<div style="display:grid;grid-template-columns:repeat({TILE_COLUMNS},1fr);gap:8px">'
        + "".join(f'<img src="{path}" style="width:100%;border:4px solid {color};'
                  'border-radius:4px;box-sizing:border-box">' for path in paths)
        + "</div>"
    )


def show_tiles(own, percentages, colors, types):
    """The sample's own tiles, one row per community it has any in, titled with its type."""
    st.subheader("Representative tiles")
    if own.empty:
        st.info("No tile for this sample.")
        return
    for community, tiles in own.groupby("community"):
        if percentages is None:
            share = ""
        elif percentages[community] < 1:
            share = " — less than 1% of the tiles"
        else:
            share = f" — {percentages[community]:.1f}% of the tiles"
        st.html(f'<strong><a href="{explorer_url(community)}" target="_blank">'
                f'{community_title(community, types)}</a></strong>{share}')
        tile_row(tiles.image.head(TILE_COLUMNS).tolist(), colors[community])


def heatmap(slide, path):
    """One slide heatmap, linked to the slide's IDC viewer page when it has one."""
    img = f'<img src="{path}" style="width:100%">'
    if isinstance(slide.get("viewer_url"), str):
        img = f'<a href="{slide.viewer_url}" target="_blank">{img}</a>'
    st.html(img)


def show_slide_heatmap(case_id, slides):
    """The slide coloured by community type, then by community."""
    own = slides[slides.case_id == case_id]
    if own.empty:
        st.subheader("Slide heatmap")
        st.info("No slide heatmap for this sample.")
        return
    slide = own.iloc[0]
    st.subheader("Community types")
    if isinstance(slide.type_image, str):
        st.caption(f"Tiles coloured by the type of their community: {TYPE_COLORS}.")
        heatmap(slide, slide.type_image)
    else:
        st.info("No community-type heatmap for this sample.")
    st.subheader("Communities")
    heatmap(slide, slide.image)


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

    tiles, slides = sample_tiles(), sample_slides()
    # over every community, not only the sample's, or its colors would shift with its content
    communities = sorted(tiles.community.unique())
    colors = community_colors(communities)
    percentages = community_percentages(row.wsi_id, communities)
    with st.sidebar:
        st.markdown("**Communities**")
        if percentages is None:
            st.info("No community composition for this sample.")
        else:
            st.html(composition_bars(percentages, colors))
            st.caption(f"{percentages.sum():.1f}% of the slide's tiles sit in these communities; "
                       "the rest are unassigned or in communities without a heatmap. "
                       "A community opens in the explorer, in a new tab.")

    tiles_column, heatmap_column = st.columns(2)
    with tiles_column:
        show_tiles(tiles[tiles.case_id == case_id], percentages, colors, community_types())
    with heatmap_column:
        show_slide_heatmap(case_id, slides)


main()
