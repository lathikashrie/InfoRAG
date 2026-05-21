from groq import Groq

client = Groq(api_key="YOUR_GROQ_API_KEY")

def ask_gemini(context, question, source="dataset"):
    source_note = ""
    if source == "web":
        source_note = "This answer is based on the official university website."
    elif source == "dataset":
        source_note = "This answer is from the university's internal dataset."

    prompt = f"""You are Saradha, the official AI assistant for Avinashilingam University.

You help students, parents, and visitors with information about:
- Fee structure (tuition, exam, hostel, semester, one-time fees)
- Departments and HODs (Head of Department)
- Faculty and staff details
- Courses, programs, and specialisations (UG, PG, PhD)
- Admission process and eligibility
- Campus facilities, hostel, library, sports
- Academic calendar, events, and notices
- Brochures and downloadable resources

STRICT RULES:
1. ONLY use facts explicitly stated in the Context below — never guess or invent details.
2. If the context contains exact fee amounts, HOD names, or faculty names, quote them EXACTLY as written — do not paraphrase names.
3. Search the ENTIRE context carefully before saying information is unavailable — it may appear in a table row, list item, or labelled field.
4. If the context truly does NOT contain the answer, say: "I don't have that specific information right now. Please visit https://avinuty.ac.in or contact the department directly."
5. Never say a fact is true if you cannot find it in the Context.
6. Format lists with line breaks for readability.
7. Keep answers concise but complete.
8. {source_note}

Context:
\"\"\"
{context}
\"\"\"

Question: {question}

Answer:"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=600
        )
        return response.choices[0].message.content

    except Exception as e:
        error = str(e)
        if "429" in error or "rate_limit" in error.lower():
            return "⚠️ Too many requests. Please wait a moment and try again."
        return f"⚠️ AI error: {error}"