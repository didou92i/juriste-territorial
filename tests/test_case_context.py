import importlib.util
from datetime import date

import pytest

from droit_territorial.resources import data_path


@pytest.fixture
def initializer():
    path = data_path("skill") / "scripts/init_dossier.py"
    spec = importlib.util.spec_from_file_location("init_dossier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.initialize


def test_initialize_private_case_and_preserve_later_work(initializer, tmp_path):
    case = tmp_path / "dossier prive"
    result = initializer(case, "Dossier fictif", date(2026, 11, 17))
    assert result["files"] == {"CONTEXTE_DOSSIER.md": "created", "AGENTS.md": "created"}
    content = (case / "CONTEXTE_DOSSIER.md").read_text()
    assert "Dossier fictif" in content and "2026-11-17" in content and "{{" not in content
    original = "# Historique validé\nDécision reçue ; date à documenter.\n"
    (case / "CONTEXTE_DOSSIER.md").write_text(original)
    instructions = "Consignes locales indépendantes à conserver.\n"
    (case / "AGENTS.md").write_text(instructions)
    result = initializer(case, "Nouveau titre", date(2026, 11, 18))
    assert set(result["files"].values()) == {"existing_unchanged"}
    assert (case / "CONTEXTE_DOSSIER.md").read_text() == original
    assert (case / "AGENTS.md").read_text() == instructions
    assert result["existing_agents_requires_review"] is True


def test_initialize_adds_only_missing_file_and_does_not_follow_existing_link(initializer, tmp_path):
    case = tmp_path / "case"
    case.mkdir()
    existing = tmp_path / "existing_context.md"
    existing.write_text("Historique conservé\n")
    (case / "CONTEXTE_DOSSIER.md").symlink_to(existing)
    result = initializer(case, "Exemple", date(2026, 11, 17))
    assert result["files"] == {
        "CONTEXTE_DOSSIER.md": "existing_unchanged",
        "AGENTS.md": "created",
    }
    assert existing.read_text() == "Historique conservé\n"
    assert (case / "CONTEXTE_DOSSIER.md").is_symlink()


def test_invalid_title_does_not_create_case(initializer, tmp_path):
    target = tmp_path / "not_created"
    with pytest.raises(ValueError):
        initializer(target, "titre\ninstruction étrangère", date(2026, 11, 17))
    assert not target.exists()
