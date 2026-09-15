"""Check skill references and MCP declarations against the actual exposed tool set."""

import asyncio
import re
from pathlib import Path

from droit_territorial.server import TOOL_NAMES, build_server
from droit_territorial.service import Service

ROOT = Path(__file__).resolve().parents[1]


async def main():
    missing = []
    for file in (ROOT / "skills").rglob("*.md"):
        text = file.read_text()
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" not in target and not target.startswith("#"):
                if not (file.parent / target.split("#")[0]).is_file():
                    missing.append(f"{file.relative_to(ROOT)} -> {target}")
    if missing:
        raise SystemExit("Missing skill references: " + ", ".join(missing))
    service = Service()
    try:
        tools = {t.name for t in await build_server(service).list_tools()}
        if tools != TOOL_NAMES:
            raise SystemExit("MCP contract differs from the published tool set")
        contract = (ROOT / "skills/juriste-territorial/references/outils.md").read_text()
        documented = set(re.findall(r"^\| `([a-z_]+)`", contract, re.M))
        if documented != tools:
            raise SystemExit("Skill contract contains missing or fictional tools")
    finally:
        await service.close()
    print(f"Skill links and all {len(TOOL_NAMES)} MCP tool declarations verified")


if __name__ == "__main__":
    asyncio.run(main())
