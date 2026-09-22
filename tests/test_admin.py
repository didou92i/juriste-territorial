import io
import sqlite3
import zipfile

import httpx
import pytest

from droit_territorial.admin import AdminIndex, parse_xml
from droit_territorial.models import SourceError
from droit_territorial.runtime import Settings, Transport
from droit_territorial.service import Service

URL = "https://opendata.justice-administrative.fr/DCE/2021/09/CE_202109.zip"


def xml(
    identifier="DCE_123_20210927.xml",
    court="CE",
    body="Le requérant demande. Le juge décide.",
    ecli="",
):
    return f"""<?xml version="1.0" encoding="UTF-8"?><Document><Identification>{identifier}</Identification>
    <Code_Juridiction>{court}</Code_Juridiction><Nom_Juridiction>Juridiction fictive</Nom_Juridiction>
    <Numero_Dossier>123</Numero_Dossier><Numero_ECLI>{ecli}</Numero_ECLI>
    <Date_Lecture>2021-09-27</Date_Lecture>
    <Texte_Integral><p>{body}</p><p>Dispositif fictif.</p></Texte_Integral></Document>""".encode()


def zipped(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, raw in entries:
            archive.writestr(name, raw)
    return stream.getvalue()


async def test_real_transport_contract_import_search_pages_and_withdrawal(tmp_path):
    entries = [(f"DCE_{i}_20210927.xml", xml(f"DCE_{i}_20210927.xml")) for i in range(25)]
    raw = zipped(entries)
    transport = Transport(
        Settings(),
        httpx.AsyncClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(200, content=raw))
        ),
    )
    index = AdminIndex(str(tmp_path / "admin.sqlite"))
    service = Service(Settings(admin_db=index.path), transport)
    try:
        imported = await index.sync(URL, transport)
        assert imported["count"] == 25
        assert (await index.sync(URL, transport))["status"] == "already_imported"
        first = index.search("requerant juge", ["CE"])
        second = index.search("requerant juge", ["CE"], offset=first["next_offset"])
        assert len(first["results"]) == 20 and len(second["results"]) == 5
        assert not (
            {r["source_ref"] for r in first["results"]}
            & {r["source_ref"] for r in second["results"]}
        )
        assert index.search("inexistant", ["TA"])["results"] == []
        ref = first["results"][0]["source_ref"]
        fetched = await service.fetch(ref, length=10)
        assert (
            fetched["next_offset"] == 10
            and fetched["metadata"]["source_authenticity"] == "official"
        )
        assert (await service.fetch(fetched["source_ref"], offset=10))["content_hash"] == fetched[
            "content_hash"
        ]
        index.withdraw(ref.removeprefix("admin:"))
        with pytest.raises(SourceError):
            await service.fetch(fetched["source_ref"])
        assert index.coverage()["courts"][0]["count"] == 24
    finally:
        await service.close()


def test_ordonnance_and_ta_directory_supported(tmp_path):
    name = "ORTA_123_20210927.xml"
    index = AdminIndex(str(tmp_path / "admin.sqlite"))
    assert (
        index._import_zip(zipped([("TA06/", b""), ("TA06/" + name, xml(name, "TA06"))]), "fixture")[
            "count"
        ]
        == 1
    )
    assert index.fetch(name).source_authenticity == "unknown"
    assert len(index.search("juge", ["TA"])["results"]) == 1


def test_exact_identifiers_variants_and_relevance(tmp_path):
    index = AdminIndex(str(tmp_path / "admin.sqlite"))
    entries = [
        (
            "DCE_123_20210927.xml",
            xml(
                ecli="ECLI:FR:CE:2021:123.20210927",
                body="Compétence compétence délégation du conseil.",
            ),
        ),
        ("DCE_456_20210927.xml", xml("DCE_456_20210927.xml", body="Compétence autre question.")),
    ]
    index._import_zip(zipped(entries), URL)
    assert index.search("DCE_123_20210927.xml")["results"][0]["source_ref"].endswith(
        "123_20210927.xml"
    )
    assert index.search("ECLI:FR:CE:2021:123.20210927")["results"][0]["source_ref"].endswith(
        "123_20210927.xml"
    )
    assert index.search("CE n° 123")["results"][0]["source_ref"].endswith("123_20210927.xml")
    result = index.search("délégation conseil", variants=["compétence délégation"])
    assert result["results"][0]["source_ref"].endswith("123_20210927.xml")
    assert result["coverage"]["batches"] and "ArianeWeb" in result["research_hint"]


@pytest.mark.parametrize(
    "name,raw,code",
    [
        ("../bad.xml", xml(), "unsafe_archive"),
        ("/bad.xml", xml(), "unsafe_archive"),
        ("bad.xml", b'<!DOCTYPE x [<!ENTITY y "injection">]><Document/>', "unsafe_xml"),
        ("bad.xml", b"<Document/>", "invalid_admin_xml"),
        ("DCE_123_20210927.xml", xml(body=""), None),
    ],
)
def test_untrusted_zip_inputs_fail_atomically(tmp_path, name, raw, code):
    index = AdminIndex(str(tmp_path / "admin.sqlite"))
    if code:
        with pytest.raises(SourceError) as exc:
            index._import_zip(zipped([(name, raw)]), "fixture")
        assert exc.value.problem.code == code
        assert not (tmp_path / "admin.sqlite").exists()
    else:
        assert index._import_zip(zipped([(name, raw)]), "fixture")["count"] == 1


def test_duplicate_identity_and_corruption(tmp_path):
    name = "DCE_123_20210927.xml"
    index = AdminIndex(str(tmp_path / "admin.sqlite"))
    with pytest.raises(SourceError, match="Duplicate"):
        index._import_zip(zipped([("one/" + name, xml()), ("two/" + name, xml())]), "fixture")
    index._import_zip(zipped([(name, xml())]), "fixture")
    with sqlite3.connect(index.path) as db:
        db.execute("UPDATE decisions SET xml='corrupted'")
    with pytest.raises(SourceError):
        index.fetch(name)


def test_absent_corpus_is_not_zero_results():
    with pytest.raises(SourceError) as exc:
        AdminIndex("").search("test")
    assert exc.value.problem.code == "admin_index_not_configured"


def test_utf16_cannot_bypass_dtd_guard():
    with pytest.raises(SourceError):
        parse_xml(
            '<!DOCTYPE x [<!ENTITY a "unsafe">]><Document/>'.encode("utf-16"), "x.xml", "fixture"
        )
