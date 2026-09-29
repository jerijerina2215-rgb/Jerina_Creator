import re
from datetime import date

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any


def _validate_structured_text(value: str, field_name: str, maximum_length: int = 200) -> str:
    value = value.strip()
    lowered = value.lower()
    if not value:
        raise ValueError(f"{field_name} is required")
    if len(value) > maximum_length:
        raise ValueError(f"{field_name} is too long")
    if "\n" in value or "\r" in value or ";" in value:
        raise ValueError(f"{field_name} must contain one structured value, not clauses")
    if re.search(r"\[\s*(insert|name|address|price|date|vin)|\b(todo|instruction|example)\b", lowered):
        raise ValueError(f"{field_name} contains a placeholder or instruction")
    return value


class Party(BaseModel):
    name: str
    address: Optional[str] = None
    role: Optional[str] = None

    @validator("name")
    def validate_name(cls, value):
        value = _validate_structured_text(value, "Party name", 120)
        if re.search(r"\b(no\s+replacement|no\s+return|payment|confidential|shall|must|agree|whereas)\b", value, re.I):
            raise ValueError("Party name appears to contain a legal clause or unrelated text")
        if len(re.findall(r"\s+", value)) > 12:
            raise ValueError("Party name must be a person or company name, not a sentence")
        return value

    @validator("address")
    def validate_address(cls, value):
        if value is None:
            return value
        return _validate_structured_text(value, "Party address", 300)

    @validator("role")
    def validate_role(cls, value):
        if value is None:
            return value
        return _validate_structured_text(value, "Party role", 80)


class DocumentRequest(BaseModel):
    document_type: str = Field(..., example="NDA")
    party_a: Party
    party_b: Party
    effective_date: str
    jurisdiction: Optional[str] = ""
    key_terms: Optional[Dict[str, Any]] = {}
    custom_clauses: Optional[str] = ""
    markdown: Optional[str] = None

    @validator("document_type")
    def validate_document_type(cls, value):
        value = _validate_structured_text(value, "Document type", 120)
        if re.search(r"[.;:!?]", value):
            raise ValueError("Document type must be a document name, not a sentence or clause")
        return value

    @validator("effective_date")
    def validate_effective_date(cls, value):
        value = value.strip()
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise ValueError("Effective date must use YYYY-MM-DD format") from error
        return value
