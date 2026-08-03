
import altair as alt
import pandas as pd
import streamlit as st
from PIL import Image

DATA_PATH = "app/data"
IMG_PATH = "app/static"
ANNOTATIONS = {"CoNSeP": "consep", "NuCLS": "nucls"}


def cell_percentages_per_community(name):
    """Cell type percentages of each leiden community, one row per community.
    """
    path = f"{DATA_PATH}/leiden_communities_annotations_percentage_{name}.tsv"
    return pd.read_csv(path, sep="\t").set_index("Community")


def aspect(path):
    with Image.open(path) as image:  # lazy, only the header is read
        return image.size[0] / image.size[1]


def retrieve_data():
    """Slides, tiles and sarcoma scores of every community, one row per slide.

    Not cached: the load is 3 tsvs and 300 PNG headers, and @st.cache_data keys on
    arguments only, so it kept serving stale rows after the tsvs were regenerated.
    """
    slides = pd.read_csv(f"{DATA_PATH}/slides.tsv", sep="\t")
    tiles = pd.read_csv(f"{DATA_PATH}/tiles.tsv", sep="\t")
    df = slides.rename(columns={"image": "slide"})
    df["tile"] = tiles.image
    df["case_id"] = [x[:12] for x in df.slide]
    # tile names are <case_id>_<x>_<y>_community_<n>.png
    coords = [x.split("_community")[0].split("_")[-2:] for x in df.tile]
    df[["x", "y"]] = [[int(x), int(y)] for x, y in coords]
    # viewer_url is resolved offline by app/idc_links.py, absent until that has been run
    df["viewer_url"] = slides.get("viewer_url")
    df["tile"] = f"{IMG_PATH}/" + df.tile
    df["slide"] = f"{IMG_PATH}/" + df.slide
    scores = pd.read_csv(f"{DATA_PATH}/sarcoma_score_heatmaps.tsv", sep="\t")
    # inner: cases with no sarcoma score are not shown at all
    df = df.merge(
        scores[["case_id", "histological_type", "sarcoma_score_wsi"]],
        on="case_id", how="inner",
    )
    # slide heatmaps have wildly different shapes (0.68 to 3.53), the layout needs their aspect
    for column in ("tile", "slide"):
        df[f"{column}_aspect"] = [aspect(p) for p in df[column]]
    return df


def plot_cell_proportions(percentages, community, title):
    if community not in percentages.index:
        return None
    row = percentages.loc[community]
    df = pd.DataFrame({"cell_type": percentages.columns, "proportion": row.values / 100})
    bars = alt.Chart(df, height=alt.Step(24)).mark_bar(
        cornerRadiusEnd=4, color="#4269d0"
    ).encode(
        alt.X("proportion:Q").axis(format="%").title(None),
        alt.Y("cell_type:N").sort("-x").title(None),
        tooltip=[alt.Tooltip("cell_type:N", title="cell type"),
                 alt.Tooltip("proportion:Q", format=".1%")],
    )
    labels = bars.mark_text(align="left", dx=4, color="gray").encode(
        text=alt.Text("proportion:Q", format=".1%")
    )
    return (bars + labels).properties(title=f"{title} — community {community}")


def plot_image_grid(df, url, tooltip, href=False, columns=3, size=160, gap=10, max_aspect=1.6):
    """Images on a pixel grid: fixed column pitch, rows only as tall as their tallest image.

    Positions are computed here rather than left to a band scale so the gutters stay even
    whatever shape the images are - slide heatmaps range from portrait to very wide.
    """
    df = df.reset_index(drop=True)
    aspects = df[f"{url}_aspect"].clip(1 / max_aspect, max_aspect)
    widths = [min(size, size * a) for a in aspects]
    heights = [w / a for w, a in zip(widths, aspects)]

    x1, x2, y1, y2 = [], [], [], []
    row_top = 0
    for start in range(0, len(df), columns):
        row_height = max(heights[start:start + columns])
        for i in range(start, min(start + columns, len(df))):
            # centre each image in its cell so gutters read as even
            left = (i - start) * (size + gap) + (size - widths[i]) / 2
            top = row_top + (row_height - heights[i]) / 2
            x1.append(left)
            x2.append(left + widths[i])
            y1.append(top)
            y2.append(top + heights[i])
        row_top += row_height + gap

    df = df.assign(x1=x1, x2=x2, y1=y1, y2=y2)
    width, height = columns * (size + gap) - gap, row_top - gap
    chart = alt.Chart(df).mark_image(cursor="pointer" if href else "default").encode(
        alt.X("x1:Q").axis(None).title(None).scale(domain=[0, width], nice=False),
        alt.X2("x2:Q"),
        alt.Y("y1:Q").axis(None).title(None).scale(domain=[height, 0], nice=False),
        alt.Y2("y2:Q"),
        url=f"{url}:N",
        tooltip=tooltip,
    )
    if href:
        chart = chart.encode(alt.Href("viewer_url:N"))
    return chart.properties(width=width, height=height).configure_view(stroke=None)


