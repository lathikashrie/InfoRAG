with open('web_scraper.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = """def is_valid_url(url):
    parsed = urlparse(url)
    return (
        parsed.netloc in ["avinuty.ac.in", "www.avinuty.ac.in"]
        and parsed.scheme in ["http", "https"]
        and not url.endswith((".jpg", ".png", ".gif", ".css", ".js", ".svg"))
    )"""

new = """SKIP_EXTENSIONS = (
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
    return True"""

if old in content:
    content = content.replace(old, new)
    with open('web_scraper.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS - file patched!")
else:
    print("FAILED - old function not found, printing current function:")
    idx = content.find("def is_valid_url")
    print(content[idx:idx+200])