"""Section-aware resume chunking.

Resume text is first split into logical sections (summary, skills,
experience, projects, education, certifications, achievements) by detecting
heading lines, then each section is chunked on its own so a chunk never
mixes unrelated sections. Text before the first heading (usually name and
contact details) goes into a "general" section.

This is a heuristic splitter: it only recognises headings that sit on their
own line and match a known title. Resumes with unusual headings fall back to
"general" for that content.
"""
import re
from dataclasses import dataclass

from app.services.document_chunking import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    chunk_text,
)

GENERAL_SECTION = "general"

SECTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "professional summary", "profile", "professional profile", "objective",
                "career objective", "about me", "about"),
    "skills": ("skills", "technical skills", "key skills", "core competencies", "skills and tools",
               "technologies", "tech stack"),
    "experience": ("experience", "work experience", "professional experience", "employment history",
                   "work history", "internships", "internship experience"),
    "projects": ("projects", "academic projects", "personal projects", "key projects"),
    "education": ("education", "academic background", "academic qualifications", "qualifications"),
    "certifications": ("certifications", "certificates", "licenses and certifications",
                       "certifications and licenses", "courses"),
    "achievements": ("achievements", "awards", "honors", "accomplishments", "awards and achievements"),
}

_HEADING_LOOKUP = {title: section for section, titles in SECTION_HEADINGS.items() for title in titles}
_MAX_HEADING_LEN = 40


@dataclass(frozen=True)
class SectionChunk:
    section: str
    chunk_index: int  # running index across the whole document
    content: str


def detect_heading(line: str) -> str | None:
    """Return the canonical section name if ``line`` is a known heading, else None."""
    candidate = line.strip()
    if not candidate or len(candidate) > _MAX_HEADING_LEN:
        return None
    candidate = candidate.rstrip(":").strip().lower().replace("&", " and ")
    candidate = re.sub(r"[^a-z\s]", " ", candidate)
    candidate = re.sub(r"\s+", " ", candidate).strip()
    return _HEADING_LOOKUP.get(candidate)


def split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split text into ``(section, body)`` pairs, in document order.

    A section name can appear more than once (e.g. two "Projects" blocks);
    each block is kept separately.
    """
    sections: list[tuple[str, list[str]]] = [(GENERAL_SECTION, [])]
    for line in text.splitlines():
        heading = detect_heading(line)
        if heading is not None:
            sections.append((heading, []))
        else:
            sections[-1][1].append(line)
    result = []
    for name, lines in sections:
        body = "\n".join(lines).strip()
        if body:
            result.append((name, body))
    return result


def chunk_document(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[SectionChunk]:
    chunks: list[SectionChunk] = []
    for section, body in split_into_sections(text):
        for piece in chunk_text(body, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            chunks.append(SectionChunk(section=section, chunk_index=len(chunks), content=piece))
    return chunks
