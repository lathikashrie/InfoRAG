from flask import Flask, request, jsonify, render_template
from file_reader import read_file
from chunking import chunk_text
from vector import build_index, search, load_index, save_index
from groq_ai import ask_gemini
from db import init_db, get_all_datasets, delete_dataset
from web_scraper import load_site_index, search_website, get_relevant_url, live_search_university, extract_avinuty_url
import os

app = Flask(__name__)

UPLOAD_FOLDER   = os.path.join(os.path.dirname(__file__), "uploads")
BROCHURE_FOLDER = os.path.join(UPLOAD_FOLDER, "brochures")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BROCHURE_FOLDER, exist_ok=True)

combined_index  = None
combined_chunks = []
answer_cache    = {}

# ─────────────────────────────────────────────
# ✅ INIT
# ─────────────────────────────────────────────
init_db()
load_site_index()

# ─────────────────────────────────────────────
# ✅ REBUILD INDEX
# ─────────────────────────────────────────────
def rebuild_index_from_db():
    global combined_index, combined_chunks, answer_cache

    datasets   = get_all_datasets()
    all_chunks = []

    for ds in datasets:
        filepath = ds["filepath"]
        if not os.path.exists(filepath):
            continue

        try:
            text = read_file(filepath)

            if not text or len(text.strip()) < 50:
                print(f"⚠️ Empty file skipped: {ds['filename']}")
                continue

            chunks = chunk_text(text, chunk_size=1000, overlap=200)
            all_chunks.extend(chunks)

        except Exception as e:
            print(f"⚠️ Error reading {ds['filename']}: {e}")

    if all_chunks:
        combined_index, combined_chunks = build_index(all_chunks)
        save_index(combined_index, combined_chunks)
        answer_cache = {}
        print(f"✅ Index built: {len(all_chunks)} chunks")
    else:
        combined_index, combined_chunks = None, []
        print("❌ No valid dataset loaded")


# ─────────────────────────────────────────────
# ✅ STRONG KEYWORD SEARCH (VERY IMPORTANT)
# ─────────────────────────────────────────────
def keyword_boost_search(question, chunks, top_k=10):
    q = question.lower()
    results = []

    for chunk in chunks:
        c = chunk.lower()
        score = 0

        # keyword scoring
        for word in q.split():
            if word in c:
                score += 5

        # special boosts for commonly searched topics
        if "hod" in q and "hod" in c:
            score += 40
        if "head" in q and "department" in q and "head" in c:
            score += 40
        if "faculty" in q and "faculty" in c:
            score += 20
        if "staff" in q and "staff" in c:
            score += 20
        if "fee" in q and ("fee" in c or "fees" in c):
            score += 30
        if "it" in q and ("information technology" in c or "it department" in c):
            score += 30
        if "hostel" in q and "hostel" in c:
            score += 30
        if "admission" in q and "admission" in c:
            score += 30

        if score > 0:
            results.append((score, chunk))

    results.sort(reverse=True)
    return [c for _, c in results[:top_k]]


# ─────────────────────────────────────────────
# ✅ LOAD INDEX
# ─────────────────────────────────────────────
combined_index, combined_chunks = load_index()

if combined_index is None:
    rebuild_index_from_db()


# ─────────────────────────────────────────────
# ✅ ROUTES
# ─────────────────────────────────────────────
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_question = data.get("question", "").strip()

        if not user_question:
            return jsonify({
                "answer": "❗ Please type a question.",
                "url": "https://avinuty.ac.in",
                "source": "none"
            })

        cache_key = user_question.lower()

        if cache_key in answer_cache:
            cached = answer_cache[cache_key]
            return jsonify(cached)

        # 🔍 DATASET SEARCH
        keyword_chunks = keyword_boost_search(user_question, combined_chunks) if combined_chunks else []
        vector_chunks = search(user_question.lower(), combined_index, combined_chunks) if combined_index is not None else []

        seen, final_chunks = set(), []
        for chunk in keyword_chunks + vector_chunks:
            if chunk not in seen:
                seen.add(chunk)
                final_chunks.append(chunk)

        context = "\n".join(final_chunks[:10])
        source = "dataset"

        # 🌐 WEBSITE SEARCH (from cached site index)
        web_text, web_url = search_website(user_question)

        if not final_chunks or len(context.strip()) < 80:
            if web_text:
                context = web_text
                source = "web"
        else:
            if web_text:
                context += "\n\n" + web_text[:500]

        # 🔴 LIVE SEARCH FALLBACK — fetch live from university site when index misses
        if len(context.strip()) < 80:
            print(f"🔴 Index miss — live searching for: {user_question}")
            live_text, live_url = live_search_university(user_question)
            if live_text:
                context = live_text
                web_url  = live_url
                source   = "web"
                print(f"✅ Live search found: {live_url}")

        if not context.strip():
            context = "No relevant information found."

        # 🤖 AI
        answer = ask_gemini(context, user_question, source)

        # 1. Try to extract a real university URL from the AI answer
        answer_url = extract_avinuty_url(answer)

        # 2. If AI answer has a real page URL, use it — it's the most accurate
        if answer_url:
            web_url = answer_url
        # 3. Otherwise use the URL from search/live-search
        elif not web_url or web_url in ["https://avinuty.ac.in", "https://www.avinuty.ac.in"]:
            web_url = f"https://avinuty.ac.in/?s={user_question.replace(' ', '+')}"

        result = {
            "answer": answer,
            "url": web_url,
            "source": source,
            "page_title": "Avinashilingam University"
        }

        answer_cache[cache_key] = result

        return jsonify(result)

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "answer": "❌ Server error",
            "url": "https://avinuty.ac.in",
            "source": "error"
        })

# ─────────────────────────────────────────────
# ✅ BROCHURES
# ─────────────────────────────────────────────
@app.route("/brochures")
def brochures():
    files = []
    for f in os.listdir(BROCHURE_FOLDER):
        if f.endswith(".pdf"):
            files.append({
                "name": f,
                "url": f"/brochure/{f}"
            })
    return jsonify(files)


@app.route("/brochure/<filename>")
def serve_brochure(filename):
    from flask import send_from_directory
    return send_from_directory(BROCHURE_FOLDER, filename)


# ─────────────────────────────────────────────
# ✅ DATASET MGMT
# ─────────────────────────────────────────────
@app.route("/datasets")
def datasets():
    rows = get_all_datasets()
    return jsonify(rows)


@app.route("/delete_dataset/<int:did>", methods=["DELETE"])
def remove_dataset(did):
    delete_dataset(did)
    rebuild_index_from_db()
    return jsonify({"success": True})


# ─────────────────────────────────────────────
# ✅ RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000/")
    app.run(debug=True, use_reloader=False)