import sys
import os
import json
import hashlib
import time
import random
import httpx
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import undetected_chromedriver as uc
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
sys.path.insert(0, '/app/backend')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from app.models import Post, Competitor

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/mapspy")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def create_content_hash(post_url, post_text):
    """Create SHA-256 hash for duplicate detection"""
    combined = f"{post_url}_{post_text[:100]}"
    return hashlib.sha256(combined.encode()).hexdigest()

def init_driver():
    """Initialize undetected Chrome driver"""
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = uc.Chrome(options=options, version_main=None)
    return driver

def detect_captcha(driver):
    """Detect CAPTCHA or verification screens"""
    captcha_indicators = [
        'verify', 'human', 'recaptcha', 'challenge', 'unusual activity',
        'not a robot', 'i am not a robot', 'bot check'
    ]
    
    page_text = driver.page_source.lower()
    page_title = driver.title.lower()
    
    for indicator in captcha_indicators:
        if indicator in page_text or indicator in page_title:
            return True
    
    return False

def extract_posts(driver, competitor_id, project_id, maps_url):
    """Extract Google Maps update posts from competitor profile"""
    driver.get(maps_url)
    time.sleep(random.uniform(2, 4))
    
    # Check for CAPTCHA
    if detect_captcha(driver):
        print(f"[CAPTCHA] Detected on {maps_url}")
        # Send webhook to n8n for notification
        notify_n8n("captcha", {
            "competitor_id": competitor_id,
            "maps_url": maps_url,
            "job_id": os.getenv("JOB_ID", "unknown")
        })
        return []
    
    posts = []
    
    try:
        # Scroll to load all posts
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 500)")
            time.sleep(random.uniform(1, 2))
    except:
        pass
    
    # Extract posts (this is a simplified example — real selectors vary by Google Maps)
    try:
        post_elements = driver.find_elements(By.XPATH, "//div[@data-review-id]")
        
        for elem in post_elements:
            try:
                post_text = elem.find_element(By.XPATH, ".//span[@class='reviewText']").text
                post_url = elem.find_element(By.XPATH, ".//a").get_attribute("href") or ""
                
                # Try to get date
                try:
                    date_text = elem.find_element(By.XPATH, ".//span[@class='reviewDate']").text
                    published_date = parse_date(date_text)
                except:
                    published_date = datetime.utcnow()
                
                # Check for duplicates
                content_hash = create_content_hash(post_url, post_text)
                db = Session()
                existing = db.query(Post).filter(Post.content_hash == content_hash).first()
                
                if not existing:
                    post = {
                        "competitor_id": competitor_id,
                        "project_id": project_id,
                        "post_text": post_text,
                        "post_url": post_url,
                        "published_date": published_date,
                        "content_hash": content_hash
                    }
                    posts.append(post)
                
                db.close()
            except Exception as e:
                print(f"[ERROR] Extracting post: {e}")
                continue
    
    except TimeoutException:
        print(f"[ERROR] Timeout loading posts for {competitor_id}")
    
    return posts

def save_posts(posts, job_id):
    """Save extracted posts to database"""
    db = Session()
    added = 0
    skipped = 0
    
    for post_data in posts:
        try:
            new_post = Post(
                project_id=post_data["project_id"],
                competitor_id=post_data["competitor_id"],
                post_text=post_data["post_text"],
                post_url=post_data["post_url"],
                published_date=post_data["published_date"],
                content_hash=post_data["content_hash"]
            )
            db.add(new_post)
            added += 1
        except Exception as e:
            skipped += 1
            print(f"[SKIP] {e}")
    
    db.commit()
    db.close()
    
    return added, skipped

def notify_n8n(event_type, data):
    """Send webhook to n8n"""
    n8n_url = os.getenv("N8N_BASE_URL", "http://n8n:5678")
    
    if event_type == "captcha":
        webhook = f"{n8n_url}/webhook/alert"
        payload = {"alert_type": "captcha", **data}
    elif event_type == "scrape_done":
        webhook = f"{n8n_url}/webhook/scrape-complete"
        payload = {"alert_type": "scrape_done", **data}
    
    try:
        httpx.post(webhook, json=payload, timeout=10)
        print(f"[n8n] {event_type} webhook sent")
    except Exception as e:
        print(f"[ERROR] Webhook failed: {e}")

def parse_date(date_text):
    """Parse relative date strings like '2 days ago'"""
    from datetime import timedelta
    # Simplified — you'd expand this for more formats
    if "ago" in date_text:
        days_back = int(''.join(filter(str.isdigit, date_text)) or "1")
        return datetime.utcnow() - timedelta(days=days_back)
    return datetime.utcnow()

def scrape_competitor(competitor_id, project_id):
    """Main scrape flow for one competitor"""
    print(f"\n[SCRAPE] Starting competitor {competitor_id}")
    
    db = Session()
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    db.close()
    
    if not competitor:
        print(f"[ERROR] Competitor {competitor_id} not found")
        return
    
    driver = init_driver()
    
    try:
        posts = extract_posts(driver, competitor_id, project_id, competitor.maps_url)
        print(f"[EXTRACTED] {len(posts)} posts found")
        
        added, skipped = save_posts(posts, competitor_id)
        print(f"[SAVED] {added} new, {skipped} duplicates")
        
        # Update competitor stats
        db = Session()
        competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
        competitor.last_scraped_at = datetime.utcnow()
        competitor.posts_count = db.query(Post).filter(Post.competitor_id == competitor_id).count()
        db.commit()
        db.close()
        
        # Notify n8n that scrape is done
        notify_n8n("scrape_done", {
            "competitor_id": competitor_id,
            "competitor_name": competitor.name,
            "project_id": project_id,
            "new_added": added,
            "duplicates_skipped": skipped,
            "images_downloaded": 0,
            "errors_count": 0
        })
    
    except Exception as e:
        print(f"[ERROR] Scrape failed: {e}")
        notify_n8n("scrape_failed", {"competitor_id": competitor_id, "error": str(e)})
    
    finally:
        driver.quit()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--competitor_id", required=True)
    parser.add_argument("--project_id", required=True)
    args = parser.parse_args()
    
    scrape_competitor(args.competitor_id, args.project_id)