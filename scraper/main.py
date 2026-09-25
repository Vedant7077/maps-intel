import sys
import os
import hashlib
import time
import random
import httpx
from datetime import datetime, timedelta
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

# backend/ is mounted read-only into this container at /app/backend,
# and PYTHONPATH (set in Dockerfile) includes it — same import your
# pyrightconfig.json already resolves for the linter.
from app.models import Post, Competitor, ScrapeJob
from app.database import SessionLocal

DATABASE_URL = os.getenv("DATABASE_URL")
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678")
CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")


def create_content_hash(post_url, post_text):
    combined = f"{post_url}_{post_text[:100]}"
    return hashlib.sha256(combined.encode()).hexdigest()


def init_driver():
    """Use the Chromium already baked into the image — no runtime download,
    no version-mismatch surprises between host and container."""
    options = uc.ChromeOptions()
    options.binary_location = CHROME_BIN
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36'
    )
    driver = uc.Chrome(options=options, version_main=None, driver_executable_path=CHROMEDRIVER_PATH)
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
    driver.get(maps_url)
    time.sleep(random.uniform(3, 5))
    accept_consent(driver)
    time.sleep(2)

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

    # 3. Scroll the active panel to lazy-load posts
    try:
        panels = driver.find_elements(By.XPATH, '//div[@role="main"] | //div[@role="feed"]')
        if panels:
            for _ in range(5):
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", panels[0])
                time.sleep(random.uniform(1.0, 1.8))
        else:
            for _ in range(5):
                driver.execute_script("window.scrollBy(0, 500)")
                time.sleep(random.uniform(1.0, 1.8))
    except Exception as e:
        print(f"[WARN] Scroll failed: {e}")

    posts = []
    db = SessionLocal()

    # 4. Extract post cards
    try:
        card_selectors = [
            "//div[@role='main']//div[contains(@class, 'cKbrCd')]",
            "//div[@role='main']//*[contains(@jsaction, 'local-post') and not(@role='button')]",
            "//div[@role='article']",
            "//div[contains(@aria-label,'Update')]",
            "//div[contains(@aria-label,'Post')]",
        ]
        post_elements = []
        for sel in card_selectors:
            found = driver.find_elements(By.XPATH, sel)
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

                content_hash = create_content_hash(post_url, post_text)
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
        existing = db.query(Post).filter(Post.content_hash == content_hash).first()
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

    db = SessionLocal()
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    competitor_name = competitor.name if competitor else None
    maps_url = competitor.maps_url if competitor else None
    db.close()

    if not competitor_name:
        print(f"[ERROR] Competitor {competitor_id} not found")
        return

    driver = init_driver()
    try:
        posts = extract_posts(driver, competitor_id, project_id, maps_url, job_id)
        print(f"[EXTRACTED] {len(posts)} posts found")

        added, skipped = save_posts(posts)
        print(f"[SAVED] {added} new, {skipped} duplicates")

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
        db.close()

        notify_n8n("scrape_done", {
            "competitor_id": competitor_id,
            "competitor_name": competitor_name,
            "project_id": project_id,
            "job_id": job_id or "unknown",
            "new_added": added,
            "duplicates_skipped": skipped,
            "images_downloaded": 0,
            "errors_count": 0,
        })

    except Exception as e:
        print(f"[ERROR] Scrape failed: {e}")
        if job_id:
            db_err = SessionLocal()
            job = db_err.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                db_err.commit()
            db_err.close()

        notify_n8n("scrape_failed", {
            "competitor_id": competitor_id,
            "job_id": job_id or "unknown",
            "error": str(e),
        })
    finally:
        driver.quit()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitor_id", required=True)
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--job_id", required=False, default=None)
    args = parser.parse_args()

    scrape_competitor(args.competitor_id, args.project_id, args.job_id)