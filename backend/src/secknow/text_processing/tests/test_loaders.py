from __future__ import annotations

from pathlib import Path

from docx import Document

from secknow.text_processing.loaders.router import load_document_text


def test_load_text_and_markdown(tmp_path: Path) -> None:
    """txt/md 文件应能正确读取。"""
    txt = tmp_path / "sample.txt"
    md = tmp_path / "sample.md"
    txt.write_text("hello txt", encoding="utf-8")
    md.write_text("# 标题\n正文", encoding="utf-8")

    assert load_document_text(txt) == "hello txt"
    assert "标题" in load_document_text(md)


def test_load_docx(tmp_path: Path) -> None:
    """docx 文件应能提取段落文本。"""
    file_path = tmp_path / "sample.docx"
    doc = Document()
    doc.add_paragraph("第一段")
    doc.add_paragraph("第二段")
    doc.save(file_path)

    text = load_document_text(file_path)
    assert "第一段" in text
    assert "第二段" in text


def test_load_pdf_with_monkeypatch(tmp_path: Path, monkeypatch) -> None:
    """pdf 路由应调用 pdf_loader 并返回拼接文本。"""
    file_path = tmp_path / "sample.pdf"
    file_path.write_bytes(b"%PDF-1.4")

    class _FakePage:
        def __init__(self, content: str):
            self._content = content

        def extract_text(self) -> str:
            return self._content

    class _FakePdf:
        pages = [_FakePage("第一页"), _FakePage("第二页")]

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(
        "secknow.text_processing.loaders.pdf_loader.pdfplumber.open",
        lambda *_args, **_kwargs: _FakePdf(),
    )

    text = load_document_text(file_path)
    assert "第一页" in text
    assert "第二页" in text
