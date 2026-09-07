"""Embedding a vega-lite chart by hand, which is what makes a click open a new tab.

Streamlit's own chart component strips the loader target out of the spec, so a chart whose
marks carry an href navigates the app itself instead of opening a tab. Embedding it in an
iframe keeps the option, and the iframe sandbox allows popups.
"""

import streamlit as st

VEGA_CDN = ("https://cdn.jsdelivr.net/npm/vega@5", "https://cdn.jsdelivr.net/npm/vega-lite@6",
            "https://cdn.jsdelivr.net/npm/vega-embed@7")

EMBED_TEMPLATE = """
<div id="vis"></div>
<div id="fallback">{fallback}</div>
{scripts}
<script>
  if (window.vegaEmbed) {{
    document.getElementById("fallback").remove();
    vegaEmbed("#vis", {spec}, {{actions: false, loader: {{target: "_blank"}}}});
  }}
</script>
"""


def embed(chart, fallback=""):
    """One chart, links and all; `fallback` is shown when vega cannot be loaded.

    The chart must carry a pixel width and height - they size the iframe, which does not
    grow with its content, so this fits a grid of images and not much else: axes and labels
    fall outside a chart's own size, and an iframe too small for them scrolls.

    st.iframe, not components.v1.html: same srcdoc iframe and same sandbox, but html is
    removed after 2026-06-01. Sizes must be ints, a grid height is a float.
    """
    st.iframe(
        EMBED_TEMPLATE.format(
            spec=chart.to_json(indent=None),
            fallback=fallback,
            scripts="".join(f'<script src="{src}"></script>' for src in VEGA_CDN),
        ),
        height=round(chart.height) + 30,
        width=round(chart.width) + 30,
    )
