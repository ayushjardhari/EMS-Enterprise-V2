"""Safe, dependency-light text extraction for PDF/DOCX employee documents."""
import re
from io import BytesIO

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_pdf_text(file_data: bytes) -> str:
    reader = PdfReader(BytesIO(file_data))
    return "\n".join(text for page in reader.pages if (text := page.extract_text()))


def extract_docx_text(file_data: bytes) -> str:
    document = DocxDocument(BytesIO(file_data))
    return "\n".join(p.text.strip() for p in document.paragraphs if p.text.strip())


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def extract_text(file_data: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        return clean_text(extract_pdf_text(file_data))
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return clean_text(extract_docx_text(file_data))
    raise ValueError("Unsupported document type for text extraction")
