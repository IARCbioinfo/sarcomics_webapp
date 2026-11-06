"""Copy the pipeline's webapp outputs for the score-building communities into app/data and app/static.

Run it after the explainable_WSI stages 17a, 17c, 21a, 21c and 17d, then resolve the IDC links:
    python -m app.update_data <titan_20.0x folder>
    python -m app.idc_links app/data/5_training_communities_pancancer_slides/cryptic_sarcoma_slides.tsv
    python -m app.idc_links app/data/5_training_communities_pancancer_slides/explorer_slides.tsv

Everything comes from the run "5_training_communities_pancancer_slides", the score-building communities labelling
every pancancer slide, restricted to the cryptic sarcomas: the cryptic sarcoma pages and the community explorer
(webapp_data=cryptic_explorer_cohort_communities). Only the selected communities (stage 13a) are kept. Images are
shrunk to JPEG at about the size they are shown, which keeps the deployed app small (full-size PNGs made it too
large to deploy); only the images the pages show are copied.
"""

import argparse
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from PIL import Image

APP = Path(__file__).parent
RUN = "5_training_communities_pancancer_slides"
TILE_SIDE = 320  # tiles are shown 160 px wide in the explorer, a column wide on the sample page
HEATMAP_SIDE = 1024  # slide heatmaps are shown up to a page column wide


def to_jpeg(source, target, side):
    """`source` image as a JPEG of at most `side` pixels a side, on white where it was transparent."""
    with Image.open(source) as image:
        image.thumbnail((side, side))
        if image.mode in ("RGBA", "LA", "P"):
            image = image.convert("RGBA")
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        target.parent.mkdir(parents=True, exist_ok=True)
        image.convert("RGB").save(target, "JPEG", quality=85, optimize=True)


def jpg(name):
    return str(Path(name).with_suffix(".jpg"))


def copy_images(names, source_dir, target_dir, side):
    """Shrink every image of `names` from `source_dir` into `target_dir`, as .jpg."""
    # parallel: the images are read over the network, one at a time it takes hours
    with ThreadPoolExecutor(max_workers=16) as pool:
        list(pool.map(lambda name: to_jpeg(Path(source_dir) / name, Path(target_dir) / jpg(name), side),
                      sorted(set(names))))


def selected_communities(clipsum):
    """The score-building communities of interest (stage 13a), the only ones the pages show:
    neither the unassigned tiles (-1) nor the communities the selection left out."""
    selection = pd.read_csv(clipsum / RUN / "community_selection" / "community_selection.tsv", sep="\t")
    return set(selection.community[selection.selected])


def write(df, name, data):
    df.to_csv(data / name, sep="\t", index=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("titan", type=Path, help="the pipeline's titan_20.0x folder")
    parser.add_argument("--clipsum", type=Path, help="default: <titan>/explanations/integrated_gradients/clipsum")
    parser.add_argument("--webapp", type=Path, help="the webapp_data tables and tiles, default: <run heatmaps>/webapp")
    parser.add_argument("--types", type=Path,
                        help="the community-type heatmaps (17c), default: <run heatmaps>/community_types")
    parser.add_argument("--explorer", type=Path,
                        help="the one-community explorer heatmaps (17d), default: <run heatmaps>/explorer")
    args = parser.parse_args()
    clipsum = args.clipsum or args.titan / "explanations" / "integrated_gradients" / "clipsum"
    heatmaps = clipsum / RUN / "heatmaps_integrated_gradients"
    webapp, types = args.webapp or heatmaps / "webapp", args.types or heatmaps / "community_types"
    explorer = args.explorer or heatmaps / "explorer"
    keep = selected_communities(clipsum)
    print(f"communities shown: {sorted(keep)}")

    data, static = APP / "data" / RUN, APP / "static" / RUN
    for folder in (data, static):  # no image of an earlier generation is left behind
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)

    # cryptic sarcoma pages
    tiles = pd.read_csv(webapp / "cryptic_sarcomas_tiles.tsv", sep="\t")
    tiles = tiles[tiles.community.isin(keep)]
    copy_images(tiles.tile, webapp / "cryptic_tiles", static / "cryptic_tiles", TILE_SIDE)
    write(tiles.assign(tile=tiles.tile.map(jpg)), "cryptic_sarcomas_tiles.tsv", data)
    slides = pd.read_csv(webapp / "cryptic_sarcoma_slides.tsv", sep="\t")
    copy_images(slides.heatmap.dropna(), heatmaps / "thumbnails", static / "thumbnails", HEATMAP_SIDE)
    slides["heatmap"] = slides.heatmap.map(jpg, na_action="ignore")
    # the same slides coloured by community type, when 17c has run
    type_heatmaps = [h for h in slides.heatmap.dropna().map(lambda h: str(Path(h).with_suffix(".png")))
                     if (types / "thumbnails" / h).exists()]
    copy_images(type_heatmaps, types / "thumbnails", static / "type_thumbnails", HEATMAP_SIDE)
    slides["type_heatmap"] = slides.heatmap.where(slides.heatmap.isin([jpg(h) for h in type_heatmaps]))
    write(slides, "cryptic_sarcoma_slides.tsv", data)
    shutil.copy(webapp / "cryptic_sarcomas_leiden_embeddings.tsv", data)
    shutil.copy(args.titan / "cryptic_sarcomas.tsv", data)
    if (types / "community_types.tsv").exists():
        community_types = pd.read_csv(types / "community_types.tsv", sep="\t")
        write(community_types[community_types.community.isin(keep)], "community_types.tsv", data)

    # community explorer: cryptic slide heatmaps of each community alone and random top tiles
    explorer_slides = pd.read_csv(webapp / "explorer_slides.tsv", sep="\t")
    explorer_slides = explorer_slides[explorer_slides.community.isin(keep)]
    copy_images(explorer_slides.heatmap, explorer / "thumbnails", static / "explorer_thumbnails", HEATMAP_SIDE)
    write(explorer_slides.assign(heatmap=explorer_slides.heatmap.map(jpg)), "explorer_slides.tsv", data)
    explorer_tiles = pd.read_csv(webapp / "explorer_tiles.tsv", sep="\t")
    explorer_tiles = explorer_tiles[explorer_tiles.community.isin(keep)]
    copy_images(explorer_tiles.image, webapp / "explorer_tiles", static / "explorer_tiles", TILE_SIDE)
    write(explorer_tiles.assign(image=explorer_tiles.image.map(jpg)), "explorer_tiles.tsv", data)

    files = list(static.rglob("*.jpg"))
    print(f"{len(files)} images, {sum(f.stat().st_size for f in files) / 2 ** 20:.0f} MB; "
          f"{len(type_heatmaps)} of {slides.heatmap.notna().sum()} type heatmaps")


if __name__ == "__main__":
    main()