VEGA_CDN = ("https://cdn.jsdelivr.net/npm/vega@5", "https://cdn.jsdelivr.net/npm/vega-lite@6",
            "https://cdn.jsdelivr.net/npm/vega-embed@7")

EMBED_TEMPLATE = """
<div id="vis"></div>
<div id="fallback">{fallback}</div>
{scripts}
<script>
  if (window.vegaEmbed) {{
    document.getElementById("fallback").remove();
    // the loader target is what makes a click open a new tab; Streamlit's own chart
    // component strips this option out, which is why the chart is embedded by hand here
    vegaEmbed("#vis", {spec}, {{actions: false, loader: {{target: "_blank"}}}});
  }}
</script>
"""


def image_panel(title, df, url, tooltip, linkable=False, **grid):
    """One image grid. The slides are hyperlinked to their IDC viewer page."""
    st.subheader(title)
    if not linkable:
        st.altair_chart(plot_image_grid(df, url, tooltip, **grid), width="content")
        return

    linked = df.dropna(subset=["viewer_url"])
    missing = len(df) - len(linked)
    if missing:
        st.caption(f"{missing} slide(s) without an IDC link, those are not clickable "
                   "(run `python -m app.idc_links` to resolve them).")
    if linked.empty:
        # an empty grid has a negative height, which renders as a broken empty box
        st.altair_chart(plot_image_grid(df, url, tooltip, **grid), width="content")
        return

    chart = plot_image_grid(linked, url, tooltip, href=True, **grid)
    fallback = "".join(
        f'<a href="{row.viewer_url}" target="_blank"><img src="{getattr(row, url)}" width="120"></a>'
        for row in linked.itertuples()
    )
    # st.iframe, not components.v1.html: same srcdoc iframe and same sandbox (allow-popups,
    # which is what lets a slide open in a new tab), but html is removed after 2026-06-01.
    # Sizes must be ints, the grid height is a float.
    st.iframe(
        EMBED_TEMPLATE.format(
            spec=chart.to_json(indent=None),
            fallback=fallback,
            scripts="".join(f'<script src="{src}"></script>' for src in VEGA_CDN),
        ),
        height=round(chart.height) + 30,
        width=round(chart.width) + 30,
    )


def main():
    df = retrieve_data()
    communities = sorted(df.community.unique())
    community = st.sidebar.selectbox("Community", communities)
    selected = df[df.community == community]

    with st.sidebar:
        for title, name in ANNOTATIONS.items():
            chart = plot_cell_proportions(cell_percentages_per_community(name), community, title)
            if chart is None:
                st.info(f"No {title} annotation for community {community}.")
            else:
                st.altair_chart(chart, width="stretch")

    case = [
        alt.Tooltip("case_id:N", title="case"),
        alt.Tooltip("histological_type:N", title="histological type"),
        alt.Tooltip("sarcoma_score_wsi:Q", title="sarcoma score", format=".2f"),
    ]
    tiles, slides = st.columns(2)
    with tiles:
        image_panel("Tiles", selected, "tile", case + ["x:Q", "y:Q"])
    with slides:
        image_panel("Slide heatmaps", selected, "slide", case, linkable=True,
                    columns=2, size=240)


main()
