from app.database import SessionLocal
from app.models import *
from datetime import datetime, timedelta
import uuid
import hashlib

def create_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def seed_demo():
    db = SessionLocal()
    
    # Create demo project 1
    proj1 = Project(name="ABC Salon Kharghar", client_name="ABC Salon", client_maps_url="https://maps.google.com/...")
    db.add(proj1)
    db.commit()
    
    # Create competitors
    comp1 = Competitor(project_id=proj1.id, name="Rival Salon 1", maps_url="https://maps.google.com/...")
    comp2 = Competitor(project_id=proj1.id, name="Rival Salon 2", maps_url="https://maps.google.com/...")
    db.add_all([comp1, comp2])
    db.commit()
    
    # Create 20 demo posts per competitor
    topics = ["Hair Care Tips", "Festival Offer", "Before/After", "New Service", "Customer Review"]
    for comp in [comp1, comp2]:
        for i in range(20):
            post_text = f"Amazing {topics[i % len(topics)]} #{i+1}. Visit us today!"
            post = Post(
                project_id=proj1.id,
                competitor_id=comp.id,
                post_text=post_text,
                post_url=f"https://maps.google.com/post-{uuid.uuid4()}",
                published_date=datetime.utcnow() - timedelta(days=i),
                content_hash=create_hash(f"{comp.id}_{post_text}"),
                main_topic=topics[i % len(topics)],
                keywords=["salon", "haircare", "kharghar"],
                content_type="offer" if i % 3 == 0 else "tips",
                cta_type="visit" if i % 2 == 0 else "call",
                ai_analysed=True
            )
            db.add(post)
    
    db.commit()
    print("✓ Demo data seeded successfully")
    db.close()

if __name__ == "__main__":
    seed_demo()