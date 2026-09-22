"""Prepare a mode-blinded packet; keep the key outside the published repository."""

import argparse
import json
import os
from pathlib import Path

from droit_territorial.evaluation import Run, prepare_review_packet, verify_corpus_manifest


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _private_file(path: Path, content: str):
    if "private" not in path.resolve().parts:
        raise ValueError("Review packets and keys must be stored under a private directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(content)


def main():
    parser = argparse.ArgumentParser()
    for name in ("cases", "runs", "out", "map"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.out.resolve() == args.map.resolve() or args.out.exists() or args.map.exists():
        parser.error("Use two distinct new private output paths")
    cases = lines(args.cases)
    if args.manifest:
        verify_corpus_manifest(
            cases, args.cases.read_bytes(), json.loads(args.manifest.read_text())
        )
    runs = [Run.model_validate(row) for row in lines(args.runs)]
    if not runs:
        parser.error("Run file is empty; no review packet was created")
    packet, key = prepare_review_packet(cases, runs)
    _private_file(args.out, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in packet))
    _private_file(args.map, json.dumps(key, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": "prepared",
                "responses": len(packet),
                "packet": str(args.out),
                "operator_map": str(args.map),
            }
        )
    )


if __name__ == "__main__":
    main()
