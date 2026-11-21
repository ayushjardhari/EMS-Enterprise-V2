from eval_data.personas import PERSONAS
from eval_data.requirements import REQUIREMENTS
from eval_data.resume_builder import build_docx, email_for, resume_text
from app.services.document_extraction import extract_text
from app.services.section_chunking import split_into_sections

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
NAMES = {p.name for p in PERSONAS}
BY_NAME = {p.name: p for p in PERSONAS}


def test_personas_are_unique_and_valid():
    assert len(PERSONAS) == 30
    assert len({email_for(p) for p in PERSONAS}) == 30
    assert all(p.availability in {"AVAILABLE", "PARTIALLY_AVAILABLE", "UNAVAILABLE"} for p in PERSONAS)
    assert all(p.skills for p in PERSONAS)


def test_every_resume_splits_into_expected_sections():
    for p in PERSONAS:
        sections = [name for name, _ in split_into_sections(resume_text(p))]
        for expected in ("summary", "skills", "experience", "education"):
            assert expected in sections, f"{p.name} missing {expected}"


def test_docx_round_trips_through_text_extraction():
    p = PERSONAS[0]
    text = extract_text(build_docx(p), DOCX_MIME)
    assert p.name in text and "Skills" in text
    assert "experience" in [n for n, _ in split_into_sections(text)]


def test_requirement_labels_reference_real_people_and_respect_filters():
    assert len(REQUIREMENTS) == 16
    assert len({r["id"] for r in REQUIREMENTS}) == 16
    for req in REQUIREMENTS:
        assert req["relevant"], req["id"]
        assert set(req["relevant"]) <= NAMES, req["id"]
        assert set(req["relevant"].values()) <= {1, 2}
        allowed = req["filters"].get("availability")
        if allowed:
            for name in req["relevant"]:
                assert BY_NAME[name].availability in allowed, f"{req['id']}: {name} fails the availability filter"
