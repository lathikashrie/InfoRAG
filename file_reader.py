import pandas as pd
from PyPDF2 import PdfReader
import os
import json


def read_file(path):
    text = ""
    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(path)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"

    elif ext == ".csv":
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="latin-1")
        # Convert each row to "col: val | col: val" format — keeps labels with values
        for _, row in df.iterrows():
            parts = []
            for col, val in row.items():
                if pd.notna(val) and str(val).strip():
                    parts.append(f"{col}: {val}")
            if parts:
                text += " | ".join(parts) + "\n"

    elif ext == ".xlsx":
        df = pd.read_excel(path, engine="openpyxl")
        for _, row in df.iterrows():
            parts = []
            for col, val in row.items():
                if pd.notna(val) and str(val).strip():
                    parts.append(f"{col}: {val}")
            if parts:
                text += " | ".join(parts) + "\n"

    elif ext == ".xls":
        df = pd.read_excel(path, engine="xlrd")
        for _, row in df.iterrows():
            parts = []
            for col, val in row.items():
                if pd.notna(val) and str(val).strip():
                    parts.append(f"{col}: {val}")
            if parts:
                text += " | ".join(parts) + "\n"

    elif ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == ".docx":
        import docx
        doc = docx.Document(path)
        for para in doc.paragraphs:
            if para.text.strip():
                text += para.text + "\n"

    elif ext == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = _flatten_json(data)

    else:
        print(f"⚠️  Unsupported file type: {ext}")

    return text


def _flatten_json(data, prefix=""):
    """Recursively flatten JSON into readable labeled lines."""
    lines = []
    if isinstance(data, list):
        for item in data:
            lines.append(_flatten_json(item, prefix))
    elif isinstance(data, dict):
        parts = []
        for key, value in data.items():
            full_key = f"{prefix} > {key}" if prefix else key
            if isinstance(value, (dict, list)):
                lines.append(_flatten_json(value, full_key))
            else:
                parts.append(f"{key}: {value}")
        if parts:
            lines.append(" | ".join(parts))
    else:
        lines.append(f"{prefix}: {data}" if prefix else str(data))
    return "\n".join(filter(None, lines))