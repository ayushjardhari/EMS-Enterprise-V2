"""Turns a Persona into resume text and a .docx file."""
from io import BytesIO

from docx import Document as DocxDocument
from docx.shared import Pt

from eval_data.personas import Persona


def email_for(persona: Persona) -> str:
    first, last = persona.name.lower().split()
    return f"{first}.{last}@eval.acmecorp.example"


def resume_blocks(p: Persona) -> list[tuple[str, str]]:
    """Ordered (kind, text) blocks; kind is name | meta | heading | body | bullet | subhead."""
    blocks = [("name", p.name), ("meta", f"{p.role} | {p.location} | {email_for(p)}"),
              ("heading", "Summary"), ("body", p.summary),
              ("heading", "Skills"), ("body", p.skills_line),
              ("heading", "Experience")]
    for title, company, period, bullets in p.experience:
        blocks.append(("subhead", f"{title}, {company} ({period})"))
        blocks += [("bullet", b) for b in bullets]
    if p.projects:
        blocks.append(("heading", "Projects"))
        for name, bullets in p.projects:
            blocks.append(("subhead", name))
            blocks += [("bullet", b) for b in bullets]
    blocks += [("heading", "Education"), ("body", p.education)]
    if p.certifications:
        blocks.append(("heading", "Certifications"))
        blocks += [("bullet", c) for c in p.certifications]
    return blocks


def resume_text(p: Persona) -> str:
    lines = []
    for kind, text in resume_blocks(p):
        lines.append(f"• {text}" if kind == "bullet" else text)
    return "\n".join(lines)


def build_docx(p: Persona) -> bytes:
    doc = DocxDocument()
    for kind, text in resume_blocks(p):
        para = doc.add_paragraph()
        run = para.add_run(f"• {text}" if kind == "bullet" else text)
        if kind == "name":
            run.bold, run.font.size = True, Pt(18)
        elif kind == "heading":
            run.bold, run.font.size = True, Pt(13)
        elif kind == "subhead":
            run.bold = True
    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
