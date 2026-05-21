"""
Run this script ONCE before starting the chatbot.
It will:
  1. Crawl the entire avinuty.ac.in website
  2. Build a searchable index of all pages
  3. Download all PDF brochures found on the site
  4. Register brochures into the database

After this, the chatbot will:
  - Link to the exact relevant page (not just homepage)
  - Answer questions from brochures too
"""

from web_scraper import crawl_site, download_pdfs
from db import init_db, insert_dataset, get_all_datasets
from file_reader import read_file
from chunking import chunk_text
import os

BROCHURE_DIR = os.path.join(os.path.dirname(__file__), "uploads", "brochures")

def register_brochures():
    """Register downloaded PDFs into the database."""
    if not os.path.exists(BROCHURE_DIR):
        return

    existing       = get_all_datasets()
    existing_names = {r["filename"] for r in existing}

    pdfs = [f for f in os.listdir(BROCHURE_DIR) if f.endswith(".pdf")]
    if not pdfs:
        print("⚠️ No PDFs found in brochures folder.")
        return

    for fname in pdfs:
        if fname in existing_names:
            print(f"✅ Already registered: {fname}")
            continue

        fpath = os.path.join(BROCHURE_DIR, fname)
        try:
            text   = read_file(fpath)
            chunks = chunk_text(text)
            insert_dataset(fname, fpath, "pdf", len(chunks))
            print(f"✅ Registered brochure: {fname} ({len(chunks)} chunks)")
        except Exception as e:
            print(f"❌ Failed: {fname} — {e}")

if __name__ == "__main__":
    print("=" * 55)
    print("  AVINUTY CHATBOT — ONE-TIME SETUP")
    print("=" * 55)

    print("\n📋 Step 1: Initializing database...")
    init_db()

    print("\n🌐 Step 2: Crawling university website...")
    pages = crawl_site(max_pages=80)
    print(f"  → Indexed {len(pages)} pages")

    print("\n📥 Step 3: Downloading PDF brochures...")
    pdfs = download_pdfs(max_pdfs=20)
    print(f"  → Downloaded {len(pdfs)} PDFs")

    print("\n📂 Step 4: Registering brochures into database...")
    register_brochures()

    print("\n" + "=" * 55)
    print("✅ Setup complete!")
    print("👉 Now run: py register_db.py")
    print("👉 Then:    py app.py")
    print("=" * 55)