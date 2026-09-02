from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from core.errors import ValidationError
from core.settings import settings
from services.document_parser import DocumentParser, sanitize_filename


def test_parse_txt():
    file_type, text = DocumentParser().parse("notes.txt", b"Hello\nworld")

    assert file_type == "txt"
    assert text == "Hello\nworld"


def test_parse_docx():
    document_xml = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        b'<w:body><w:p><w:r><w:t>Document text</w:t></w:r></w:p></w:body>'
        b'</w:document>'
    )
    content_types = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        b'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        b'</Types>'
    )
    relationships = (
        b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        b'</Relationships>'
    )
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document_xml)

    file_type, text = DocumentParser().parse("notes.docx", buffer.getvalue())

    assert file_type == "docx"
    assert text == "Document text"


def test_parse_sanitizes_path_like_names():
    file_type, text = DocumentParser().parse("C:/fakepath/notes with spaces.txt", b"Hello\nworld")

    assert file_type == "txt"
    assert text == "Hello\nworld"


def test_parse_txt_utf16():
    file_type, text = DocumentParser().parse("notes.txt", "Hello from UTF-16".encode("utf-16"))

    assert file_type == "txt"
    assert text == "Hello from UTF-16"


def test_sanitize_filename_falls_back_for_extension_only_names():
    assert sanitize_filename(" .pdf ") == "uploaded-document.pdf"
    assert sanitize_filename("C:/fakepath/") == "uploaded-document"


def test_parse_rejects_unsupported_type():
    with pytest.raises(ValidationError):
        DocumentParser().parse("notes.rtf", b"text")


def test_extracted_text_limit_remains_validation_error(monkeypatch):
    monkeypatch.setattr(settings, "MAX_DOCUMENT_CONTENT_LENGTH", 3)

    with pytest.raises(ValidationError, match="exceeds"):
        DocumentParser().parse("notes.txt", b"text")
