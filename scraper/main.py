"""
scraper/main.py
Standalone scraper that is launched by server.py as a subprocess.
Imports models from the backend via PYTHONPATH=/app:/app/backend (set in Dockerfile).
"""
import argparse
import hashlib
import os
import random
import time
from datetime import datetime

import httpx
import undetected_chromedriver as uc
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

# ── DB imports resolved via PYTHONPATH=/app/backend ─────────────────────────
from app.models import Post, Competitor, ScrapeJob
from app.database import SessionLocal

# ── Module-level config ──────────────────────────────────────────────────────
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://n8n:5678")
DATABASE_URL = os.getenv("DATABASE_URL")

# ── Helpers ──────────────────────────────────────────────────────────────────

def create_content_hash(post_url: str, post_text: str) -> str:
    """SHA-256 hash for duplicate detection."""
    combined = f"{post_url}_{post_text[:100]}"
    return hashlib.sha256(combined.encode()).hexdigest()


def init_driver():
    """Initialize undetected Chrome driver using the distro-packaged Chromium."""
    CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium")
    CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    options = uc.ChromeOptions()
    options.binary_location = CHROME_BIN
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    driver = uc.Chrome(
        options=options,
        version_main=None,
        driver_executable_path=CHROMEDRIVER_PATH,
    )
    return driver


def detect_captcha(driver) -> bool:
    """Return True if the page looks like a CAPTCHA / bot-check wall."""
    captcha_indicators = [
        "verify",
        "unusual traffic",
        "recaptcha",
        "challenge",
        "unusual activity",
        "not a robot",
        "i am not a robot",
        "bot check",
    ]
    page_text = driver.page_source.lower()
    page_title = driver.title.lower()
    return any(ind in page_text or ind in page_title for ind in captcha_indicators)


def notify_n8n(event_type: str, data: dict):
    """Fire-and-forget webhook to n8n."""
    if event_type == "captcha":
        webhook = f"{N8N_BASE_URL}/webhook/alert"
        payload = {"alert_type": "captcha", **data}
    elif event_type == "scrape_done":
        webhook = f"{N8N_BASE_URL}/webhook/scrape-complete"
        payload = {"alert_type": "scrape_done", **data}
    elif event_type == "scrape_failed":
        webhook = f"{N8N_BASE_URL}/webhook/alert"
        payload = {"alert_type": "scrape_failed", **data}
    else:
        return

    try:
        print(f"Sending webhook to {webhook} ...")
        httpx.post(webhook, json=payload, timeout=10)
        print(f"[n8n] {event_type} webhook sent")
    except Exception as e:
        print(f"[ERROR] Webhook failed ({webhook}): {e}")


def parse_date(date_text: str) -> datetime:
    """Parse relative date strings like '2 days ago'."""
    from datetime import timedelta
    if "ago" in date_text:
        days_back = int("".join(filter(str.isdigit, date_text)) or "1")
        return datetime.utcnow() - timedelta(days=days_back)
    return datetime.utcnow()


def extract_posts(driver, competitor_id: str, project_id: str, maps_url: str, job_id: str | None) -> list:
    """Extract Google Maps update posts from a competitor profile."""
    driver.get(maps_url)
    time.sleep(random.uniform(2, 4))

    if detect_captcha(driver):
        print(f"[CAPTCHA] Detected on {maps_url}")
        notify_n8n("captcha", {
            "competitor_id": competitor_id,
            "maps_url": maps_url,
            "job_id": job_id,
        })
        return []

    posts = []

    # Scroll to lazy-load content
    try:
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(random.uniform(1, 2))
    except Exception:
        pass

    try:
        post_elements = driver.find_elements(By.XPATH, "//div[@data-review-id]")
        db = SessionLocal()
        try:
            for elem in post_elements:
                try:
                    post_text = elem.find_element(By.XPATH, ".//span[@class='reviewText']").text
                    post_url = elem.find_element(By.XPATH, ".//a").get_attribute("href") or ""

                    try:
                        date_text = elem.find_element(By.XPATH, ".//span[@class='reviewDate']").text
                        published_date = parse_date(date_text)
                    except Exception:
                        published_date = datetime.utcnow()

                    content_hash = create_content_hash(post_url, post_text)
                    existing = db.query(Post).filter(Post.content_hash == content_hash).first()

                    if not existing:
                        posts.append({
                            "competitor_id": competitor_id,
                            "project_id": project_id,
                            "post_text": post_text,
                            "post_url": post_url,
                            "published_date": published_date,
                            "content_hash": content_hash,
                        })
                except Exception as e:
                    print(f"[ERROR] Extracting post: {e}")
        finally:
            db.close()

    except TimeoutException:
        print(f"[ERROR] Timeout loading posts for {competitor_id}")

    return posts


def save_posts(posts: list, job_id: str | None) -> tuple[int, int]:
    """Persist extracted posts; return (added, skipped)."""
    db = SessionLocal()
    added, skipped = 0, 0
    try:
        for post_data in posts:
            try:
                new_post = Post(
                    project_id=post_data["project_id"],
                    competitor_id=post_data["competitor_id"],
                    post_text=post_data["post_text"],
                    post_url=post_data["post_url"],
                    published_date=post_data["published_date"],
                    content_hash=post_data["content_hash"],
                )
                db.add(new_post)
                added += 1
            except Exception as e:
                skipped += 1
                print(f"[SKIP] {e}")
        db.commit()
    finally:
        db.close()
    return added, skipped


def scrape_competitor(competitor_id: str, project_id: str, job_id: str | None):
    """Main scrape flow for one competitor."""
    print(f"\n[SCRAPE] Starting competitor {competitor_id}")

    db = SessionLocal()
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()

    if not competitor:
        print(f"[ERROR] Competitor {competitor_id} not found")
        db.close()
        return
        
    competitor_name = competitor.name
    maps_url = competitor.maps_url
    db.close()

    driver = init_driver()
    try:
        posts = extract_posts(driver, competitor_id, project_id, maps_url, job_id)
        print(f"[EXTRACTED] {len(posts)} posts found")

        added, skipped = save_posts(posts, job_id)
        print(f"[SAVED] {added} new, {skipped} duplicates")

        # Update competitor stats
        db = SessionLocal()
        try:
            competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
            if competitor:
                competitor.last_scraped_at = datetime.utcnow()
                competitor.posts_count = db.query(Post).filter(
                    Post.competitor_id == competitor_id
                ).count()
                db.commit()
        finally:
            db.close()

        notify_n8n("scrape_done", {
            "competitor_id": competitor_id,
            "competitor_name": competitor_name,
            "project_id": project_id,
            "job_id": job_id,
            "new_added": added,
            "duplicates_skipped": skipped,
            "images_downloaded": 0,
            "errors_count": 0,
        })

    except Exception as e:
        print(f"[ERROR] Scrape failed: {e}")
        notify_n8n("scrape_failed", {
            "competitor_id": competitor_id,
            "job_id": job_id,
            "error": str(e),
        })

    finally:
        driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitor_id", required=True)
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--job_id", default=None)
    args = parser.parse_args()

    scrape_competitor(args.competitor_id, args.project_id, args.job_id)