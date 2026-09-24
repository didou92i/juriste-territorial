"""Bounded local extraction. OCR output is evidence to review, never certified text."""

import csv
import io
import shutil
import subprocess
import tempfile
import zipfile
from collections import defaultdict
from pathlib import Path

from docx import Document as DocxDocument
from docx.table import Table
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .models import TextLocator

MAX_DOCUMENT_BYTES = 20_000_000
MAX_EXTRACTED_CHARS = 2_000_000
MAX_PDF_PAGES = 200
MAX_LOCATORS = 5000


def _assemble(parts):
    content, locators = "", []
    for label, value, method, confidence in parts:
        value = value.strip()
        if not value:
            continue
        prefix = f"\n[{label}]\n" if content else f"[{label}]\n"
        start = len(content) + len(prefix)
        content += prefix + value
        locators.append(
            TextLocator(
                label=label,
                start=start,
                end=len(content),
                method=method,
                confidence=confidence,
                uncertain=method == "ocr" and (confidence is None or confidence < 85),
            )
        )
        if len(content) > MAX_EXTRACTED_CHARS or len(locators) > MAX_LOCATORS:
            raise ValueError("Extracted document exceeds the text or locator limit")
    if not content:
        raise ValueError("Document has no extractable text; review it before import")
    return content, locators


def _ocr_page(raw: bytes, page_number: int, language: str):
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise ValueError("OCR requires local pdftoppm and tesseract executables")
    if not language.isalpha() or len(language) > 12:
        raise ValueError("Invalid OCR language")
    with tempfile.TemporaryDirectory(prefix="jt-ocr-") as folder:
        source = Path(folder) / "source.pdf"
        image = Path(folder) / "page"
        source.write_bytes(raw)
        try:
            subprocess.run(
                [
                    "pdftoppm",
                    "-f",
                    str(page_number),
                    "-l",
                    str(page_number),
                    "-singlefile",
                    "-r",
                    "180",
                    "-png",
                    str(source),
                    str(image),
                ],
                check=True,
                capture_output=True,
                timeout=45,
            )
            result = subprocess.run(
                ["tesseract", str(image) + ".png", "stdout", "-l", language, "tsv"],
                check=True,
                capture_output=True,
                timeout=45,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            raise ValueError(f"OCR failed on page {page_number}; no import was made") from exc
    groups = defaultdict(list)
    for row in csv.DictReader(io.StringIO(result.stdout.decode("utf-8")), delimiter="\t"):
        word = row.get("text", "").strip()
        if not word:
            continue
        try:
            confidence = float(row.get("conf", "-1"))
        except ValueError:
            confidence = -1
        key = (row.get("block_num"), row.get("par_num"), row.get("line_num"))
        groups[key].append((word, confidence))
    lines = []
    for number, words in enumerate(groups.values(), 1):
        scores = [score for _, score in words if score >= 0]
        confidence = sum(scores) / len(scores) if scores else None
        lines.append(
            (
                f"page {page_number}, ligne OCR {number}",
                " ".join(w for w, _ in words),
                "ocr",
                confidence,
            )
        )
    return lines


def extract_document(raw: bytes, suffix: str, *, ocr=False, ocr_language="fra"):
    """Return text, locators, extraction status and warnings without changing storage."""
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise ValueError("Document exceeds the 20 MB import limit")
    if suffix in {".txt", ".md"}:
        if len(raw) > 2_000_000:
            raise ValueError("Text document exceeds the 2 MB import limit")
        value = raw.decode("utf-8")
        if not value.strip():
            raise ValueError("Document is empty")
        return (
            value,
            [TextLocator(label="texte original", start=0, end=len(value), method="original_text")],
            "complete",
            [],
        )
    if suffix == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(raw), strict=True)
            if reader.is_encrypted or not 1 <= len(reader.pages) <= MAX_PDF_PAGES:
                raise ValueError("Encrypted PDF or unsupported page count")
            parts, warnings, used_ocr = [], [], False
            for index, page in enumerate(reader.pages, 1):
                value = page.extract_text() or ""
                if len(value.strip()) >= 40:
                    parts.append((f"page {index}", value, "pdf_text", None))
                elif ocr:
                    used_ocr = True
                    lines = _ocr_page(raw, index, ocr_language)
                    if lines:
                        parts.extend(lines)
                    else:
                        warnings.append(f"Page {index}: OCR returned no text")
                else:
                    warnings.append(f"Page {index}: little or no text; OCR/review needed")
            text, locators = _assemble(parts)
            if used_ocr:
                warnings.append(
                    "OCR text and uncertain passages require comparison with the original"
                )
            warnings.append("PDF layout, signatures and images require visual review")
            return text, locators, "ocr_unreviewed" if used_ocr else "partial", warnings
        except (OSError, ValueError, PdfReadError) as exc:
            raise ValueError(f"PDF extraction failed: {exc}") from exc
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                entries = archive.infolist()
                if len(entries) > 5000 or sum(x.file_size for x in entries) > 40_000_000:
                    raise ValueError("DOCX expanded size exceeds the import limit")
                names = {x.filename for x in entries}
            doc = DocxDocument(io.BytesIO(raw))
            parts, paragraph, table = [], 0, 0
            for element in doc.iter_inner_content():
                if isinstance(element, Table):
                    table += 1
                    for row_number, row in enumerate(element.rows, 1):
                        parts.append(
                            (
                                f"tableau {table}, ligne {row_number}",
                                " | ".join(cell.text for cell in row.cells),
                                "docx_text",
                                None,
                            )
                        )
                else:
                    paragraph += 1
                    parts.append((f"paragraphe {paragraph}", element.text, "docx_text", None))
            text, locators = _assemble(parts)
            warnings = [
                "DOCX layout, signatures and pagination require visual review",
                "Headers, footers and text boxes are not included in extracted text",
            ]
            if (
                any(name.startswith("word/media/") for name in names)
                or {"word/footnotes.xml", "word/endnotes.xml"} & names
            ):
                warnings.append("Embedded images or notes are not included in extracted text")
            return text, locators, "partial", warnings
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            raise ValueError(f"DOCX extraction failed: {exc}") from exc
    raise ValueError("Supported imports: UTF-8 .txt/.md, .pdf and .docx")
