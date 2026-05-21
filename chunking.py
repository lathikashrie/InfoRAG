def chunk_text(text, size=300, overlap=20):
    """
    Smart dual-mode chunker:
    - Line-by-line  → best for structured data (CSV rows, JSON, TXT with labels)
    - Sliding window → best for prose (PDF, DOCX paragraphs)
    Uses a set() to deduplicate overlapping chunks automatically.
    """
    print("🔍 Chunking started...")

    if not text or not text.strip():
        print("❌ Empty text received")
        return []

    text_lower = text.lower()
    chunks = set()

    # --- LINE-BY-LINE (each row = one chunk) ---
    lines = [line.strip() for line in text_lower.split("\n")
             if line.strip() and len(line.strip()) > 5]

    for line in lines:
        chunks.add(line)

    # Pair adjacent lines (gives more context for QA retrieval)
    for i in range(len(lines) - 1):
        chunks.add(lines[i] + " | " + lines[i + 1])

    # --- SLIDING WINDOW (for longer prose documents) ---
    words = text_lower.split()
    if len(words) > size:
        start = 0
        while start < len(words):
            end = start + size
            chunk = " ".join(words[start:end])
            chunks.add(chunk)
            start = end - overlap

    result = list(chunks)
    print(f"✅ Total chunks: {len(result)}")
    return result
