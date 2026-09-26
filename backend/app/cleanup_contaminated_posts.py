"""
cleanup_contaminated_posts.py
Step 2: Hard delete flagged contaminated posts and reset competitor posts_count.
"""
import re
from app.database import SessionLocal
from app.models import Post, Competitor, Project

PLACE_CARD_PATTERNS = [
    r'Open\s*[·⋅]\s*Closes',
    r'Opens soon',
    r'\d\.\d\s*\(\s*[\d,]+\s*\)',
    r'Order online',
]


def is_likely_contaminated(post_text: str, competitor_name: str) -> bool:
    if not post_text:
        return False
    for pattern in PLACE_CARD_PATTERNS:
        if re.search(pattern, post_text, re.IGNORECASE):
            return True
    if competitor_name and post_text.strip().lower().startswith((competitor_name.lower() + ' ' + competitor_name.lower())):
        return True
    return False


def cleanup():
    db = SessionLocal()
    posts = db.query(Post).all()
    deleted_count = 0
    deleted_by_comp = {}

    print("================================================================================")
    print("STEP 2: DELETING CONTAMINATED POSTS")
    print("================================================================================\n")

    for p in posts:
        comp = db.query(Competitor).filter(Competitor.id == p.competitor_id).first()
        comp_name = comp.name if comp else ""
        if is_likely_contaminated(p.post_text, comp_name):
            comp_key = f"{comp_name} ({p.competitor_id})"
            deleted_by_comp[comp_key] = deleted_by_comp.get(comp_key, 0) + 1
            print(f"Deleting Post ID: {p.id}")
            print(f"  Competitor: {comp_key}")
            print(f"  Snippet: {p.post_text.replace(chr(10), ' ')[:100]}...\n")
            db.delete(p)
            deleted_count += 1

    db.commit()

    print(f"Hard deleted {deleted_count} contaminated posts.\n")
    print("Summary of deletions by competitor:")
    for comp_key, count in deleted_by_comp.items():
        print(f"  - {comp_key}: {count} deleted")

    print("\n--------------------------------------------------------------------------------")
    print("RESETTING posts_count ON AFFECTED COMPETITORS")
    print("--------------------------------------------------------------------------------\n")

    affected_comp_ids = [
        "9ad13e98-2eac-4c50-b26e-09cdfad44251",  # Boojee Cafe QA
        "b1a2c3d4-e5f6-7890-abcd-ef1234567890",  # Boojee Cafe Seeded
        "dc9e28c2-5719-4f6e-b5a2-6ba6f0ed91ef",  # Starbucks QA
        "5b2c8e71-0d46-4a95-b673-f19c3d824ae6",  # Starbucks Seeded
    ]

    for comp_id in affected_comp_ids:
        comp = db.query(Competitor).filter(Competitor.id == comp_id).first()
        if comp:
            old_count = comp.posts_count
            real_count = db.query(Post).filter(Post.competitor_id == comp.id).count()
            comp.posts_count = real_count
            print(f"Competitor: {comp.name} ({comp.id})")
            print(f"  Project ID: {comp.project_id}")
            print(f"  Previous posts_count: {old_count} -> New posts_count: {real_count}\n")

    db.commit()
    db.close()
    print("Cleanup & posts_count reset complete.")
    print("================================================================================")


if __name__ == "__main__":
    cleanup()
