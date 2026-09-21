#!/usr/bin/env python3
"""Create grounded local learning packs for NotebookLM/Gemini workflows."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

try:
    from scripts.init_study import atomic_write
    from scripts.state_io import atomic_update_json
except ModuleNotFoundError:  # direct execution: ``python scripts/create_learning_pack.py``
    from init_study import atomic_write
    from state_io import atomic_update_json


SUPPORTED_FORMATS = {
    "cards",
    "quiz",
    "mind_map",
    "chart",
    "image",
    "infographic",
    "slides",
    "audio",
    "video",
    "study_guide",
}
VISUAL_FORMATS = {"mind_map", "chart", "image", "infographic", "slides"}
TRANSCRIPT_FORMATS = {"audio", "video"}
MEDIA_STATUSES = {"prepared", "generated", "verified", "failed", "archived"}

FORMAT_INSTRUCTIONS = {
    "cards": "Create concise flashcards with one retrievable claim each and cite source IDs.",
    "quiz": "Create questions that test misconceptions; keep the answer key hidden until an attempt.",
    "mind_map": "Create a concept map showing labeled relationships and cite each branch.",
    "chart": "Create a quantitative chart only from explicit source data; include units and a data table.",
    "image": "Create a didactic image with accurate labels and provide complete alt text.",
    "infographic": "Create an accessible infographic with a clear hierarchy and source citations.",
    "slides": "Create a teaching deck with one claim per slide, speaker notes, citations, and alt text.",
    "audio": "Create an audio overview in Brazilian Portuguese and provide a transcript or notes.",
    "video": "Create an explainer video with source-grounded visuals and provide a transcript.",
    "study_guide": "Create a study guide with retrieval questions and explicit source citations.",
}


def _source_hash(source: dict) -> str:
    content = str(source.get("content", "")).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _validate_sources(sources: list[dict]) -> None:
    if not isinstance(sources, list) or not sources:
        raise ValueError("at least one verified source is required")
    required = {"source_id", "title", "url", "content"}
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"source {index} must be an object")
        missing = sorted(required - source.keys())
        if missing:
            raise ValueError(f"source {index} missing fields: {', '.join(missing)}")
        if not all(isinstance(source[field], str) and source[field].strip() for field in required):
            raise ValueError(f"source {index} contains an empty required field")
        source_id = source["source_id"]
        if source_id in source_ids:
            raise ValueError(f"duplicate source_id: {source_id}")
        source_ids.add(source_id)


def validate_formats(formats: list[str]) -> list[str]:
    if not isinstance(formats, list) or not all(isinstance(value, str) for value in formats):
        raise ValueError("formats must be a list of strings")
    requested = list(dict.fromkeys(formats))
    unknown = sorted(set(requested) - SUPPORTED_FORMATS)
    if unknown:
        raise ValueError("unsupported formats: " + ", ".join(unknown))
    if not requested:
        raise ValueError("at least one output format is required")
    return requested


def build_manifest(
    lesson_id: str,
    sources: list[dict],
    formats: list[str],
    objective: str,
) -> dict:
    _validate_sources(sources)
    requested = validate_formats(formats)
    if not isinstance(lesson_id, str) or not lesson_id.strip() or not isinstance(objective, str) or not objective.strip():
        raise ValueError("lesson_id and objective are required")
    return {
        "schema_version": 2,
        "artifact_id": f"media_{uuid.uuid4()}",
        "lesson_id": lesson_id,
        "objective": objective,
        "source_ids": [source["source_id"] for source in sources],
        "source_hashes": {source["source_id"]: _source_hash(source) for source in sources},
        "requested_formats": requested,
        "external_upload": {
            "provider": "notebooklm",
            "consented": False,
            "consented_at": None,
            "files": ["source-pack.md", "prompts.md"],
        },
        "evidence_eligible": False,
        "status": "prepared",
        "outputs": [],
    }


def _is_timestamp(value: object, *, allow_none: bool = False) -> bool:
    if value is None:
        return allow_none
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            date.fromisoformat(value)
        except ValueError:
            return False
    return True


def validate_media_item(item: dict) -> list[str]:
    if not isinstance(item, dict):
        return ["media artifact must be an object"]
    errors: list[str] = []
    required = {
        "artifact_id", "lesson_id", "type", "provider", "source_ids", "objective",
        "local_path", "url", "status", "verified", "created_at", "verified_at",
        "accessibility", "evidence_eligible",
    }
    errors.extend(f"media artifact missing field: {field}" for field in sorted(required - item.keys()))
    artifact_type = item.get("type")
    artifact_id = item.get("artifact_id")
    if not isinstance(artifact_id, str) or not artifact_id.strip():
        errors.append("artifact_id is required")
    elif not artifact_id.startswith("media_"):
        errors.append("artifact_id must start with media_")
    if item.get("evidence_eligible") is not False:
        errors.append("evidence_eligible must be false")
    if not isinstance(item.get("lesson_id"), str) or not item["lesson_id"].strip():
        errors.append("lesson_id is required")
    for field in ("type", "provider", "objective", "status"):
        if not isinstance(item.get(field), str) or not item[field].strip():
            errors.append(f"{field} is required")
    if not isinstance(item.get("source_ids"), list) or not all(
        isinstance(value, str) and value.strip() for value in item.get("source_ids", [])
    ):
        errors.append("source_ids must be a list of non-empty strings")
    local_path = item.get("local_path")
    url = item.get("url")
    if local_path is not None and not isinstance(local_path, str):
        errors.append("local_path must be a string or null")
    if url is not None and not isinstance(url, str):
        errors.append("url must be a string or null")
    if not (
        isinstance(local_path, str) and local_path.strip()
        or isinstance(url, str) and url.strip()
    ):
        errors.append("local_path or url is required")
    if not isinstance(item.get("status"), str) or item.get("status") not in MEDIA_STATUSES:
        errors.append("status must be a supported media status")
    if not isinstance(item.get("verified"), bool):
        errors.append("verified must be boolean")
    for field in ("created_at", "verified_at"):
        value = item.get(field)
        if field == "verified_at" and value is None:
            continue
        if not _is_timestamp(value, allow_none=field == "verified_at"):
            errors.append(f"{field} is required as an ISO timestamp")
    if item.get("verified") is True and not _is_timestamp(item.get("verified_at")):
        errors.append("verified_at is required when media is verified")
    if not isinstance(item.get("accessibility"), dict):
        errors.append("accessibility must be an object")
    if isinstance(artifact_type, str) and artifact_type in VISUAL_FORMATS and not isinstance(item.get("alt_text"), str):
        errors.append(f"alt_text is required for {artifact_type}")
    elif isinstance(artifact_type, str) and artifact_type in VISUAL_FORMATS and not item["alt_text"].strip():
        errors.append(f"alt_text is required for {artifact_type}")
    if isinstance(artifact_type, str) and artifact_type in TRANSCRIPT_FORMATS and not isinstance(item.get("transcript"), str):
        errors.append(f"transcript is required for {artifact_type}")
    elif isinstance(artifact_type, str) and artifact_type in TRANSCRIPT_FORMATS and not item["transcript"].strip():
        errors.append(f"transcript is required for {artifact_type}")
    return errors


def render_sources(sources: list[dict]) -> str:
    sections = ["# Verified Source Pack", ""]
    for source in sources:
        sections.extend([
            f"## {source['title']}",
            "",
            f"- Source ID: `{source['source_id']}`",
            f"- URL: {source['url']}",
            "",
            source["content"].strip(),
            "",
        ])
    return "\n".join(sections).rstrip() + "\n"


def render_prompts(formats: list[str], sources: list[dict], objective: str) -> str:
    source_ids = ", ".join(source["source_id"] for source in sources)
    lines = [
        "# Grounded Generation Prompts",
        "",
        f"Learning objective: {objective}",
        f"Use only these source IDs: {source_ids}",
        "If a requested claim is absent, state that it is unsupported instead of inventing it.",
        "Generated material is not learning evidence; end with an autonomous retrieval or transfer task.",
        "",
    ]
    for artifact_type in formats:
        lines.extend([
            f"## {artifact_type}",
            "",
            FORMAT_INSTRUCTIONS[artifact_type],
            "",
        ])
    lines.extend([
        "## Provider note",
        "",
        "Generate Studio artifacts in NotebookLM. Use Gemini notebook chat only for synchronized conversation or broader tools; verify any non-source context separately.",
        "",
    ])
    return "\n".join(lines)


def _create_local_fallbacks(pack: Path, lesson_id: str, formats: list[str]) -> None:
    local = pack / "local"
    local.mkdir(parents=True, exist_ok=True)
    if "cards" in formats:
        atomic_write(local / "cards.json", json.dumps({"schema_version": 2, "lesson_id": lesson_id, "cards": []}, indent=2) + "\n")
    if "quiz" in formats:
        atomic_write(local / "quiz.json", json.dumps({"schema_version": 2, "lesson_id": lesson_id, "questions": [], "answer_key": []}, indent=2) + "\n")
    text_fallbacks = {
        "mind_map": ("concept-map.mmd", "mindmap\n  root((Learning objective))\n"),
        "chart": ("chart-data.csv", "label,value,unit,source_id\n"),
        "image": ("image-brief.md", "# Didactic Image Brief\n\nInclude source-grounded labels and alt text.\n"),
        "infographic": ("infographic-brief.md", "# Infographic Brief\n\nInclude hierarchy, citations, and alt text.\n"),
        "slides": ("slides-outline.md", "# Slide Outline\n\nInclude speaker notes, citations, and alt text.\n"),
        "audio": ("audio-script.md", "# Audio Script\n\nInclude a complete transcript.\n"),
        "video": ("video-storyboard.md", "# Video Storyboard\n\nInclude visual descriptions and transcript.\n"),
        "study_guide": ("study-guide.md", "# Study Guide\n\nInclude retrieval questions and citations.\n"),
    }
    for artifact_type, (name, content) in text_fallbacks.items():
        if artifact_type in formats:
            atomic_write(local / name, content)
    if "chart" in formats:
        atomic_write(
            local / "chart-spec.md",
            "# Chart Specification\n\nDefine chart type, axes, units, source IDs, labels, and an accessible text summary.\n",
        )


def _register_pack(study_root: Path, pack: Path, manifest: dict) -> None:
    index_path = study_root / ".ai-tutor" / "media-index.json"
    if not index_path.is_file():
        return
    relative_path = pack.relative_to(study_root).as_posix()

    artifact = {
        "artifact_id": manifest["artifact_id"],
        "lesson_id": manifest["lesson_id"],
        "type": "learning_pack",
        "provider": "local+notebooklm",
        "source_ids": manifest["source_ids"],
        "objective": manifest["objective"],
        "requested_formats": manifest["requested_formats"],
        "local_path": relative_path,
        "url": None,
        "status": "prepared",
        "verified": False,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "verified_at": None,
        "accessibility": {
            "visuals_require_alt_text": True,
            "audio_video_require_transcript": True,
        },
        "evidence_eligible": False,
    }

    def append_artifact(index: dict) -> dict:
        artifacts = index.get("artifacts")
        if not isinstance(artifacts, list):
            raise ValueError("media-index artifacts must be a list")
        if any(item.get("artifact_id") == artifact["artifact_id"] for item in artifacts if isinstance(item, dict)):
            return index
        artifacts.append(artifact)
        return index

    atomic_update_json(index_path, append_artifact)


def create_learning_pack(
    study_root: Path,
    lesson_id: str,
    sources: list[dict],
    formats: list[str],
    *,
    objective: str,
) -> Path:
    manifest = build_manifest(lesson_id, sources, formats, objective)
    pack = study_root.resolve() / "media" / lesson_id / "notebooklm"
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "exports").mkdir(parents=True, exist_ok=True)
    atomic_write(pack / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    atomic_write(pack / "source-pack.md", render_sources(sources))
    atomic_write(pack / "prompts.md", render_prompts(manifest["requested_formats"], sources, objective))
    _create_local_fallbacks(pack, lesson_id, manifest["requested_formats"])
    _register_pack(study_root.resolve(), pack, manifest)
    return pack


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--study-root", required=True, type=Path)
    parser.add_argument("--lesson-id", required=True)
    parser.add_argument("--sources-json", required=True, type=Path)
    parser.add_argument("--formats", required=True, nargs="+")
    parser.add_argument("--objective", required=True)
    args = parser.parse_args()
    sources = json.loads(args.sources_json.read_text(encoding="utf-8"))
    pack = create_learning_pack(
        args.study_root,
        args.lesson_id,
        sources,
        args.formats,
        objective=args.objective,
    )
    print(pack)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
