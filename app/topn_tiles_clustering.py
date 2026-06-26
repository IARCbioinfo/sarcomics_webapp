import altair as alt
import pandas as pd

def retrieve_data(data_path, img_path):
    df = pd.read_csv(f"{data_path}/topn_integrated_gradients_tiles_clustering.tsv", sep="\t")
    df['image'] = df['image'].apply(lambda x: f"{img_path}/{x}")
    df['case_id'] = df['case_id'].apply(lambda x: x[:12])
    return df

def plot_figure(df):
    points = alt.Chart(df, width=1000, height=500).mark_point().encode(
        x='x:Q',
        y='y:Q',
        color=alt.Color('leiden:N').title('Cluster labels'),
        tooltip=['case_id:N', 'histological_type:N'],
    )

    points


def main():
    df = retrieve_data("app/data", "app/static")
    plot_figure(df)

main()