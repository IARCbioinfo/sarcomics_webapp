"""Fill the `viewer_url` column of a slides tsv with IDC slim viewer links.

Run it once after regenerating one:  python -m app.idc_links [app/data/slides.tsv]

A QIDO round trip is about a second per slide, far too slow to do while a community is
being displayed, so the links are resolved here and read straight out of the tsv by the
webapp. Slides that cannot be resolved get an empty cell and are not clickable.
"""

import sys
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import requests

SLIDES = "app/data/slides_cryptic_sarcoma.tsv"
DICOMWEB = ("https://proxy.imaging.datacommons.cancer.gov/current"
            "/viewer-only-no-downloads-see-tinyurl-dot-com-slash-3j3d9jyp/dicomWeb")
SLIM = "https://viewer.imaging.datacommons.cancer.gov/slim/studies"


def barcode(image):
    """TCGA-N5-A4RM-01Z-00-DX1.8FB1D437..._community_1.png -> TCGA-N5-A4RM-01Z-00-DX1"""
    return image.split("_community")[0].split(".")[0]


def _first(item, tag):
    value = item.get(tag, {}).get("Value")
    return value[0] if value else None


def idc_viewer_url(slide_barcode):
    """IDC slim viewer URL for one slide barcode, e.g. TCGA-DX-A3U7-01Z-00-DX1.

    The slim viewer shows the one slide, unlike the GDC viewer which lists the whole case.
    The patient is the DICOM study; the slide is the SM series whose description ends in
    the same DX number as the barcode.
    """
    patient, slide = slide_barcode[:12], slide_barcode.split("-")[-1]
    try:
        studies = requests.get(f"{DICOMWEB}/studies", params={"PatientID": patient}, timeout=30)
        for study in studies.json():
            study_uid = _first(study, "0020000D")
            series = requests.get(f"{DICOMWEB}/studies/{study_uid}/series", timeout=40).json()
            for item in series:
                description = _first(item, "0008103E") or ""
                if _first(item, "00080060") == "SM" and description.split()[-1].upper() == slide:
                    return f"{SLIM}/{study_uid}/series/{_first(item, '0020000E')}"
    except Exception as error:  # noqa: BLE001 - one dead lookup must not lose the other 112
        print(f"{slide_barcode}: lookup failed ({error})", file=sys.stderr)
    return None


def main(path=SLIDES):
    slides = pd.read_csv(path, sep="\t")
    barcodes = sorted({barcode(image) for image in slides.image})
    with ThreadPoolExecutor(max_workers=8) as pool:
        urls = dict(zip(barcodes, pool.map(idc_viewer_url, barcodes)))
    slides["viewer_url"] = [urls[barcode(image)] for image in slides.image]
    slides.to_csv(path, sep="\t", index=False)
    resolved = sum(url is not None for url in urls.values())
    print(f"{resolved}/{len(barcodes)} slides resolved, written to {path}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
