import os
from file_reader import read_file
from chunking import chunk_text
from db import init_db, insert_dataset, get_all_datasets

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
ALLOWED_EXTENSIONS = {".pdf", ".csv", ".xlsx", ".xls", ".txt", ".docx", ".json"}


def register_all():
    init_db()

    existing_names = {row["filename"] for row in get_all_datasets()}

    if not os.path.exists(UPLOAD_FOLDER):
        print(f"❌ uploads/ folder not found. Create it and add your dataset files.")
        return

    files = os.listdir(UPLOAD_FOLDER)
    if not files:
        print("⚠️  No files found in uploads/ folder.")
        return

    for filename in files:
        ext = os.path.splitext(filename)[1].lower()

        if ext not in ALLOWED_EXTENSIONS:
            print(f"⏭️  Skipping unsupported file: {filename}")
            continue

        if filename in existing_names:
            print(f"✅ Already registered, skipping: {filename}")
            continue

        filepath = os.path.join(UPLOAD_FOLDER, filename)

        try:
            print(f"📄 Reading:  {filename}")
            text = read_file(filepath)

            print(f"✂️  Chunking: {filename}")
            chunks = chunk_text(text)

            insert_dataset(filename, filepath, ext.replace(".", ""), len(chunks))
            print(f"✅ Registered: {filename} → {len(chunks)} chunks\n")

        except Exception as e:
            print(f"❌ Skipping {filename} — Error: {e}\n")

    print("🎉 All datasets registered!")
    print("👉 Now run: py app.py")


if __name__ == "__main__":
    register_all()