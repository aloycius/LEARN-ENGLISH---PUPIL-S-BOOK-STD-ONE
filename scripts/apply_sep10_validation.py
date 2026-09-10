#!/usr/bin/env python3
"""Apply the September validation document corrections to the ADT bundle."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXTS_PATH = ROOT / "content/i18n/en/texts.json"


UPDATES = {
    "pg014_im017": "A picture of a jackfruit.",
    "pg014_im003": "A picture of a lemon.",
    "pg014_im007": "A picture of spinach.",
    "pg023_im005": "A picture of a girl carrying containers with her hands.",
    "pg027_im017": "A picture of a pin.",
    "pg028_im024": "A picture of a cup.",
    "pg028_im025": "A picture of a crocodile.",
    "pg031_im007": "A picture of a glove.",
    "pg031_im001": "A picture of grass.",
    "pg031_im008": "A picture of a guitar.",
    "pg031_im003": "A picture of grapes.",
    "pg031_im006": "A picture of a grasshopper.",
    "pg031_im004": "A picture of a girl.",
    "pg031_im009": "A picture of guava.",
    "pg031_im010": "A picture of a gumboot.",
    "pg033_im001": "A picture of jeans.",
    "pg033_im002": "A picture of a jug.",
    "pg033_im003": "A picture of a jacket.",
    "pg033_im004": "A picture of jam.",
    "pg033_im005": "A picture of a jar.",
    "pg034_n0043": "/feɪk/",
    "pg035_im008": "A picture of a lamp.",
    "pg035_n0070": "/laɪf/",
    "pg037_im004": "A picture of a needle.",
    "pg039_im004": "A picture of a question mark.",
    "pg040_n0018": "/raɪd/",
    "pg040_n0023": "/raɪp/",
    "pg040_im009": "A picture of a slipper.",
    "pg042_im004": "A picture of a vest.",
    "pg042_im003": "A picture of a vase.",
    "pg043_im002": "A picture of a wagon.",
    "pg043_im005": "A picture of wood.",
    "pg043_n0044": "/veɪn/",
    "pg044_im001": "A picture of oxen.",
    "pg044_im002": "A picture of a box.",
    "pg044_im003": "A picture of a fox.",
    "pg045_im001": "A picture of a yoke.",
    "pg045_im002": "A picture of a yacht.",
    "pg045_im004_crop_v1": "A picture of a yolk.",
    "pg046_im003": "A picture of zero.",
    "pg051_n0008": "dot",
    "pg054_im001": "A picture of a pin.",
    "pg056_n0037": "/eɪdʒ/",
    "pg056_n0044": "/neɪm/",
    "pg056_n0052": "/fɑːr/",
    "pg057_n0076": "/dɒɡ/",
    "pg057_n0083": "/dɪɡ/",
    "pg057_n0090": "/dɒt/",
    "pg058_n0049": "1. Relate letter f to its sound. Then, read the words aloud. Or fingerspell letter f,",
    "pg060_n0026": "/kɪt/",
    "pg060_n0033": "/kɪn/",
    "pg060_n0040": "/kaɪt/",
    "pg060_n0071": "/lɪd/",
    "pg061_n0025": "/mɒp/",
    "pg061_n0055": "/nɒt/",
    "pg064_n0025": "/tɒp/",
    "pg068_im012": "Number 9.",
    "pg068_im013": "Number 0.",
    "pg084_im001_crop1": "A picture of two pupils speaking politely in a classroom.",
    "pg001_n0019": "",
    "pg010_n0044": "",
    "pg021_n0023": "",
    "pg024_n0043": "",
}


DUPLICATE_NUMBER_IDS = [
    "pg031_n0076",
    "pg035_n0037",
    "pg035_n0044",
    "pg038_n0042",
    "pg038_n0048",
    "pg042_n0003",
    "pg042_n0010",
    "pg043_n0003",
    "pg043_n0023",
    "pg044_n0003",
    "pg044_n0009",
    "pg044_n0057",
    "pg044_n0063",
    "pg046_n0029",
    "pg046_n0045",
    "pg066_n0016",
]


def replace_data_id_text(source: str, text_id: str, value: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[A-Za-z0-9:-]+)\b[^>]*\bdata-id="{re.escape(text_id)}"[^>]*>)(?P<body>.*?)(</(?P=tag)>)',
        re.DOTALL,
    )
    escaped = html.escape(value, quote=False)
    return pattern.sub(lambda m: m.group(1) + escaped + m.group(4), source)


def replace_img_alt(source: str, text_id: str, value: str) -> str:
    pattern = re.compile(rf'(<img\b(?=[^>]*\bdata-id="{re.escape(text_id)}")[^>]*\balt=")[^"]*(")')
    escaped = html.escape(value, quote=True)
    return pattern.sub(lambda m: m.group(1) + escaped + m.group(2), source)


def main() -> None:
    texts = json.loads(TEXTS_PATH.read_text())

    for text_id in DUPLICATE_NUMBER_IDS:
        old = texts[text_id]
        new = re.sub(r"^\s*\d+\.\s*", "", old)
        UPDATES[text_id] = new

    for text_id, value in list(UPDATES.items()):
        texts[text_id] = value
        easy_id = text_id + "_easy_read"
        if easy_id in texts:
            texts[easy_id] = re.sub(r"^\s*\d+\.\s*", "", value) if text_id in DUPLICATE_NUMBER_IDS else value

    TEXTS_PATH.write_text(json.dumps(texts, ensure_ascii=False, indent=2) + "\n")

    for page in ROOT.glob("pg*.html"):
        source = page.read_text()
        updated = source
        for text_id, value in UPDATES.items():
            if text_id.startswith(page.stem.split("_sec", 1)[0] + "_"):
                updated = replace_data_id_text(updated, text_id, value)
                updated = replace_img_alt(updated, text_id, value)
                easy_id = text_id + "_easy_read"
                updated = replace_data_id_text(updated, easy_id, texts.get(easy_id, value))
        if page.name == "pg039_sec001.html":
            updated = updated.replace(
                '<img src="images/pg039_im004.jpg" alt=""',
                '<img src="images/pg039_im004.jpg" alt="A picture of a question mark." data-id="pg039_im004"',
            )
        if page.name == "pg044_sec002.html":
            updated = updated.replace('src="images/pg044_im003.jpg"', 'src="images/pg054_im012.jpg"')
        if page.name == "pg067_sec001.html":
            updated = re.sub(r'(<img\b[^>]*?)\sdata-id="pg067_[^"]+"', r'\1', updated)
        reading_order = {
            "pg075_sec001.html": [("pg075_im003", "pg075_n0009"), ("pg075_im002", "pg075_n0015")],
            "pg076_sec001.html": [("pg076_im001", "pg076_n0004")],
            "pg077_sec001.html": [("pg077_im002", "pg077_n0008"), ("pg077_im001", "pg077_n0012"), ("pg077_im003", "pg077_n0016"), ("pg077_im004", "pg077_n0019")],
            "pg079_sec001.html": [("pg079_im001", "pg079_n0004"), ("pg079_im002", "pg079_n0009")],
            "pg080_sec001.html": [("pg080_im001", "pg080_n0004"), ("pg080_im002", "pg080_n0009")],
            "pg087_sec001.html": [("pg087_im001", "pg087_n0004")],
        }
        if page.name in reading_order:
            for image_id, first_text_id in reading_order[page.name]:
                updated = re.sub(rf'(<img\b[^>]*?)\sdata-id="{re.escape(image_id)}"', r'\1', updated)
                hidden = f'<span class="sr-only" data-id="{image_id}"></span>'
                if hidden not in updated:
                    updated = re.sub(
                        rf'(<(?:span|div|p)\b[^>]*data-id="{re.escape(first_text_id)}")',
                        hidden + r'\1',
                        updated,
                        count=1,
                    )
        pointer_pages = {"pg075_sec001.html", "pg077_sec001.html", "pg079_sec001.html", "pg080_sec001.html", "pg081_sec001.html", "pg083_sec001.html", "pg085_sec001.html", "pg087_sec001.html", "pg088_sec001.html"}
        if page.name in pointer_pages:
            if ".speech-pointer::after" not in updated:
                updated = updated.replace(
                    '<link href="./assets/fonts.css" rel="stylesheet">',
                    '<link href="./assets/fonts.css" rel="stylesheet">\n'
                    '    <style>\n'
                    '      .speech-pointer { position: relative; }\n'
                    '      .speech-pointer::after { content: ""; position: absolute; left: 24%; bottom: -17px; width: 0; height: 0; border-top: 18px solid #fb923c; border-left: 11px solid transparent; border-right: 11px solid transparent; }\n'
                    '    </style>',
                )
            updated = re.sub(
                r'<(div|p) class="(?![^"]*speech-pointer)(?=[^"]*rounded)(?=[^"]*border)([^"]*)"',
                r'<\1 class="speech-pointer \2"',
                updated,
            )
        if page.name == "pg088_sec002.html":
            if ".speech-tail-left::after" not in updated:
                updated = updated.replace(
                    '<link href="./assets/fonts.css" rel="stylesheet">',
                    '<link href="./assets/fonts.css" rel="stylesheet">\n'
                    '    <style>\n'
                    '      .speech-tail-left::after, .speech-tail-right::after { content: ""; position: absolute; bottom: -18px; width: 0; height: 0; border-top: 20px solid #fb923c; border-left: 12px solid transparent; border-right: 12px solid transparent; }\n'
                    '      .speech-tail-left::after { left: 28%; transform: rotate(18deg); }\n'
                    '      .speech-tail-right::after { right: 25%; transform: rotate(-18deg); }\n'
                    '    </style>',
                )
            updated = updated.replace(
                '<div class="absolute left-4 top-4 z-10 max-w-[32%]',
                '<div class="speech-tail-left absolute left-4 top-4 z-10 max-w-[32%]',
            )
            updated = updated.replace(
                '<div class="absolute bottom-5 right-4 z-10 max-w-[36%]',
                '<div class="speech-tail-right absolute bottom-5 right-4 z-10 max-w-[36%]',
            )
        if updated != source:
            page.write_text(updated)

    pages_path = ROOT / "content/pages.json"
    pages = json.loads(pages_path.read_text())
    removed_sections = {"pg034_sec003", "pg037_sec002"}
    pages = [entry for entry in pages if entry["section_id"] not in removed_sections]
    pages_path.write_text(json.dumps(pages, ensure_ascii=False, indent=2) + "\n")
    for index, entry in enumerate(pages, start=1):
        page_path = ROOT / entry["href"]
        if not page_path.exists():
            continue
        source = page_path.read_text()
        source = re.sub(
            r'(<meta\s+name="page-section-id"\s+content=")[^"]+("\s*/?>)',
            rf'\g<1>{index}\2',
            source,
            count=1,
        )
        page_path.write_text(source)


if __name__ == "__main__":
    main()
