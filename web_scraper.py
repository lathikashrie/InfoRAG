import requests
from bs4 import BeautifulSoup
import os
import json
import time
import re
from urllib.parse import urljoin, urlparse

BASE_URL = "https://avinuty.ac.in"
SITE_DB  = os.path.join(os.path.dirname(__file__), "site_index.json")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

page_store = {}

SEED_URLS = [
    BASE_URL,
    BASE_URL + "/department",
    BASE_URL + "/faculty",
    BASE_URL + "/admission",
    BASE_URL + "/courses",
    BASE_URL + "/fees",
    BASE_URL + "/hostel",
    BASE_URL + "/research",
    BASE_URL + "/placement",
    BASE_URL + "/examination",
    BASE_URL + "/swayam-mooc-courses-offered",
    BASE_URL + "/library",
    BASE_URL + "/sports",
    BASE_URL + "/events",
    BASE_URL + "/notifications",
    BASE_URL + "/downloads",
    BASE_URL + "/about",
    BASE_URL + "/contact",
    BASE_URL + "/alumni",
    BASE_URL + "/naac",
    BASE_URL + "/iqac",
    BASE_URL + "/nss",
    BASE_URL + "/ncc",
    BASE_URL + "/scholarship",
    BASE_URL + "/calendar",
]

PRIORITY_KEYWORDS = [
    "faculty", "department", "staff", "hod",
    "information-technology", "computer", "cse",
    "fee", "admission", "hostel", "course",
    "swayam", "mooc", "research", "placement",
    "exam", "result", "scholarship", "library",
]

URL_KEYWORD_MAP = {
    "admission":   ["admission", "apply", "application", "eligibility", "entrance"],
    "course":      ["course", "program", "degree", "curriculum", "syllabus", "bsc", "msc", "mba", "phd"],
    "faculty":     ["faculty", "staff", "professor", "lecturer", "teacher"],
    "hod":         ["hod", "head-of-department", "head of department"],
    "hostel":      ["hostel", "accommodation", "residence", "dormitory"],
    "research":    ["research", "publication", "journal", "project"],
    "placement":   ["placement", "career", "recruit", "campus-drive"],
    "exam":        ["exam", "examination", "result", "hall-ticket", "timetable"],
    "department":  ["department", "dept", "school-of"],
    "download":    ["download", "circular", "notification", "notice"],
    "brochure":    ["brochure"],
    "prospectus":  ["prospectus"],
    "fee":         ["fee", "fees", "payment", "tuition"],
    "swayam":      ["swayam", "mooc", "online-course"],
    "library":     ["library", "e-resources", "journal"],
    "scholarship": ["scholarship", "stipend", "financial-aid"],
}

DEPT_URL_MAP = {
    "it":                     "information-technology",
    "information technology": "information-technology",
    "cse":                    "computer-science",
    "computer science":       "computer-science",
    "mba":                    "management",
    "management":             "management",
    "physics":                "physics",
    "chemistry":              "chemistry",
    "mathematics":            "mathematics",
    "english":                "english",
    "psychology":             "psychology",
    "nutrition":              "nutrition",
    "food science":           "food-science",
    "education":              "education",
    "biotechnology":          "biotechnology",
    "commerce":               "commerce",
    "economics":              "economics",
    "home science":           "home-science",
    "textile":                "textile",
}


SKIP_EXTENSIONS = (
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".css", ".js", ".woff", ".woff2", ".ttf",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".zip", ".rar", ".mp4", ".mp3",
)

def is_valid_url(url):
    parsed = urlparse(url)
    if parsed.netloc not in ["avinuty.ac.in", "www.avinuty.ac.in"]:
        return False
    if parsed.scheme not in ["http", "https"]:
        return False
    path_lower = parsed.path.lower()
    if any(path_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
        return False
    if "/sites/" in path_lower and "/files/" in path_lower:
        return False
    if "%20" in url or "%2F" in url:
        return False
    return True


def scrape_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None, None, None
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title else url
        texts = []
        for tag in soup.find_all(["h1", "h2", "h3", "h4"]):
            t = tag.get_text(" ", strip=True)
            if t: texts.append(t)
        for tag in soup.find_all("p"):
            t = tag.get_text(" ", strip=True)
            if t: texts.append(t)
        for table in soup.find_all("table"):
            texts.append(table.get_text(" ", strip=True))
        for li in soup.find_all("li"):
            t = li.get_text(" ", strip=True)
            if t: texts.append(t)
        text = " ".join(texts)
        return title, text, soup
    except Exception as e:
        print(f"Warning {url}: {e}")
        return None, None, None


def crawl_site(max_pages=300):
    global page_store
    visited = set()
    queue   = list(SEED_URLS)
    print(f"Crawling {BASE_URL} (max {max_pages} pages)...")
    while queue and len(page_store) < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        print(f"Page {len(page_store)+1}: {url}")
        title, text, soup = scrape_page(url)
        if not title or not text or len(text) < 50:
            continue
        page_store[url] = {"title": title, "text": text, "path": urlparse(url).path.lower()}
        if soup:
            try:
                for a in soup.find_all("a", href=True):
                    full = urljoin(url, a["href"]).split("#")[0].rstrip("/")
                    if is_valid_url(full) and full not in visited:
                        if any(k in full.lower() for k in PRIORITY_KEYWORDS):
                            queue.insert(0, full)
                        else:
                            queue.append(full)
            except Exception:
                pass
        time.sleep(0.2)
    with open(SITE_DB, "w", encoding="utf-8") as f:
        json.dump(page_store, f, indent=2, ensure_ascii=False)
    print(f"DONE: {len(page_store)} pages saved")
    return page_store


def download_pdfs(max_pdfs=20):
    if not page_store:
        load_site_index()
    BROCHURE_DIR = os.path.join(os.path.dirname(__file__), "uploads", "brochures")
    os.makedirs(BROCHURE_DIR, exist_ok=True)
    downloaded = []
    seen_urls  = set()
    for page_url in list(page_store.keys()):
        if len(downloaded) >= max_pdfs:
            break
        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=8)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if not a["href"].lower().endswith(".pdf"):
                    continue
                full_url = urljoin(page_url, a["href"])
                if full_url in seen_urls:
                    continue
                seen_urls.add(full_url)
                filename = os.path.basename(urlparse(full_url).path) or "brochure.pdf"
                filepath = os.path.join(BROCHURE_DIR, filename)
                if os.path.exists(filepath):
                    downloaded.append(filepath)
                    continue
                try:
                    r = requests.get(full_url, headers=HEADERS, timeout=15)
                    if r.status_code == 200:
                        with open(filepath, "wb") as f:
                            f.write(r.content)
                        downloaded.append(filepath)
                        if len(downloaded) >= max_pdfs:
                            break
                except Exception:
                    pass
        except Exception:
            pass
    print(f"PDFs downloaded: {len(downloaded)}")
    return downloaded


