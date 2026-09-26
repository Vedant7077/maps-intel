"""
find_contaminated_posts.py
Dry-run script to identify contaminated post data from scraper fallback matching place cards.
"""
import re
from app.database import SessionLocal
from app.models import Post, Competitor, Project

PLACE_CARD_PATTERNS = [
    r'Open\s*[·⋅]\s*Closes',
    r'Opens soon',
    r'\d\.\d\s*\(\s*[\d,]+\s*\)',      # rating like "4.4 (4,723)"
    r'Order online',
]


def is_likely_contaminated(post_text: str, competitor_name: str) -> bool:
    if not post_text:
        return False
    for pattern in PLACE_CARD_PATTERNS:
        if re.search(pattern, post_text, re.IGNORECASE):
            return True
    # Repeated business name at the start (e.g. "Boojee Cafe Boojee Cafe 4.4...")
    if competitor_name and post_text.strip().lower().startswith((competitor_name.lower() + ' ' + competitor_name.lower())):
        return True
    return False


def run_dry_run():
    db = SessionLocal()
    competitors = db.query(Competitor).order_by(Competitor.project_id, Competitor.name).all()

    total_all_posts = 0
    total_flagged_posts = 0

    print("================================================================================")
    print("CONTAMINATED POSTS DRY-RUN REPORT (IDENTIFY ONLY - NO DELETIONS)")
    print("================================================================================\n")

    for c in competitors:
        project = db.query(Project).filter(Project.id == c.project_id).first()
        proj_name = project.name if project else "Unknown Project"
        posts = db.query(Post).filter(Post.competitor_id == c.id).order_by(Post.created_at.asc()).all()

        flagged = []
        clean = []

        for p in posts:
            if is_likely_contaminated(p.post_text, c.name):
                flagged.append(p)
            else:
                clean.append(p)

        total_all_posts += len(posts)
        total_flagged_posts += len(flagged)

        print(f"Competitor: {c.name} ({c.id})")
        print(f"  Project: {proj_name} ({c.project_id})")
        print(f"  Total posts in DB: {len(posts)}")
        print(f"  Flagged as contaminated: {len(flagged)}")
        print(f"  Clean posts: {len(clean)}")

        if flagged:
            print("  Flagged post IDs & sample text:")
            for p in flagged:
                sample = p.post_text.replace('\n', ' ')[:140]
                print(f"    - ID: {p.id}")
                print(f"      Text: \"{sample}...\"")
                print(f"      URL: {p.post_url or '(no URL)'}")
        else:
            print("  Status: Clean (0 contaminated)")
        print()

    print("--------------------------------------------------------------------------------")
    print(f"SUMMARY: {total_flagged_posts} of {total_all_posts} posts flagged across {len(competitors)} competitors.")
    print("================================================================================")
    db.close()


if __name__ == "__main__":
    run_dry_run()
