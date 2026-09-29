from app.generator import generate_document


def test_generate_mock():
    payload = {
        "document_type": "NDA",
        "party_a": {"name": "Alice"},
        "party_b": {"name": "Bob"},
        "effective_date": "2026-09-24",
        "jurisdiction": "CA",
    }
    md = generate_document(payload)
    assert "Alice" in md
    assert "Bob" in md
