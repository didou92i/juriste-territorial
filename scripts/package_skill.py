"""Build the standalone skill from the single canonical directory."""

import hashlib
import tomllib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills" / "juriste-territorial"


def main():
    version = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
    output = ROOT / "dist" / f"juriste-territorial-{version}.zip"
    output.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(SOURCE.rglob("*")):
            if file.is_file():
                info = zipfile.ZipInfo(
                    str(Path("juriste-territorial") / file.relative_to(SOURCE)),
                    (2026, 9, 25, 0, 0, 0),
                )
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, file.read_bytes())
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix(".zip.sha256").write_text(f"{digest}  {output.name}\n")
    print(f"{output.name}: {digest}")


if __name__ == "__main__":
    main()
