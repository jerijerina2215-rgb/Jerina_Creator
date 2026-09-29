from typing import Dict
from ai_core.gemini_generator import GeminiDocumentGenerator


generator = GeminiDocumentGenerator()


def generate_document(payload: Dict) -> str:
    return generator.generate_document(
        payload.get("document_type", "AGREEMENT"),
        payload.get("party_a", {}),
        payload.get("party_b", {}),
        payload.get("effective_date", ""),
        payload.get("jurisdiction", ""),
        payload.get("key_terms", {}),
        payload.get("custom_clauses", ""),
    )
