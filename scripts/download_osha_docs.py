"""
Download real OSHA compliance documents for Codex demo.
Run: python scripts/download_osha_docs.py
"""

import os
import sys
from pathlib import Path

import requests

OSHA_DOCS = [
    {
        "url": "https://www.osha.gov/sites/default/files/publications/OSHA3146.pdf",
        "name": "OSHA3146_Crane_Safety.pdf",
        "desc": "Crane and Derrick Safety",
    },
    {
        "url": "https://www.osha.gov/sites/default/files/publications/osha3150.pdf",
        "name": "OSHA3150_Fall_Protection.pdf",
        "desc": "Fall Protection in Construction",
    },
    {
        "url": "https://www.osha.gov/sites/default/files/publications/osha3124.pdf",
        "name": "OSHA3124_Scaffolding.pdf",
        "desc": "Scaffolding Safety",
    },
    {
        "url": "https://www.osha.gov/sites/default/files/publications/OSHA3010.pdf",
        "name": "OSHA3010_Electrical_Safety.pdf",
        "desc": "Electrical Safety in Construction",
    },
    {
        "url": "https://www.osha.gov/sites/default/files/publications/OSHA3154.pdf",
        "name": "OSHA3154_Trenching_Excavation.pdf",
        "desc": "Trenching and Excavation Safety",
    },
    {
        "url": "https://www.osha.gov/sites/default/files/publications/OSHA3088.pdf",
        "name": "OSHA3088_Heat_Stress.pdf",
        "desc": "Heat Stress in Construction",
    },
]

def download_docs(output_dir: str = "sample_docs"):
    """Download OSHA documents to the sample_docs directory."""
    out = Path(output_dir)
    out.mkdir(exist_ok=True)

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Codex-Compliance-Agent/1.0)"
    }

    success = 0
    failed = []

    for doc in OSHA_DOCS:
        dest = out / doc["name"]
        if dest.exists():
            print(f"  ⏭️  Already exists: {doc['name']}")
            success += 1
            continue

        print(f"  ⬇️  Downloading: {doc['desc']}...")
        try:
            response = requests.get(doc["url"], headers=headers, timeout=30)
            response.raise_for_status()

            # Verify it's actually a PDF
            if b"%PDF" not in response.content[:10]:
                print(f"  ⚠️  Not a valid PDF, skipping: {doc['name']}")
                failed.append(doc["name"])
                continue

            with open(dest, "wb") as f:
                f.write(response.content)

            size_kb = len(response.content) // 1024
            print(f"  ✅  Saved: {doc['name']} ({size_kb} KB)")
            success += 1

        except Exception as e:
            print(f"  ❌  Failed: {doc['name']} — {e}")
            failed.append(doc["name"])

    print(f"\n{'='*50}")
    print(f"Downloaded: {success}/{len(OSHA_DOCS)} documents")
    if failed:
        print(f"Failed: {', '.join(failed)}")
    print(f"Location: {out.resolve()}")
    print(f"{'='*50}")
    print("\nNext step: Run the Streamlit app and upload these PDFs,")
    print("or they will be auto-ingested on startup.")
    return success


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "sample_docs"
    print("=" * 50)
    print("Codex - OSHA Document Downloader")
    print("=" * 50)
    download_docs(output)
