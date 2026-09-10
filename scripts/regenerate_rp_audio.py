#!/usr/bin/env python3
"""Regenerate validation-targeted ADT narration in British RP.

The script deliberately leaves videos.json and all video assets untouched.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXTS_PATH = ROOT / "content/i18n/en/texts.json"
AUDIOS_PATH = ROOT / "content/i18n/en/audios.json"
AUDIO_DIR = ROOT / "content/i18n/en/audio"

EXPLICIT_IDS = {
    "pg014_im017", "pg014_im003", "pg014_im007", "pg023_im005", "pg027_im017",
    "pg028_im024", "pg028_im025", "pg031_im007", "pg031_im001", "pg031_im008",
    "pg031_im003", "pg031_im006", "pg031_im004", "pg031_im009", "pg031_im010",
    "pg033_im001", "pg033_im002", "pg033_im003", "pg033_im004", "pg033_im005",
    "pg034_n0043", "pg035_im008", "pg035_n0070", "pg037_im004", "pg039_im004",
    "pg040_n0018", "pg040_n0023", "pg040_im009", "pg042_im004", "pg042_im003",
    "pg043_im002", "pg043_im005", "pg043_n0044", "pg044_im001", "pg044_im002",
    "pg044_im003", "pg045_im001", "pg045_im002", "pg045_im004_crop_v1", "pg046_im003",
    "pg051_n0008", "pg054_im001", "pg056_n0037", "pg056_n0044", "pg056_n0052",
    "pg057_n0076", "pg057_n0083", "pg057_n0090", "pg058_n0049", "pg060_n0026",
    "pg060_n0033", "pg060_n0040", "pg060_n0071", "pg061_n0025", "pg061_n0055",
    "pg064_n0025", "pg068_im012", "pg068_im013", "pg084_im001_crop1",
    "pg049_n0107", "pg049_n0108", "pg052_n0017", "pg055_n0011", "pg056_n0056",
    "pg057_n0108", "pg060_n0075", "pg061_n0060", "pg063_n0056", "pg064_n0061", "pg066_n0005",
}

FULL_DIALOGUE_PAGES = {"005", "021", "022", "023", "075", "076", "077", "079", "080", "081", "083", "084", "085", "086", "087", "088"}
PHONICS_PAGES = set(f"{n:03d}" for n in range(26, 49))
RELATIONSHIP_PAGES = {"055", "056", "057", "058", "059", "060", "061", "062", "063", "064", "065", "066"}

SONG_RANGES = {
    "049": (111, 113),
    "052": (21, 24),
    "053": (132, 133),
    "055": (14, 16),
    "056": (59, 66),
    "057": (111, 117),
    "060": (78, 84),
    "061": (63, 68),
    "063": (59, 63),
    "064": (64, 70),
    "066": (8, 13),
}

BASE = (
    "Speak in clear, careful British Received Pronunciation suitable for Standard One learners. "
    "Read every word exactly once. Do not omit, repeat, paraphrase, or add words. Use a warm, measured teaching pace."
)


def parts(text_id: str) -> tuple[str, int | None]:
    m = re.match(r"pg(\d{3})_n(\d{4})$", text_id)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r"pg(\d{3})_", text_id)
    return (m.group(1), None) if m else ("", None)


def is_song_id(text_id: str) -> bool:
    page, number = parts(text_id)
    return page in SONG_RANGES and number is not None and SONG_RANGES[page][0] <= number <= SONG_RANGES[page][1]


def choose_targets(texts: dict[str, str]) -> set[str]:
    targets = set(EXPLICIT_IDS)
    keywords = ("letter sound", "letter sounds", "pronounce", "fingerspell", "combine", "relate letter", "sweets containing")
    for text_id, value in texts.items():
        if text_id.endswith("_easy_read") or not value.strip() or not text_id.startswith("pg"):
            continue
        page, _ = parts(text_id)
        lower = value.lower()
        if page in FULL_DIALOGUE_PAGES:
            targets.add(text_id)
        if page in PHONICS_PAGES and (
            "_im" in text_id or re.fullmatch(r"\([a-z]\)", value.strip()) or re.fullmatch(r"[a-z]", value.strip())
            or value.startswith("/") or any(k in lower for k in keywords) or "[[blank:" in value
            or value in {"Letter", "Sound", "Letter sound", "Letter sounds", "Pictures", "Words", "How to pronounce", "How to read"}
        ):
            targets.add(text_id)
        if page in RELATIONSHIP_PAGES and (
            re.fullmatch(r"[a-z]", value.strip()) or value.startswith("/") or any(k in lower for k in keywords)
            or "[[blank:" in value or value in {"Letter", "Sound", "Words", "How to read"}
        ):
            targets.add(text_id)
        if is_song_id(text_id):
            targets.add(text_id)
        if page in {"068", "073"} and "_im" in text_id:
            targets.add(text_id)
    return {text_id for text_id in targets if text_id in texts and texts[text_id].strip()}


def build_pronunciation_words(texts: dict[str, str]) -> dict[str, str]:
    """Pair 'How to read/pronounce' IPA cells with their word cells."""
    result: dict[str, str] = {}
    for page in ROOT.glob("pg*.html"):
        source = page.read_text()
        for row in re.findall(r"<tr\b[^>]*>.*?</tr>", source, re.DOTALL):
            ids = re.findall(r'data-id="([^"]+)"', row)
            values = [(text_id, html.unescape(texts.get(text_id, "")).strip()) for text_id in ids]
            ipas = [(text_id, value) for text_id, value in values if value.startswith("/") and value.endswith("/")]
            words = [
                (text_id, value) for text_id, value in values
                if re.fullmatch(r"[A-Za-z]+", value)
                and value.lower() not in {"letter", "sound", "words", "pronounce", "read"}
                and len(value) > 1
            ]
            if words and len(ipas) >= len(words):
                for (ipa_id, _), (_, word) in zip(ipas[-len(words):], words):
                    result[ipa_id] = word
    return result


def speech_request(text_id: str, value: str, texts: dict[str, str], pronunciation_words: dict[str, str]) -> tuple[str, str]:
    page, _ = parts(text_id)
    value = re.sub(r"\[\[blank:[^\]]+\]\]", "dash", value)
    value = value.replace("—", " dash ") if "[[blank:" in texts[text_id] else value
    instructions = BASE

    if re.fullmatch(r"\([a-z]\)", value.strip()):
        value = value.strip()[1]
        instructions += " Say only the letter name; do not say the word 'letter' or repeat it."
    elif re.fullmatch(r"[a-z]", value.strip()):
        if page in PHONICS_PAGES:
            instructions += " Say only this letter's common British English phoneme, not its alphabet name."
        else:
            instructions += " Say only the alphabet letter name."
    elif value.startswith("/") and value.endswith("/"):
        if text_id in pronunciation_words:
            value = pronunciation_words[text_id]
            instructions += " Pronounce only this English word naturally; do not read slash marks or phonetic symbols aloud."
        else:
            instructions += " Produce only the British English speech sound represented between the slash marks; do not say the slash marks or symbol names."
    elif "letter sound" in value.lower() or "letter sounds" in value.lower():
        instructions += (
            " Whenever a letter follows the words 'letter sound' or 'letter sounds', pronounce its common British English phoneme. "
            "Whenever a letter follows 'letter' or 'letters' in the fingerspelling alternative, say its alphabet name."
        )
    elif re.search(r"(?:^|\s)[a-z](?:\s|[-—])", value) and ("form words" not in value.lower()):
        instructions += " Pronounce separated lowercase letters as their common British English phonemes, then pronounce the completed word normally. Say a visible blank as 'dash'."

    if is_song_id(text_id) and "Sing or sign" not in value:
        instructions += " Sing or rhythmically chant this line with a simple, steady children's melody. Pronounce slash-marked letters as phonemes and do not say the slash or hyphen marks."
        value = re.sub(r"/([a-zæɒʌɪʊəʃʒθðŋ]+)/", r"\1", value)
        value = value.replace("-", " ").replace("x2", "twice")
    return value, instructions


def generate_one(job: tuple[str, str, str], api_key: str) -> tuple[str, str]:
    filename, text, instructions = job
    output = AUDIO_DIR / filename
    if output.exists() and output.stat().st_size > 1000:
        return filename, "cached"
    payload = json.dumps({
        "model": "gpt-4o-mini-tts",
        "voice": "cedar",
        "input": text,
        "instructions": instructions,
        "response_format": "mp3",
    }).encode()
    request = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                data = response.read()
            if len(data) < 1000:
                raise RuntimeError(f"short audio response ({len(data)} bytes)")
            output.write_bytes(data)
            return filename, "generated"
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, RuntimeError):
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not configured")
    texts = json.loads(TEXTS_PATH.read_text())
    audios = json.loads(AUDIOS_PATH.read_text())
    pronunciation_words = build_pronunciation_words(texts)
    targets = choose_targets(texts)
    requests: dict[tuple[str, str], list[str]] = {}
    for text_id in sorted(targets):
        speech = speech_request(text_id, texts[text_id], texts, pronunciation_words)
        requests.setdefault(speech, []).append(text_id)

    jobs = []
    mapping = {}
    for (text, instructions), text_ids in requests.items():
        digest = hashlib.sha256((text + "\0" + instructions).encode()).hexdigest()[:10]
        filename = f"{text_ids[0]}_rp_sep10_{digest}.mp3"
        jobs.append((filename, text, instructions))
        for text_id in text_ids:
            mapping[text_id] = filename
            easy_id = text_id + "_easy_read"
            if easy_id in texts and texts[easy_id] == texts[text_id]:
                mapping[easy_id] = filename

    print(f"Regenerating {len(targets)} text IDs as {len(jobs)} unique British-RP clips")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(generate_one, job, api_key) for job in jobs]
        done = 0
        failures = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                failures += 1
                print(f"  warning: one clip failed after retries: {exc}", flush=True)
            done += 1
            if done % 25 == 0 or done == len(futures):
                print(f"  {done}/{len(futures)} clips ready", flush=True)

    missing = [filename for filename, _, _ in jobs if not (AUDIO_DIR / filename).exists()]
    if missing:
        raise SystemExit(f"{len(missing)} clips remain missing; rerun the script to retry them")

    audios.update(mapping)
    AUDIOS_PATH.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n")
    referenced = set(audios.values())
    for generated in AUDIO_DIR.glob("*_rp_sep10_*.mp3"):
        if generated.name not in referenced:
            generated.unlink()


if __name__ == "__main__":
    main()
