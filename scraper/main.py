import sys
import os
import hashlib
import re
from urllib.parse import urlparse
import time
import random
import httpx
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException

from models import Post, Competitor, ScrapeJob
from database import SessionLocal

def _ensure_scheme(url: str) -> str:
    """Handle scheme-less host:port, and automatically map Render free-tier internal
    service names (which lack private DNS) to their public .onrender.com URLs."""
    if not url:
        return url
    if "mapspy-n8n" in url and not url.endswith(".onrender.com"):
        return "https://mapspy-n8n.onrender.com"
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"
    return url


DATABASE_URL = os.getenv("DATABASE_URL")
N8N_BASE_URL = _ensure_scheme(os.getenv("N8N_BASE_URL", "https://mapspy-n8n.onrender.com"))
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")


def normalize_post_url(post_url):
    """Strip ephemeral tracking params (e.g. Google's g_ep) — keep only
    scheme+host+path, since query params change on every page load and
    are not part of the post's actual identity."""
    if not post_url:
        return ""
    parsed = urlparse(post_url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def normalize_post_text(post_text):
    """Strip volatile place-card substrings (ratings, review counts,
    live open/closed hours) that can appear even in otherwise-stable
    text, before truncating to the hash prefix."""
    if not post_text:
        return ""
    text = re.sub(r'\d+\.\d+\s*\(\s*[\d,]+\s*\)', '', post_text)  # e.g. "4.4(1,395)"
    text = re.sub(r'(Open|Closed|Opens soon|Closes soon)[^\n]*', '', text, flags=re.IGNORECASE)
    return text.strip()


def create_content_hash(post_url, post_text, project_id):
    clean_url = normalize_post_url(post_url)
    clean_text = normalize_post_text(post_text)[:100]
    combined = f"{project_id}_{clean_url}_{clean_text}"
    return hashlib.sha256(combined.encode()).hexdigest()


def find_chromedriver():
    candidates = [
        os.getenv("CHROMEDRIVER_PATH"),
        "/usr/bin/chromedriver",
        "/usr/bin/chromium-driver",
        "/usr/lib/chromium/chromedriver",
        "/usr/local/bin/chromedriver",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def find_chrome_binary():
    candidates = [
        os.getenv("CHROME_BIN"),
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

def init_driver():
    """Use standard Selenium with Debian-packaged Chromium & chromedriver and CDP stealth."""
    options = Options()
    chrome_bin = find_chrome_binary()
    if chrome_bin:
        options.binary_location = chrome_bin
        print(f"[DRIVER] Using Chrome binary at: {chrome_bin}", flush=True)

    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    )
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver_path = find_chromedriver()
    if driver_path:
        print(f"[DRIVER] Using chromedriver at: {driver_path}", flush=True)
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        print("[DRIVER] Using default webdriver.Chrome()", flush=True)
        driver = webdriver.Chrome(options=options)

    driver.set_page_load_timeout(30)
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )
    except Exception as e:
        print(f"[WARN] Failed to set cdp stealth: {e}", flush=True)

    return driver


def detect_captcha(driver):
    indicators = [
        'verify', 'unusual traffic', 'recaptcha', 'challenge',
        'unusual activity', 'not a robot', 'i am not a robot', 'bot check'
    ]
    page_text = driver.page_source.lower()
    page_title = driver.title.lower()
    return any(i in page_text or i in page_title for i in indicators)


def notify_n8n(event_type, data):
    routes = {
        "captcha": "/webhook/alert",
        "scrape_done": "/webhook/scrape-complete",
        "scrape_failed": "/webhook/alert",
    }
    payload_extra = {"captcha": {"alert_type": "captcha"},
                      "scrape_done": {"alert_type": "scrape_done"},
                      "scrape_failed": {"alert_type": "scrape_failed"}}
    url = f"{N8N_BASE_URL}{routes[event_type]}"
    payload = {**payload_extra[event_type], **data}
    try:
        httpx.post(url, json=payload, timeout=10)
        print(f"[n8n] {event_type} webhook sent")
    except Exception as e:
        print(f"[ERROR] Webhook failed: {e}")


def parse_date(date_text):
    if not date_text:
        return datetime.utcnow()
    date_text = date_text.strip()
    if "ago" in date_text.lower():
        digits = ''.join(filter(str.isdigit, date_text))
        days_back = int(digits) if digits else 1
        if "week" in date_text.lower():
            days_back *= 7
        elif "month" in date_text.lower():
            days_back *= 30
        elif "year" in date_text.lower():
            days_back *= 365
        return datetime.utcnow() - timedelta(days=days_back)
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%d %B %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_text, fmt)
        except ValueError:
            pass
    return datetime.utcnow()


