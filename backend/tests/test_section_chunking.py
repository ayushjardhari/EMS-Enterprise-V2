from app.services.section_chunking import chunk_document, detect_heading, split_into_sections

RESUME = """Asha Verma
asha@example.com | Dehradun

Summary
Backend engineer with 4 years of experience building APIs.

Technical Skills:
Python, FastAPI, PostgreSQL, Docker, Kubernetes

WORK EXPERIENCE
Built a document pipeline at Acme.

Projects
Talent matching system using pgvector.

Education
B.Tech in Computer Science

Certifications & Licenses
AWS Cloud Practitioner
"""


def test_detect_heading_variants():
    assert detect_heading("Technical Skills:") == "skills"
    assert detect_heading("WORK EXPERIENCE") == "experience"
    assert detect_heading("Certifications & Licenses") == "certifications"
    assert detect_heading("I have work experience in Python and many other things.") is None
    assert detect_heading("") is None


def test_split_into_sections_order_and_general():
    sections = [name for name, _ in split_into_sections(RESUME)]
    assert sections == ["general", "summary", "skills", "experience", "projects", "education", "certifications"]


def test_chunks_never_mix_sections():
    chunks = chunk_document(RESUME)
    by_section = {c.section: c.content for c in chunks}
    assert "Kubernetes" in by_section["skills"] and "Kubernetes" not in by_section["experience"]
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_long_section_is_split_with_running_index():
    long_experience = "Experience\n" + "\n\n".join(f"Paragraph {i} " + "x" * 400 for i in range(6))
    chunks = chunk_document(long_experience, chunk_size=1000, chunk_overlap=100)
    assert len(chunks) > 1
    assert {c.section for c in chunks} == {"experience"}


def test_text_without_headings_is_general():
    chunks = chunk_document("Just a paragraph with no headings at all.")
    assert [c.section for c in chunks] == ["general"]


def test_empty_text_gives_no_chunks():
    assert chunk_document("   \n  ") == []
