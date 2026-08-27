"""Download the Phase 0 development splits from their public project sources."""

from __future__ import annotations

import json
import logging
import shutil
import urllib.error
import urllib.request
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

LOGGER = logging.getLogger(__name__)

HOTPOTQA_DEV_URL = (
    "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
)
HOTPOTQA_HF_PREVIEW_URL = (
    "https://datasets-server.huggingface.co/first-rows?"
    "dataset=hotpotqa%2Fhotpot_qa&config=distractor&split=validation"
)
TWOWIKI_ARCHIVE_URL = (
    "https://www.dropbox.com/scl/fi/32t7pv1dyf3o2pp0dl25u/"
    "data_ids_april7.zip?rlkey=u868q6h0jojw4djjg7ea65j46&dl=1"
)
TWOWIKI_HF_PREVIEW_URL = (
    "https://datasets-server.huggingface.co/first-rows?"
    "dataset=framolfese%2F2WikiMultihopQA&config=default&split=validation"
)


def _download(url: str, destination: Path, *, timeout_seconds: int = 120) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ReliableRAG-Phase0/1.0 (dataset verification)"},
    )
    LOGGER.info("Downloading %s", url)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            with temporary_path.open("wb") as output_file:
                shutil.copyfileobj(response, output_file)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    LOGGER.info("Saved %s", destination)


def _hf_viewer_row_to_authors_json(row: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a public viewer row to the datasets' original JSON layout."""

    converted = dict(row)
    if "_id" not in converted and "id" in converted:
        converted["_id"] = converted.pop("id")

    context = converted.get("context")
    if isinstance(context, Mapping):
        titles = context.get("title")
        sentence_lists = context.get("sentences")
        if (
            not isinstance(titles, Sequence)
            or isinstance(titles, (str, bytes))
            or not isinstance(sentence_lists, Sequence)
            or isinstance(sentence_lists, (str, bytes))
            or len(titles) != len(sentence_lists)
        ):
            raise ValueError("Malformed context in public dataset viewer row")
        converted["context"] = [
            [title, sentences]
            for title, sentences in zip(titles, sentence_lists, strict=True)
        ]

    supporting_facts = converted.get("supporting_facts")
    if isinstance(supporting_facts, Mapping):
        titles = supporting_facts.get("title")
        sentence_ids = supporting_facts.get("sent_id")
        if (
            not isinstance(titles, Sequence)
            or isinstance(titles, (str, bytes))
            or not isinstance(sentence_ids, Sequence)
            or isinstance(sentence_ids, (str, bytes))
            or len(titles) != len(sentence_ids)
        ):
            raise ValueError(
                "Malformed supporting facts in public dataset viewer row"
            )
        converted["supporting_facts"] = [
            [title, sentence_id]
            for title, sentence_id in zip(titles, sentence_ids, strict=True)
        ]
    return converted


def _download_hf_preview(url: str, destination: Path, dataset_name: str) -> None:
    """Materialize a public validation preview when the primary host is down."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ReliableRAG-Phase0/1.0 (dataset verification)"},
    )
    LOGGER.info(
        "Downloading public %s validation preview from Hugging Face", dataset_name
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.load(response)
        rows = payload.get("rows") if isinstance(payload, Mapping) else None
        if not isinstance(rows, list) or len(rows) < 10:
            raise ValueError(
                f"Public {dataset_name} preview contains fewer than 10 rows"
            )
        records = []
        for item in rows:
            if not isinstance(item, Mapping) or not isinstance(item.get("row"), Mapping):
                raise ValueError(f"Malformed row in public {dataset_name} preview")
            records.append(_hf_viewer_row_to_authors_json(item["row"]))
        with temporary_path.open("w", encoding="utf-8") as output_file:
            json.dump(records, output_file, ensure_ascii=False)
        temporary_path.replace(destination)
    except Exception:
        temporary_path.unlink(missing_ok=True)
        raise
    LOGGER.info("Saved %s", destination)


def ensure_hotpotqa_dev(data_dir: str | Path) -> Path:
    """Return the official HotpotQA distractor dev JSON, downloading if absent."""

    dataset_dir = Path(data_dir) / "hotpotqa"
    destination = dataset_dir / "hotpot_dev_distractor_v1.json"
    preview_destination = dataset_dir / "hotpot_dev_distractor_hf_preview.json"
    if destination.exists():
        return destination
    if preview_destination.exists():
        return preview_destination
    try:
        _download(HOTPOTQA_DEV_URL, destination, timeout_seconds=30)
        return destination
    except (OSError, urllib.error.URLError) as error:
        LOGGER.warning(
            "Official HotpotQA host unavailable (%s); using the public "
            "Hugging Face validation preview for the Phase 0 smoke test",
            error,
        )
        _download_hf_preview(
            HOTPOTQA_HF_PREVIEW_URL,
            preview_destination,
            "HotpotQA",
        )
        return preview_destination


def _select_2wiki_dev_member(archive: zipfile.ZipFile) -> str:
    candidates = [
        name
        for name in archive.namelist()
        if not name.startswith("__MACOSX/")
        and PurePosixPath(name).name.casefold() == "dev.json"
    ]
    if not candidates:
        raise FileNotFoundError("The 2WikiMultiHopQA archive contains no dev.json")
    candidates.sort(key=lambda name: ("data_ids" not in name.casefold(), len(name)))
    return candidates[0]


def ensure_2wiki_dev(data_dir: str | Path) -> Path:
    """Return the corrected official 2Wiki dev JSON, downloading if absent."""

    dataset_dir = Path(data_dir) / "2wikimultihopqa"
    destination = dataset_dir / "dev.json"
    preview_destination = dataset_dir / "dev_hf_preview.json"
    if destination.exists():
        return destination
    if preview_destination.exists():
        return preview_destination

    archive_path = dataset_dir / "data_ids_april7.zip"
    if not archive_path.exists():
        try:
            _download(TWOWIKI_ARCHIVE_URL, archive_path, timeout_seconds=30)
        except (OSError, urllib.error.URLError) as error:
            LOGGER.warning(
                "Official 2WikiMultiHopQA archive unavailable (%s); using a "
                "public validation preview for the Phase 0 smoke test",
                error,
            )
            _download_hf_preview(
                TWOWIKI_HF_PREVIEW_URL,
                preview_destination,
                "2WikiMultiHopQA",
            )
            return preview_destination

    LOGGER.info("Extracting 2WikiMultiHopQA dev split from %s", archive_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        member = _select_2wiki_dev_member(archive)
        with archive.open(member) as source_file, destination.open("wb") as output_file:
            shutil.copyfileobj(source_file, output_file)
    return destination
