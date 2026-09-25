from app.database import SessionLocal, engine, Base
from app.models import *
from datetime import datetime, timedelta
import uuid
import hashlib

def create_hash(text):
    return hashlib.sha256(text.encode()).hexdigest()

def seed_demo():
    db = SessionLocal()

    # ── Clean up existing data (raw TRUNCATE with CASCADE is bulletproof) ───
    from sqlalchemy import text
    db.execute(text(
        "TRUNCATE TABLE scrape_jobs, generated_ideas, keywords, "
        "trend_snapshots, posts, competitors, projects RESTART IDENTITY CASCADE"
    ))
    db.commit()

    # ── Project ─────────────────────────────────────────────────────────────
    proj1 = Project(
        id="7c4f2d91-3a61-4e8b-9d25-6f7a1c3b82e4",
        name="Boojee Cafe",
        client_name="Boojee Cafe",
        client_maps_url="https://www.google.com/maps/search/?api=1&query=Boojee+Cafe+Bandra+West+Mumbai",
        created_at=datetime.fromisoformat("2026-09-25T10:33:00"),
    )
    db.add(proj1)
    db.commit()

    # ── Rival Competitors ────────────────────────────────────────────────────
    comp1 = Competitor(
        id="1e8b6f42-c957-4d13-a2e9-74b5c63891fd",
        project_id=proj1.id,
        name="Mary Lodge by Subko",
        maps_url="https://www.google.com/maps/search/?api=1&query=Mary+Lodge+by+Subko+Bandra+West+Mumbai",
        created_at=datetime.fromisoformat("2026-09-25T10:33:00"),
    )
    comp2 = Competitor(
        id="a93d17e5-6c24-4fb8-b851-2d7e4c9063aa",
        project_id=proj1.id,
        name="Tuskin Coffee",
        maps_url="https://www.google.com/maps/search/?api=1&query=Tuskin+Coffee+Bandra+West+Mumbai",
        created_at=datetime.fromisoformat("2026-09-25T10:33:00"),
    )
    comp3 = Competitor(
        id="5b2c8e71-0d46-4a95-b673-f19c3d824ae6",
        project_id=proj1.id,
        name="Starbucks Bandra West",
        maps_url="https://www.google.com/maps/search/?api=1&query=Starbucks+Bandra+West+Mumbai",
        created_at=datetime.fromisoformat("2026-09-25T10:33:00"),
    )

    # ── Client Business (is_client=True) ─────────────────────────────────────
    client_biz = Competitor(
        id="b1a2c3d4-e5f6-7890-abcd-ef1234567890",
        project_id=proj1.id,
        name="Boojee Cafe",
        maps_url="https://www.google.com/maps/search/?api=1&query=Boojee+Cafe+Bandra+West+Mumbai",
        is_client=True,
        created_at=datetime.fromisoformat("2026-09-25T10:33:00"),
    )

    db.add_all([comp1, comp2, comp3, client_biz])
    db.commit()

    # ── Helper ───────────────────────────────────────────────────────────────
    pid = proj1.id
    now = datetime.fromisoformat("2026-09-25T10:33:00")

    # ── Rival posts: Mary Lodge by Subko ────────────────────────────────────
    # Topics: New Menu Item, Weekend Special, Seasonal Offer, Happy Hour, Collaboration
    rival_posts = [
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp1.id,
            post_text="Introducing our brand-new Avocado Toast with poached eggs — the freshest addition to the Mary Lodge menu! Come try it this week.",
            content_hash=create_hash("mary-lodge-new-menu-item-avocado"),
            main_topic="New Menu Item", keywords=["avocado toast", "new menu", "brunch"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=20), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp1.id,
            post_text="Every Saturday & Sunday we're serving a special French press pour-over flight. Weekend vibes only at Mary Lodge ☕",
            content_hash=create_hash("mary-lodge-weekend-special-pourover"),
            main_topic="Weekend Special", keywords=["weekend", "pour-over", "coffee flight"],
            content_type="offer", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=15), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp1.id,
            post_text="Monsoon special: warm filter coffee + homemade banana bread combo for ₹299 only. Available till end of season!",
            content_hash=create_hash("mary-lodge-seasonal-offer-monsoon"),
            main_topic="Seasonal Offer", keywords=["monsoon", "filter coffee", "banana bread", "combo"],
            content_type="offer", cta_type="buy", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=10), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp1.id,
            post_text="Happy Hour at Mary Lodge: 5 PM – 7 PM every weekday. All specialty lattes at flat ₹199. Bring a friend!",
            content_hash=create_hash("mary-lodge-happy-hour-lattes"),
            main_topic="Happy Hour", keywords=["happy hour", "lattes", "discount", "weekday"],
            content_type="offer", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=8), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp1.id,
            post_text="We've teamed up with @BandraBookClub for a monthly pop-up reading session. Books, coffee, and community — this Sunday at Mary Lodge.",
            content_hash=create_hash("mary-lodge-collaboration-bookclub"),
            main_topic="Collaboration", keywords=["collaboration", "book club", "community", "pop-up"],
            content_type="event", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=5), scraped_at=now,
        ),
    ]

    # ── Rival posts: Tuskin Coffee ───────────────────────────────────────────
    # Topics: New Menu Item, Weekend Special, Happy Hour, Loyalty Program
    rival_posts += [
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp2.id,
            post_text="Say hello to our new Cold Brew Tonic — brewed for 18 hours, served over sparkling water. Now live at Tuskin Coffee.",
            content_hash=create_hash("tuskin-new-menu-item-cold-brew-tonic"),
            main_topic="New Menu Item", keywords=["cold brew", "tonic", "new drink"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=22), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp2.id,
            post_text="Weekend brunch drop! Fresh batch of croissants + our signature oat flat white. Tuskin Coffee open from 8 AM both days.",
            content_hash=create_hash("tuskin-weekend-special-croissant"),
            main_topic="Weekend Special", keywords=["brunch", "croissant", "flat white", "weekend"],
            content_type="offer", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=14), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp2.id,
            post_text="Afternoon slump? Come in for Happy Hour from 3–5 PM. Two Espresso Martinis for the price of one at Tuskin 🍸",
            content_hash=create_hash("tuskin-happy-hour-espresso-martini"),
            main_topic="Happy Hour", keywords=["happy hour", "espresso martini", "afternoon"],
            content_type="offer", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=7), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp2.id,
            post_text="Tuskin Rewards is live! Earn 1 point per ₹50 spent. Redeem for free drinks, pastries, and exclusive merch. Sign up in-store.",
            content_hash=create_hash("tuskin-loyalty-program-rewards"),
            main_topic="Loyalty Program", keywords=["loyalty", "rewards", "points", "members"],
            content_type="announcement", cta_type="learn", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=3), scraped_at=now,
        ),
    ]

    # ── Rival posts: Starbucks Bandra West ──────────────────────────────────
    # Topics: New Menu Item, Weekend Special, Happy Hour, Collaboration, Loyalty Program
    rival_posts += [
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp3.id,
            post_text="The Lavender Oat Latte is here for a limited time! A floral twist on your morning ritual. Available at Starbucks Bandra West.",
            content_hash=create_hash("starbucks-new-menu-item-lavender-latte"),
            main_topic="New Menu Item", keywords=["lavender latte", "seasonal drink", "oat milk"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=18), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp3.id,
            post_text="Weekend mornings deserve the best. Try our new weekend breakfast bundle — any tall drink + a sandwich for ₹499. Ends Sunday.",
            content_hash=create_hash("starbucks-weekend-special-bundle"),
            main_topic="Weekend Special", keywords=["weekend", "breakfast bundle", "deal"],
            content_type="offer", cta_type="buy", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=12), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp3.id,
            post_text="Happy Hour returns! Every weekday 4–6 PM: buy one get one on all frappuccinos. Only at Starbucks Bandra West.",
            content_hash=create_hash("starbucks-happy-hour-frappuccino"),
            main_topic="Happy Hour", keywords=["happy hour", "BOGO", "frappuccino"],
            content_type="offer", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=6), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp3.id,
            post_text="We've partnered with local artist @PriyankaCreates for a limited-edition cup design. Collect all 4 designs this month!",
            content_hash=create_hash("starbucks-collaboration-local-artist"),
            main_topic="Collaboration", keywords=["collaboration", "local artist", "limited edition", "cup design"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=9), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=comp3.id,
            post_text="Star Rewards members: earn 3x stars on all purchases this week! Download the app and start collecting. ⭐",
            content_hash=create_hash("starbucks-loyalty-program-star-rewards"),
            main_topic="Loyalty Program", keywords=["loyalty", "star rewards", "app", "bonus stars"],
            content_type="offer", cta_type="learn", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=2), scraped_at=now,
        ),
    ]

    db.add_all(rival_posts)
    db.commit()

    # ── Client posts: Boojee Cafe ────────────────────────────────────────────
    #
    # Topic overlap matrix (vs rivals above):
    #   OVERLAP  (covered, not a gap):  "New Menu Item", "Weekend Special", "Seasonal Offer"
    #   OMITTED  (gap topics):          "Happy Hour", "Collaboration", "Loyalty Program"
    #   CLIENT-ONLY (novel topic):      "Signature Drink"
    #
    client_posts = [
        # ── Overlap: New Menu Item ──
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Our new Miso Caramel Cortado is now on the menu — a savoury-sweet twist you won't find anywhere else in Bandra. Come try it!",
            content_hash=create_hash("boojee-new-menu-item-miso-cortado"),
            main_topic="New Menu Item", keywords=["miso caramel", "cortado", "new menu", "bandra"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=19), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Introducing Boojee Bites — a new snack menu with freshly baked items every morning. Croissant, cookies, and banana bread. Limited daily!",
            content_hash=create_hash("boojee-new-menu-item-bites"),
            main_topic="New Menu Item", keywords=["bites", "baked goods", "snacks", "croissant"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=11), scraped_at=now,
        ),
        # ── Overlap: Weekend Special ──
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Weekend-only: Boojee Brunch Set — any specialty coffee + avocado toast or granola bowl for ₹399. Every Sat & Sun till noon.",
            content_hash=create_hash("boojee-weekend-special-brunch-set"),
            main_topic="Weekend Special", keywords=["brunch", "weekend", "combo", "avocado toast"],
            content_type="offer", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=13), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Sunday Slow Mornings at Boojee — free newspaper, ambient music, and a complimentary cookie with every full-price drink order. See you this Sunday.",
            content_hash=create_hash("boojee-weekend-special-slow-mornings"),
            main_topic="Weekend Special", keywords=["sunday", "slow morning", "community", "complimentary"],
            content_type="event", cta_type="visit", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=6), scraped_at=now,
        ),
        # ── Overlap: Seasonal Offer ──
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Monsoon mood? Our Spiced Chai Latte is back for the season — served with a ginger cookie on the side. ₹220 only.",
            content_hash=create_hash("boojee-seasonal-offer-spiced-chai"),
            main_topic="Seasonal Offer", keywords=["monsoon", "spiced chai", "seasonal", "ginger cookie"],
            content_type="offer", cta_type="buy", has_promotion=True,
            ai_analysed=True, published_date=now - timedelta(days=9), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="It's cold brew season 🌧️ Try our Monsoon Cold Brew — smooth, dark, and refreshing. Limited batch, brewed fresh daily.",
            content_hash=create_hash("boojee-seasonal-offer-cold-brew"),
            main_topic="Seasonal Offer", keywords=["cold brew", "monsoon", "seasonal", "limited batch"],
            content_type="offer", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=4), scraped_at=now,
        ),
        # ── Client-only: Signature Drink ──
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Meet the Boojee Special — our house signature: single-origin Ethiopian pour-over with a hint of cardamom and rose water. Order it by name.",
            content_hash=create_hash("boojee-signature-drink-special"),
            main_topic="Signature Drink", keywords=["signature drink", "Ethiopian", "pour-over", "cardamom", "rose water"],
            content_type="announcement", cta_type="visit", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=16), scraped_at=now,
        ),
        Post(
            id=str(uuid.uuid4()), project_id=pid, competitor_id=client_biz.id,
            post_text="Our Signature Drink got a makeover! The Boojee Special now comes in a warm version — perfect for evenings. Tell us what you think.",
            content_hash=create_hash("boojee-signature-drink-warm-version"),
            main_topic="Signature Drink", keywords=["signature drink", "warm", "feedback", "seasonal update"],
            content_type="announcement", cta_type="learn", has_promotion=False,
            ai_analysed=True, published_date=now - timedelta(days=1), scraped_at=now,
        ),
    ]

    db.add_all(client_posts)
    db.commit()

    print("✓ Demo data seeded successfully!")
    print(f"  Rivals: {comp1.name}, {comp2.name}, {comp3.name}")
    print(f"  Client: {client_biz.name} (is_client=True, id={client_biz.id})")
    print(f"  Rival posts:  {len(rival_posts)}")
    print(f"  Client posts: {len(client_posts)}")
    print()
    print("  Topic matrix:")
    print("    Covered (client ∩ rivals): New Menu Item, Weekend Special, Seasonal Offer")
    print("    Gaps    (rivals - client):  Happy Hour, Collaboration, Loyalty Program")
    print("    Client-only (client - rivals): Signature Drink")
    db.close()

if __name__ == "__main__":
    seed_demo()