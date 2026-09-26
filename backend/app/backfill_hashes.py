"""
One-time backfill: recomputes content_hash for every existing post using
the SAME normalized, project-scoped formula now used in scraper/main.py.

Run once: docker-compose exec backend python -m app.backfill_hashes
"""
import hashlib
import re
from urllib.parse import urlparse
from app.database import SessionLocal
from app.models import Post


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


def backfill():
    db = SessionLocal()
    posts = db.query(Post).order_by(Post.created_at.asc()).all()
    updated = 0
    deleted = 0
    seen_hashes = {}

    for p in posts:
        new_hash = create_content_hash(p.post_url or "", p.post_text, p.project_id)
        if new_hash in seen_hashes:
            db.delete(p)
            deleted += 1
            continue
        seen_hashes[new_hash] = p.id
        if p.content_hash != new_hash:
            p.content_hash = new_hash
            updated += 1

    db.commit()
    if deleted > 0:
        print(f"Removed {deleted} duplicate posts created due to unnormalized hashing")
    print(f"Backfilled {updated} of {len(posts)} posts to project-scoped hashes")
    db.close()


if __name__ == "__main__":
    backfill()