def search_website(question):
    if not page_store:
        load_site_index()
    if not page_store:
        return "", BASE_URL
    q_lower = question.lower()
    q_words = [w for w in q_lower.split() if len(w) > 2]
    target_dept = None
    for keyword, path_frag in DEPT_URL_MAP.items():
        if keyword in q_lower:
            target_dept = path_frag
            break
    scored = []
    for url, data in page_store.items():
        text  = data["text"].lower()
        title = data["title"].lower()
        path  = data.get("path", "")
        score = 0
        for word in q_words:
            score += text.count(word)
            score += title.count(word) * 5
            score += path.count(word) * 8
        if target_dept and target_dept in path:
            score += 60
        if target_dept:
            for dept_path in DEPT_URL_MAP.values():
                if dept_path != target_dept and dept_path in path:
                    score -= 30
        if score > 0:
            scored.append((score, url, data["text"], data["title"]))
    scored.sort(reverse=True)
    if not scored:
        return "", BASE_URL
    best_score = scored[0][0]
    best_url   = scored[0][1] if best_score >= 10 else BASE_URL
    combined = ""
    for s, url, text, title in scored[:3]:
        combined += f"\n[Page: {title} | URL: {url}]\n{text[:1000]}\n"
    return combined[:3000], best_url


def live_search_university(question):
    try:
        q_encoded  = question.strip().replace(" ", "+")
        search_url = f"https://avinuty.ac.in/?s={q_encoded}"
        resp = requests.get(search_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return "", search_url
        soup = BeautifulSoup(resp.text, "html.parser")

        # Collect result links — real content pages only
        result_links = []
        for a in soup.find_all("a", href=True):
            href = urljoin(search_url, a["href"]).split("#")[0].rstrip("/")
            if (is_valid_url(href)
                    and href != BASE_URL
                    and href not in result_links
                    and href not in page_store
                    and "?" not in href):
                result_links.append(href)

        combined_text = ""
        best_url      = search_url

        # Also try direct URL guess (e.g. question = "swayam mooc courses" -> /swayam-mooc-courses)
        slug = re.sub(r'[^a-z0-9\s-]', '', question.lower().strip())
        slug = re.sub(r'\s+', '-', slug)
        direct_url = f"{BASE_URL}/{slug}"
        if direct_url not in result_links:
            result_links.insert(0, direct_url)

        for link in result_links[:4]:
            title, text, _ = scrape_page(link)
            if text and len(text) > 100:
                combined_text += f"\n[Page: {title} | URL: {link}]\n{text[:1500]}\n"
                if best_url == search_url:
                    best_url = link   # first working page = best URL
                time.sleep(0.3)

        # Save new pages to index
        if combined_text:
            for link in result_links[:5]:
                if link not in page_store:
                    t, tx, _ = scrape_page(link)
                    if t and tx and len(tx) > 50:
                        page_store[link] = {
                            "title": t, "text": tx,
                            "path":  urlparse(link).path.lower()
                        }
            try:
                with open(SITE_DB, "w", encoding="utf-8") as f:
                    json.dump(page_store, f, indent=2, ensure_ascii=False)
                print(f"Index updated: {len(page_store)} pages")
            except Exception:
                pass
            return combined_text[:3000], best_url

        return "", search_url

    except Exception as e:
        print(f"Live search error: {e}")
        return "", f"https://avinuty.ac.in/?s={question.replace(' ', '+')}"


def extract_avinuty_url(text):
    """Extract first real avinuty.ac.in page URL from text (not homepage)."""
    urls = re.findall(r'https?://(?:www\.)?avinuty\.ac\.in[^\s\]"\'<>]*', text)
    for url in urls:
        url = url.rstrip(".,;)")
        if len(url) > len(BASE_URL) + 3:
            return url
    return None


def scrape_university_site(question):
    text, _ = search_website(question)
    return text


def get_relevant_url(question):
    _, url = search_website(question)
    return url


def load_site_index():
    global page_store
    if os.path.exists(SITE_DB):
        with open(SITE_DB, "r", encoding="utf-8") as f:
            page_store = json.load(f)
        print(f"Loaded {len(page_store)} pages from site index")
    return page_store


if __name__ == "__main__":
    crawl_site(max_pages=300)