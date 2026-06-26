import altair as alt
import pandas as pd

def retrieve_data(data_path, img_path):
    df = pd.read_csv(f"{data_path}/sarcoma_score_heatmaps.tsv", sep="\t")
    df['case_id_short'] = df.case_id
    df.case_id = [x.split('_')[1] for x in df.image]
    df['image'] = df['image'].apply(lambda x: f"{img_path}/{x}")
    df['url'] = [f"{img_path}/{x}_heatmap_overlay_only_False.png" for x in df.case_id]
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
        href='url',
    ).add_params(
        click, brush
    )

    legend = alt.Chart(df, height=190).mark_point().encode(
        alt.Y('histological_type').axis(orient='right'),
        color=color
    ).add_params(
        selection
    )

    (points | legend)

def main():
    df = retrieve_data("app/data", "app/static")
    plot_slide_heatmap(df)

main()