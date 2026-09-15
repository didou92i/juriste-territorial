from pathlib import Path


def data_path(kind: str) -> Path:
    packaged = Path(__file__).parent / "data" / kind
    if packaged.is_dir():
        return packaged
    root = Path(__file__).resolve().parents[2]
    return root / ("skills/juriste-territorial" if kind == "skill" else "registry")


def methodology(topic: str = "core", output_mode: str = "note") -> dict:
    from .models import SourceError

    topics = {"core": "SKILL.md"}
    skill = data_path("skill")
    for folder in ("references", "modules", "templates"):
        for file in sorted((skill / folder).glob("*.md")):
            topics[file.stem] = f"{folder}/{file.name}"
    if topic not in topics:
        raise SourceError("unknown_topic", "Select a topic from: " + ", ".join(topics))
    if output_mode not in {"short", "note", "audit", "draft", "letter", "litigation", "monitoring"}:
        raise SourceError("invalid_input", "Unknown output mode")
    return {
        "status": "ok",
        "method_version": "0.3.1",
        "maturity": "experimental",
        "topic": topic,
        "available_topics": list(topics),
        "output_mode": output_mode,
        "text": (skill / topics[topic]).read_text(encoding="utf-8"),
        "scope": "Methodology, not current-law verification or proof of model compliance",
    }
