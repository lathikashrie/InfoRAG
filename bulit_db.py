from vector import build_index, save_index

# Example chunks (replace with your real data)
chunks = ["sample text about fees", "sample text about hostel"]

embeddings, chunks = build_index(chunks)
save_index(embeddings, chunks)

print("✅ Index built successfully")