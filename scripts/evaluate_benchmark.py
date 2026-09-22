"""Validate recorded runs and human reviews. Never sends prompts to a paid model implicitly."""

import argparse
import json
from pathlib import Path

from droit_territorial.evaluation import Review, Run, benchmark, verify_corpus_manifest


def lines(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=Path("evals/development-cases.jsonl"))
    parser.add_argument("--runs", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    cases = lines(args.cases)
    if args.manifest:
        verify_corpus_manifest(
            cases,
            args.cases.read_bytes(),
            json.loads(args.manifest.read_text()),
        )
    result = benchmark(
        cases,
        [Run.model_validate(r) for r in lines(args.runs)] if args.runs else [],
        [Review.model_validate(r) for r in lines(args.reviews)] if args.reviews else [],
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
