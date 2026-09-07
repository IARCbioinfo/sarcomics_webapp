import altair as alt
import pandas as pd
import streamlit as st

def retrieve_data(data_path, img_path):
    df = pd.read_csv(f"{data_path}/sarcoma_score_heatmaps.tsv", sep="\t")
    df['case_id_short'] = df.case_id
    df.case_id = [x.split('_')[1] for x in df.image]
    df['image'] = df['image'].apply(lambda x: f"{img_path}/{x}")
    return df

def plot_slide_heatmap(df):
    brush = alt.selection_interval()
    selection = alt.selection_point(fields=['histological_type'])
    click = alt.selection_point(empty=False)
    color = (
        alt.when(selection)
        .then(alt.Color("histological_type:N").legend(None))
        .otherwise(alt.value("lightgray"))
    )

    points = alt.Chart(df, width=500, height=400).mark_point().encode(
        x='sarcoma_score_wsi',
        y='sarcoma_score_rnaseq',
        color=color,
        tooltip=['case_id_short', 'histological_type', 'image'],
        fill=alt.when(click).then(alt.value('red')),
    ).add_params(
        click, brush
    )

    legend = alt.Chart(df, height=190).mark_point().encode(
        alt.Y('histological_type').axis(orient='right'),
        color=color
    ).add_params(
        selection
    )

    return points | legend

def main():
    st.markdown(
        "<style>#vg-tooltip-element img {max-width: min(350px, 40vw); max-height: min(250px, 40vh);}</style>",
        unsafe_allow_html=True,
    )
    df = retrieve_data("app/data/5", "app/static/5/thumbnails")
    # No use_container_width: stretching to container width forces Vega to
    # refit the concatenated chart and clips the legend's right-oriented axis labels.
    st.altair_chart(plot_slide_heatmap(df))

main()