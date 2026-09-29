import requests
import json
import sys

API = "http://localhost:8000"

payload = {
    "document_type": "NDA",
    "party_a": {"name": "Alice Corp", "address": "123 Main St"},
    "party_b": {"name": "Bob LLC", "address": "456 Elm St"},
    "effective_date": "2026-09-24",
    "jurisdiction": "CA",
    "key_terms": {"payment": "$1000", "term": "12 months"},
    "custom_clauses": "The parties agree to a mock testing clause.",
}


def save_binary(resp, path):
    with open(path, "wb") as f:
        f.write(resp.content)


def main():
    try:
        print("Calling /generate...")
        r = requests.post(f"{API}/generate", json=payload, timeout=30)
        print("Status:", r.status_code)
        if r.status_code != 200:
            print(r.text)
            sys.exit(2)
        md = r.json().get("markdown", "")
        with open("generated.md", "w", encoding="utf-8") as f:
            f.write(md)
        print("Wrote generated.md (chars):", len(md))

        for fmt in ("txt", "docx", "pdf"):
            print(f"Exporting {fmt}...")
            r2 = requests.post(f"{API}/export/{fmt}", json=payload, timeout=60)
            print("Status:", r2.status_code)
            if r2.status_code == 200:
                out = f"exported.{fmt}"
                save_binary(r2, out)
                print("Saved", out)
            else:
                print("Failed export", fmt, r2.status_code, r2.text)

        print("Manual test completed successfully.")
    except Exception as e:
        print("Error during manual test:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()