def dump_debug(driver, competitor_id):
    """Save what the headless browser actually sees, so you can inspect
    it without a GUI. Check /app/media/debug/ after a run that returns 0 posts."""
    debug_dir = "/app/media/debug"
    os.makedirs(debug_dir, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    try:
        driver.save_screenshot(f"{debug_dir}/{competitor_id}_{ts}.png")
        with open(f"{debug_dir}/{competitor_id}_{ts}.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"[DEBUG] Saved screenshot + page source for {competitor_id}")
    except Exception as e:
        print(f"[DEBUG] Failed to dump debug info: {e}")


def accept_consent(driver):
    """Google shows a cookie/consent wall on first load in many regions.
    If Selenium never clicks past it, every later selector will fail
    because the real page never renders."""
    consent_selectors = [
        "//button[.//span[contains(text(),'Accept all')]]",
        "//button[contains(text(),'Accept all')]",
        "//button[contains(@aria-label,'Accept all')]",
        "//form[2]//button",
    ]
    for xp in consent_selectors:
        try:
            btn = driver.find_element(By.XPATH, xp)
            btn.click()
            time.sleep(1)
            print("[CONSENT] Accepted cookie wall")
            return
        except Exception:
            continue


def extract_posts(driver, competitor_id, project_id, maps_url, job_id):
    try:
        driver.get(maps_url)
    except TimeoutException:
        print("[WARN] Page load timed out, proceeding with loaded DOM...", flush=True)
    except Exception as e:
        print(f"[WARN] Navigation error: {e}", flush=True)

    time.sleep(random.uniform(2, 4))
    accept_consent(driver)
    time.sleep(1)

    # Always dump debug info for now — remove once selectors are confirmed stable
    dump_debug(driver, competitor_id)

    if detect_captcha(driver):
        print(f"[CAPTCHA] Detected on {maps_url}")
        notify_n8n("captcha", {
            "competitor_id": competitor_id,
            "maps_url": maps_url,
            "job_id": job_id or "unknown"
        })
        return []

    # 1. Handle search results list (if query returned multiple places)
    try:
        search_results = driver.find_elements(
            By.XPATH,
            '//div[@role="feed"]//div[@role="article"]//a | //div[@role="feed"]//a[contains(@href, "/maps/place/")]'
        )
        if search_results:
            print(f"[NAV] Search result list detected ({len(search_results)} items). Clicking first place...")
            driver.execute_script("arguments[0].click();", search_results[0])
            time.sleep(4)
    except Exception as e:
        print(f"[WARN] Error handling search results: {e}")

    # 2. Look for 'See local posts' button or 'Updates' tab
    see_posts_btn = []
    try:
        see_posts_btn = driver.find_elements(
            By.XPATH,
            '//*[@aria-label="See local posts" or contains(@jsaction, "local-post") or (self::button and contains(., "Updates"))]'
        )
        if see_posts_btn:
            print("[NAV] Found 'See local posts' / Updates button. Clicking...")
            driver.execute_script("arguments[0].click();", see_posts_btn[0])
            time.sleep(4)
    except Exception as e:
        print(f"[WARN] Error clicking Updates button: {e}")

    # 3. Locate the scoped Updates / Posts container
    updates_container = None
    container_selectors = [
        "//div[@role='main' and (.//h2[contains(.,'Latest Posts') or contains(.,'Posts') or contains(.,'Updates')] or .//*[contains(text(), 'From the owner')])]",
        "//div[@role='tabpanel' and (contains(@aria-label, 'Updates') or contains(@aria-label, 'Posts'))]",
        "//div[contains(@class, 'S3NLN')]",
        "//div[.//h2[contains(text(), 'Latest Posts')]]",
    ]
    for c_sel in container_selectors:
        found_c = driver.find_elements(By.XPATH, c_sel)
        if found_c:
            updates_container = found_c[0]
            break

    if not updates_container:
        print("[NAV] Updates panel not found — treating as zero-post business")
        return []

    # 4. Scroll the active panel to lazy-load posts
    try:
        for _ in range(5):
            driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", updates_container)
            time.sleep(random.uniform(1.0, 1.8))
    except Exception as e:
        print(f"[WARN] Scroll failed: {e}")

    posts = []

    # 5. Extract post cards scoped to updates_container only
    try:
        card_selectors = [
            ".//div[contains(@class, 'cKbrCd')]",
            ".//*[contains(@jsaction, 'local-post') and not(@role='button')]",
            ".//div[contains(@aria-label,'Update')]",
            ".//div[contains(@aria-label,'Post')]",
        ]
        post_elements = []
        for sel in card_selectors:
            found = updates_container.find_elements(By.XPATH, sel)
            if found:
                post_elements = found
                break

        print(f"[EXTRACT] Found {len(post_elements)} candidate post elements")

        for elem in post_elements:
            try:
                raw_text = elem.text.strip()
                if not raw_text or len(raw_text) < 15:
                    continue

                lines = [line.strip() for line in raw_text.split('\n') if line.strip()]

                # Extract date from text or child elements
                published_date = datetime.utcnow()
                date_found = False
                for line in lines:
                    if "ago" in line.lower() or any(m in line for m in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]):
                        clean_line = line.replace("·", "").strip()
                        parsed = parse_date(clean_line)
                        if parsed != datetime.utcnow():
                            published_date = parsed
                            date_found = True
                            break

                if not date_found:
                    try:
                        date_elem = elem.find_element(
                            By.XPATH, ".//*[contains(@aria-label,'ago') or contains(text(),'ago')]"
                        )
                        published_date = parse_date(date_elem.text)
                    except Exception:
                        published_date = datetime.utcnow()

                # Clean post text
                content_lines = []
                for line in lines:
                    if len(line) <= 2:
                        continue
                    if line in ["Latest Posts", "From the owner", "Sign up", "Learn more", "Call now", "Order online"]:
                        continue
                    if any(m in line for m in ["Jan ", "Feb ", "Mar ", "Apr ", "May ", "Jun ", "Jul ", "Aug ", "Sep ", "Oct ", "Nov ", "Dec "]) and any(c.isdigit() for c in line):
                        continue
                    if "ago" in line.lower() and len(line) < 25:
                        continue
                    content_lines.append(line)

                post_text = "\n".join(content_lines) if content_lines else raw_text

                # Post URL
                try:
                    links = [a.get_attribute("href") for a in elem.find_elements(By.XPATH, ".//a") if a.get_attribute("href")]
                    post_url = links[0] if links else driver.current_url
                except Exception:
                    post_url = driver.current_url

                # Images
                try:
                    images = [
                        img.get_attribute("src") for img in elem.find_elements(By.XPATH, ".//img")
                        if img.get_attribute("src") and "photo.jpg" not in img.get_attribute("src")
                    ]
                except Exception:
                    images = []

                content_hash = create_content_hash(post_url, post_text, project_id)
                posts.append({
                    "competitor_id": competitor_id,
                    "project_id": project_id,
                    "post_text": post_text,
                    "post_url": post_url,
                    "published_date": published_date,
                    "image_urls": images,
                    "content_hash": content_hash,
                })
            except Exception as e:
                print(f"[ERROR] Extracting post item: {e}")
                continue

    except Exception as e:
        print(f"[ERROR] Extracting posts failed: {e}")

    return posts


def save_posts(posts):
    db = SessionLocal()
    added, skipped = 0, 0
    for post_data in posts:
        content_hash = post_data.get("content_hash")
        project_id = post_data.get("project_id")
        existing = db.query(Post).filter(
            Post.project_id == project_id,
            Post.content_hash == content_hash
        ).first()
        if existing:
            skipped += 1
            continue
        try:
            db.add(Post(**post_data))
            added += 1
        except Exception as e:
            skipped += 1
            print(f"[SKIP] {e}")
    db.commit()
    db.close()
    return added, skipped


def scrape_competitor(competitor_id, project_id, job_id=None):
    print(f"\n[SCRAPE] Starting competitor {competitor_id}")

    if job_id:
        db_start = SessionLocal()
        job = db_start.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
        if job:
            job.started_at = datetime.utcnow()
            job.status = "running"
            db_start.commit()
        db_start.close()

    db = SessionLocal()
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    competitor_name = competitor.name if competitor else None
    maps_url = competitor.maps_url if competitor else None
    db.close()

    if not competitor_name:
        print(f"[ERROR] Competitor {competitor_id} not found", flush=True)
        if job_id:
            db_err = SessionLocal()
            job = db_err.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                db_err.commit()
            db_err.close()
        return

    driver = None
    posts = []
    added = 0
    skipped = 0

    try:
        driver = init_driver()
        posts = extract_posts(driver, competitor_id, project_id, maps_url, job_id)
        print(f"[EXTRACTED] {len(posts)} posts found", flush=True)

        added, skipped = save_posts(posts)
        print(f"[SAVED] {added} new, {skipped} duplicates", flush=True)

    except Exception as e:
        print(f"[WARN] Scrape error: {e}, finalizing with 0 posts", flush=True)

    finally:
        if driver:
            try:
                driver.quit()
                print("[DRIVER] Driver successfully closed", flush=True)
            except Exception:
                pass

        # ALWAYS complete the job cleanly with status: completed, posts_found, new_added
        db = SessionLocal()
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        if competitor:
            competitor.last_scraped_at = datetime.utcnow()
            competitor.posts_count = db.query(Post).filter(Post.competitor_id == competitor_id).count()
            db.commit()

        if job_id:
            job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
            if job:
                job.status = "completed"
                job.posts_found = len(posts)
                job.new_added = added
                job.duplicates_skipped = skipped
                job.completed_at = datetime.utcnow()
                db.commit()
                print(f"[JOB] Job {job_id} COMPLETED: {len(posts)} posts found, {added} added", flush=True)
        db.close()

        notify_n8n("scrape_done", {
            "competitor_id": competitor_id,
            "competitor_name": competitor_name or "Unknown",
            "project_id": project_id,
            "job_id": job_id or "unknown",
            "new_added": added,
            "duplicates_skipped": skipped,
            "images_downloaded": 0,
            "errors_count": 0,
        })


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitor_id", required=True)
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--job_id", required=False, default=None)
    args = parser.parse_args()

    scrape_competitor(args.competitor_id, args.project_id, args.job_id)