import os
import sys
# ensure project root is on sys.path so `from app import exporter` works
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import exporter

SAMPLE_MD = """
# Sample Agreement

This is a sample agreement between Alice and Bob.

## Terms

- Term A: Definition A
- Term B: Definition B

"""

def main():
    payload = {
        "key_terms": {"Term A": "Definition A", "Term B": "Definition B"},
        "logo_path": os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.png')
    }
    pdf_bytes = exporter.to_pdf(SAMPLE_MD, payload)
    out = os.path.join(os.path.dirname(__file__), '..', 'exports')
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, 'sample_export.pdf')
    with open(path, 'wb') as f:
        f.write(pdf_bytes)
    print('Wrote', path)

if __name__ == '__main__':
    main()
