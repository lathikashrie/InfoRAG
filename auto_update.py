import os
import json
from web_scraper import crawl_site, load_site_index, URL_KEYWORD_MAP

OUTPUT_FILE = "uploads/auto_links_dataset.txt"

def clean_page(title, text):
    """Remove noisy or useless pages"""
    bad_words = ["privacy", "policy", "login", "error", "404"]

    t = title.lower()
    if any(b in t for b in bad_words):
        return False

    if len(text) < 100:
        return False

    return True


def match_category(url, title):
    """Match URL to correct category using keyword map"""
    url_lower = url.lower()
    title_lower = title.lower()

    for category, patterns in URL_KEYWORD_MAP.items():
        for p in patterns:
            if p in url_lower or p in title_lower:
                return category.upper()

    return "GENERAL"


def auto_update():
    print("🌐 Crawling website...")
    crawl_site(max_pages=60)

    print("📦 Loading index...")
    data = load_site_index()

    lines = []
    lines.append("AUTO LINK DATASET\n")

    seen = set()

    for url, content in data.items():
        title = content.get("title", "")
        text  = content.get("text", "")

        if not clean_page(title, text):
            continue

        category = match_category(url, title)

        # avoid duplicates
        if (category, url) in seen:
            continue
        seen.add((category, url))

        # only keep useful categories
        if category in [
            "ADMISSION", "COURSE", "FACULTY", "HOD",
            "HOSTEL", "RESEARCH", "PLACEMENT",
            "EXAM", "DEPARTMENT", "DOWNLOAD",
            "BROCHURE", "PROSPECTUS"
        ]:
            lines.append(f"{category}: {url}")

    print("💾 Saving dataset...")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("✅ Smart dataset updated:", OUTPUT_FILE)

    # auto register
    os.system("python register_db.py")


if __name__ == "__main__":
    auto_update()
    