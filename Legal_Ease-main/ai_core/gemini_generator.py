import os
import re
import requests
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")
GEMINI_API_URL = os.getenv(
    "GEMINI_API_URL",
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
)


class GeminiDocumentGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or GEMINI_API_KEY

    def build_prompt(self, document_type: str, party_a: Dict, party_b: Dict, effective_date: str, jurisdiction: str, key_terms: Dict, custom_clauses: str) -> str:
        party_a_label = party_a.get("role") or "Party A"
        party_b_label = party_b.get("role") or "Party B"
        return (
            "You are LegalEase AI, an AI legal-document drafter and quality checker. "
            "Generate one polished Markdown agreement based strictly on the supplied information. "
            "Never claim that the document is guaranteed legally valid, complete, or error-free in every jurisdiction.\n\n"
            "Before returning the document, silently validate and correct it. The final document must:\n"
            f"- Match the exact document type: {document_type}. Use only terminology, clauses, rights, and duties relevant to that type.\n"
            f"- Use these exact party pairings everywhere, including definitions and signatures: {party_a_label}: {party_a.get('name')}; {party_b_label}: {party_b.get('name')}. Do not rename roles.\n"
            f"- Use one consistent date format and the effective date {effective_date}; never invent another date.\n"
            "- Define only terms that are used, keep defined meanings consistent, and remove duplicate definitions.\n"
            "- Preserve every supplied custom clause and its intended meaning. Include each clause verbatim at least once, then clarify it where appropriate.\n"
            "- Never fabricate names, addresses, prices, currencies, IDs, VINs, property details, statutes, legal authorities, or other facts. Use explicit placeholders such as [INSERT PURCHASE PRICE] for missing essential information.\n"
            "- Keep payment, dates, duties, ownership, possession, termination, warranties, liability, insurance, fees, and dispute rules internally consistent.\n"
            "- Include only relevant provisions. Add appropriate payment, performance, representations, default, termination, governing law, notices, entire agreement, amendments, severability, and signature clauses when relevant to this document type.\n"
            "- Use neutral jurisdiction wording when no jurisdiction is supplied.\n"
            "- Do not insert jurisdiction-specific agencies, statutes, legal authorities, or regulatory requirements unless the jurisdiction and document type support them.\n"
            "- Use sequential headings and numbering, clean Markdown, consistent capitalization, complete signature blocks with printed names and dates, and no accidental placeholders.\n"
            "- End with this concise disclaimer: LegalEase AI generated this template. Have a qualified legal professional review it for compliance with applicable laws and regulations.\n\n"
            "- Do not repeat raw custom clauses after they have been incorporated into their proper contractual provisions.\n"
            "- Do not output internal labels, input summaries, processing notes, prompts, model metadata, or validation logs.\n"
            "Return only the final polished legal document and disclaimer. Do not describe your validation or corrections.\n\n"
            f"Document type: {document_type}\n"
            f"{party_a_label}: {party_a.get('name')}\n"
            f"{party_b_label}: {party_b.get('name')}\n"
            f"Effective date: {effective_date}\n"
            f"Jurisdiction: {jurisdiction or '[JURISDICTION NOT PROVIDED]'}\n"
            f"Key terms: {key_terms}\n"
            f"Custom clauses: {custom_clauses or '[NO CUSTOM CLAUSES PROVIDED]'}\n"
        )

    def generate_document(self, document_type: str, party_a: Dict, party_b: Dict, effective_date: str, jurisdiction: str = "", key_terms: Dict = None, custom_clauses: str = "") -> str:
        prompt = self.build_prompt(document_type, party_a, party_b, effective_date, jurisdiction, key_terms or {}, custom_clauses)
        if not self.api_key:
            # fallback mocked response
            return self._mock(document_type, party_a, party_b, effective_date, custom_clauses)

        headers = {"Content-Type": "application/json"}
        params = {"key": self.api_key}
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2000},
        }
        try:
            resp = requests.post(
                GEMINI_API_URL,
                params=params,
                json=body,
                headers=headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            text = None
            if isinstance(data, dict):
                if "candidates" in data and data["candidates"]:
                    content = data["candidates"][0].get("content", {})
                    parts = content.get("parts", []) if isinstance(content, dict) else []
                    text = "".join(
                        part.get("text", "") for part in parts if isinstance(part, dict)
                    )
                text = text or data.get("output") or data.get("text")
            if not text:
                return self._mock(document_type, party_a, party_b, effective_date, custom_clauses)
            return self._preserve_input_details(text, party_a, party_b, custom_clauses)
        except Exception:
            return self._mock(document_type, party_a, party_b, effective_date, custom_clauses)

    @staticmethod
    def _preserve_input_details(text, party_a, party_b, custom_clauses):
        required_terms = [
            GeminiDocumentGenerator._normalize_clause(item.strip())
            for item in custom_clauses.split(";")
            if item.strip()
        ]
        text = GeminiDocumentGenerator._clean_internal_labels(text)
        for incorrect, correct in {
            "replcement": "replacement",
            "replacment": "replacement",
            "confidencial": "confidential",
            "paymant": "payment",
        }.items():
            text = re.sub(rf"\b{incorrect}\b", correct, text, flags=re.I)
        missing_terms = [term for term in required_terms if term.lower() not in text.lower()]
        missing_parties = []
        for party in (party_a, party_b):
            name = party.get("name", "").strip()
            role = party.get("role", "").strip()
            if name and role and name.lower() not in text.lower():
                missing_parties.append((role, name))
        if not missing_terms and not missing_parties:
            return text

        if missing_terms:
            additions = "\n### Additional Contractual Terms\n" + "\n".join(
                f"{index}. {term}" for index, term in enumerate(missing_terms, start=1)
            )
            signature_position = text.lower().find("signature")
            if signature_position >= 0:
                insertion = text.rfind("\n", 0, signature_position)
                text = text[:insertion] + additions + "\n" + text[insertion:]
            else:
                text = text.rstrip() + "\n\n" + additions + "\n"

        if missing_parties:
            signature_lines = "\n\n### SIGNATURES\n" + "\n".join(
                f"**{role}:** {name}\nSignature: ____________________\nDate: ____________________"
                for role, name in missing_parties
            )
            text = text.rstrip() + signature_lines + "\n"
        return text

    @staticmethod
    def _normalize_clause(clause):
        replacements = {
            "replcement": "replacement",
            "replacment": "replacement",
            "confidencial": "confidential",
            "paymant": "payment",
        }
        for incorrect, correct in replacements.items():
            clause = re.sub(rf"\b{incorrect}\b", correct, clause, flags=re.I)
        return clause

    @staticmethod
    def _clean_internal_labels(text):
        forbidden = (
            "Supplied Terms and Parties",
            "User Input",
            "Provided Information",
            "AI Notes",
            "Input Data",
            "Generated From",
        )
        lines = [line for line in text.splitlines() if not any(label.lower() in line.lower() for label in forbidden)]
        return "\n".join(lines)

    def _mock(self, document_type, party_a, party_b, effective_date, custom_clauses=""):
        clauses = [item.strip() for item in custom_clauses.split(";") if item.strip()]
        clause_text = "\n".join(f"- {clause}" for clause in clauses)
        terms_section = f"\n## Terms & Conditions\n{clause_text}\n" if clause_text else ""
        provisions = self._operative_provisions(clauses, document_type)
        provision_text = "\n".join(
            f"{index}. {heading}: {clause}"
            for index, (heading, clause) in enumerate(provisions, start=1)
        )
        return (
            f"# {document_type}\n\n"
            f"Preamble: This is a mock {document_type} between {party_a.get('name')} and {party_b.get('name')} effective {effective_date}.\n\n"
            f"## Definitions\n- {party_a.get('role') or 'Party A'}: {party_a.get('name')}\n- {party_b.get('role') or 'Party B'}: {party_b.get('name')}\n\n"
            f"{terms_section}\n## Operative Provisions\n{provision_text}\n\n"
            f"## Signature\n{party_a.get('role') or 'Party A'}: __________________\n{party_b.get('role') or 'Party B'}: __________________\n"
        )

    @staticmethod
    def _operative_provisions(clauses, document_type):
        if not clauses:
            return [("General Obligations", f"The parties shall perform their obligations under this {document_type}.")]

        categories = (
            (("payment", "fee", "invoice", "price", "compensation"), "Payment Terms"),
            (("deliver", "photo", "product", "service", "milestone"), "Deliverables and Performance"),
            (("confidential", "non-disclosure", "proprietary"), "Confidentiality"),
            (("cancel", "terminat", "notice"), "Term and Termination"),
            (("intellectual property", "copyright", "ownership", "license"), "Intellectual Property"),
            (("govern", "jurisdiction", "law"), "Governing Law"),
        )
        provisions = []
        for clause in clauses:
            normalized = clause.lower()
            heading = "General Obligations"
            for keywords, candidate in categories:
                if any(keyword in normalized for keyword in keywords):
                    heading = candidate
                    break
            provisions.append((heading, clause))
        return provisions
