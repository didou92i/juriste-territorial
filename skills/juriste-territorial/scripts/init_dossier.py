"""Create private case handoff files without replacing existing context or instructions."""

import argparse
import json
from datetime import date
from pathlib import Path


def initialize(directory: Path, title: str, updated: date) -> dict:
    if not title.strip() or any(c in title for c in "\r\n"):
        raise ValueError("Le titre doit tenir sur une ligne non vide")
    directory = directory.expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    templates = Path(__file__).resolve().parents[1] / "templates"
    files = {
        "CONTEXTE_DOSSIER.md": "contexte-dossier.md",
        "AGENTS.md": "agents-dossier.md",
    }
    states = {}
    for name, template in files.items():
        content = (templates / template).read_text(encoding="utf-8")
        content = content.replace("{{titre}}", title.strip()).replace(
            "{{date}}", updated.isoformat()
        )
        try:
            with (directory / name).open("x", encoding="utf-8") as stream:
                stream.write(content)
        except FileExistsError:
            states[name] = "existing_unchanged"
        else:
            states[name] = "created"
    return {
        "directory": str(directory),
        "files": states,
        "existing_agents_requires_review": states["AGENTS.md"] == "existing_unchanged",
        "scope": "Structure locale ; les faits et les sources restent à renseigner",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dossier", type=Path, required=True)
    parser.add_argument("--titre", required=True)
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    try:
        answer = initialize(args.dossier, args.titre, args.date)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Initialisation impossible : {exc}\n")
    print(json.dumps(answer, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
