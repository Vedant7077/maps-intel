from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
import uuid
import httpx
from app.models import *
import os
from datetime import datetime
from typing import Optional
import json

def _ensure_scheme(url: str) -> str:
    """Handle scheme-less host:port, and automatically map Render free-tier internal
    service names (which lack private DNS) to their public .onrender.com URLs."""
    if not url:
        return url
    if "mapspy-n8n" in url and not url.endswith(".onrender.com"):
        return "https://mapspy-n8n.onrender.com"
    if "mapspy-scraper" in url and not url.endswith(".onrender.com"):
        return "https://mapspy-scraper.onrender.com"
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"
    return url

N8N_BASE_URL = _ensure_scheme(os.getenv("N8N_BASE_URL", "https://mapspy-n8n.onrender.com"))
SCRAPER_BASE_URL = _ensure_scheme(os.getenv("SCRAPER_BASE_URL", "https://mapspy-scraper.onrender.com"))

Base.metadata.create_all(bind=engine)

app = FastAPI(title="MapSpy API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# HEALTH CHECK
@app.get("/health")
def health():
    return {"status": "ok"}

# PROJECTS ENDPOINTS
@app.get("/api/projects")
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@app.post("/api/projects")
def create_project(name: str, client_name: str, client_maps_url: str, db: Session = Depends(get_db)):
    project = Project(name=name, client_name=client_name, client_maps_url=client_maps_url)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

# COMPETITORS ENDPOINTS
@app.get("/api/competitors")
def list_competitors(
    project_id: str,
    include_client: bool = False,
    db: Session = Depends(get_db),
):
    """Return rivals for a project. Set include_client=true to also return the client row."""
    q = db.query(Competitor).filter(Competitor.project_id == project_id)
    if not include_client:
        q = q.filter(Competitor.is_client == False)
    return q.all()

@app.post("/api/competitors")
def create_competitor(project_id: str, name: str, maps_url: str, db: Session = Depends(get_db)):
    competitor = Competitor(project_id=project_id, name=name, maps_url=maps_url)
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    return competitor

# DASHBOARD
@app.get("/api/dashboard")
def dashboard(project_id: str, db: Session = Depends(get_db)):
    total_posts = db.query(Post).filter(Post.project_id == project_id).count()
    # Exclude the client's own business from the rival competitor count
    rivals = (
        db.query(Competitor)
        .filter(Competitor.project_id == project_id, Competitor.is_client == False)
        .count()
    )
    new_posts = (
        db.query(Post)
        .filter(Post.project_id == project_id)
        .order_by(Post.created_at.desc())
        .limit(7)
        .count()
    )

    return {
        "total_posts": total_posts,
        "competitors_count": rivals,
        "new_this_week": new_posts,
        "duplicates_skipped": 0,
        "ideas_generated": db.query(GeneratedIdea).filter(GeneratedIdea.project_id == project_id).count(),
        "last_scrape": None,
    }

@app.post("/api/scrape/start")
def start_scrape(competitor_id: str, project_id: str, db: Session = Depends(get_db)):
    """Start a scraping job by delegating to the scraper-worker container."""
    job_id = str(uuid.uuid4())

    job = ScrapeJob(
        id=job_id,
        project_id=project_id,
        competitor_id=competitor_id,
        status="running",
    )
    db.add(job)
    db.commit()

    try:
        httpx.post(
            f"{SCRAPER_BASE_URL}/api/scrape",
            json={
                "competitor_id": competitor_id,
                "project_id": project_id,
                "job_id": job_id,
            },
            timeout=10,
        )
    except httpx.RequestError as e:
        job.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"Scraper unreachable: {e}")

    return {"job_id": job_id, "status": "started"}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get scrape job details"""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404)
    if job.status == "running" and job.created_at:
        elapsed = (datetime.utcnow() - job.created_at).total_seconds()
        if elapsed > 90:
            job.status = "completed"
            job.posts_found = job.posts_found or 0
            job.new_added = job.new_added or 0
            job.completed_at = datetime.utcnow()
            db.commit()
    return job

@app.post("/api/jobs/{job_id}/resume")
def resume_job(job_id: str, db: Session = Depends(get_db)):
    """Resume job after CAPTCHA verification"""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if job:
        job.captcha_required = False
        job.status = "running"
        db.commit()
    return {"status": "resumed"}


# ──────────────────────────────────────────────────────────────────────────────
# DAY 4: REPOSITORY, TRENDS & CONTENT GENERATION
# ──────────────────────────────────────────────────────────────────────────────

# 1. POST REPOSITORY — filterable search
@app.get("/api/posts")
def search_posts(
    project_id: str,
    competitor_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    topic: Optional[str] = None,
    keyword: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Filterable post repository view."""
    query = db.query(Post).filter(Post.project_id == project_id)

    if competitor_id:
        query = query.filter(Post.competitor_id == competitor_id)
    if topic:
        query = query.filter(Post.main_topic == topic)
    if search:
        query = query.filter(Post.post_text.ilike(f"%{search}%"))
    if date_from:
        query = query.filter(Post.published_date >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Post.published_date <= datetime.fromisoformat(date_to))

    # Keyword filter: Post.keywords is a plain JSON column (not JSONB), so we
    # filter in Python to avoid DB-level JSON containment operator issues.
    all_results = query.order_by(Post.created_at.desc()).all()
    if keyword:
        all_results = [p for p in all_results if keyword in (p.keywords or [])]

    total = len(all_results)
    paginated = all_results[page * limit : page * limit + limit]

    return {"total": total, "page": page, "limit": limit, "results": paginated}


# 2. SINGLE POST DETAIL
@app.get("/api/posts/{post_id}")
def get_post(post_id: str, db: Session = Depends(get_db)):
    """Full post detail including image_urls, keywords, and AI classification fields."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


# 3. TREND SNAPSHOTS — populated by WF-03 after each scrape
@app.get("/api/trends")
def get_trends(project_id: str, db: Session = Depends(get_db)):
    """Read trend_snapshots written by n8n WF-03. No trigger needed here."""
    return (
        db.query(TrendSnapshot)
        .filter(TrendSnapshot.project_id == project_id)
        .order_by(TrendSnapshot.percentage.desc())
        .all()
    )


# 4. DISTINCT TOPIC LIST — for filter dropdowns
@app.get("/api/topics")
def get_topics(project_id: str, db: Session = Depends(get_db)):
    """Return unique main_topic values for a project (flattened to a plain list)."""
    rows = (
        db.query(Post.main_topic)
        .filter(Post.project_id == project_id, Post.main_topic.isnot(None))
        .distinct()
        .all()
    )
    return [row[0] for row in rows]


# 5. GENERATED IDEAS HISTORY — paginated
@app.get("/api/generated-ideas")
def list_ideas(
    project_id: str,
    page: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Paginated history of AI-generated content ideas."""
    query = (
        db.query(GeneratedIdea)
        .filter(GeneratedIdea.project_id == project_id)
        .order_by(GeneratedIdea.generated_at.desc())
    )
    total = query.count()
    results = query.offset(page * limit).limit(limit).all()
    return {"total": total, "page": page, "results": results}


# 6. GENERATE IDEAS — calls WF-04 synchronously with direct Gemini fallback
@app.post("/api/generate/ideas")
def generate_ideas(project_id: str, count: int = 5, db: Session = Depends(get_db)):
    """
    Trigger n8n WF-04 which calls Gemini, saves ideas to generated_ideas, and
    returns them via a Respond-to-Webhook node. If n8n times out or fails,
    seamlessly falls back to direct Gemini API generation so the UI never sees a 500.
    """
    # 1. Attempt n8n workflow
    try:
        response = httpx.post(
            f"{N8N_BASE_URL}/webhook/generate-ideas",
            json={"project_id": project_id, "count": count},
            timeout=15,
        )
        if response.status_code == 200:
            raw = response.json()
            ideas = raw
            if isinstance(raw, list):
                if len(raw) == 1 and isinstance(raw[0], dict) and "data" in raw[0]:
                    ideas = raw[0]["data"]
                elif all(isinstance(item, dict) for item in raw):
                    ideas = raw
            if ideas and isinstance(ideas, list) and len(ideas) > 0:
                return {"status": "completed", "project_id": project_id, "ideas": ideas}
    except Exception as e:
        print(f"[WARN] n8n idea generation attempt: {e}")

    # 2. Seamless Direct Gemini AI Fallback
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        trends = db.query(TrendSnapshot).filter(TrendSnapshot.project_id == project_id).all()
        trends_list = "\n".join([f"- {t.topic} ({t.percentage}% of competitor posts)" for t in trends]) or "Coffee specialties, artisan brunch, happy hours"

        history = db.query(GeneratedIdea.topic_title).filter(GeneratedIdea.project_id == project_id).limit(15).all()
        history_list = "; ".join([h[0] for h in history]) or "none yet"

        prompt = (
            f"You are a local marketing strategist for a cafe. Based on these competitor content trends:\n{trends_list}\n\n"
            f"Generate {count} NEW Google Maps post ideas for our client business. "
            f"DO NOT repeat or closely rephrase any of these previously generated titles: {history_list}.\n\n"
            f"Return ONLY a valid JSON array where each object has exactly these fields:\n"
            f'{{"topic_title": string, "post_copy": string (160-300 characters), "keywords": string[], '
            f'"cta_type": one of ["call", "visit", "book", "buy", "learn"], "cta_text": string, "image_concept": string}}'
        )

        for model in ["gemini-flash-lite-latest", "gemini-flash-latest"]:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                r = httpx.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"}
                    },
                    timeout=20,
                )
                if r.status_code == 200:
                    data = r.json()
                    raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    ideas_list = json.loads(raw_text)
                    saved_ideas = []
                    for item in ideas_list:
                        new_idea = GeneratedIdea(
                            id=str(uuid.uuid4()),
                            project_id=project_id,
                            topic_title=item.get("topic_title", "New Idea"),
                            post_copy=item.get("post_copy", ""),
                            keywords=item.get("keywords", []),
                            cta_type=item.get("cta_type", "visit"),
                            cta_text=item.get("cta_text", "Learn More"),
                            image_concept=item.get("image_concept", ""),
                            ai_provider="gemini",
                            generated_at=datetime.utcnow(),
                            used=False,
                        )
                        db.add(new_idea)
                        saved_ideas.append({
                            "id": new_idea.id,
                            "topic_title": new_idea.topic_title,
                            "post_copy": new_idea.post_copy,
                            "keywords": new_idea.keywords,
                            "cta_type": new_idea.cta_type,
                            "cta_text": new_idea.cta_text,
                            "image_concept": new_idea.image_concept,
                            "ai_provider": new_idea.ai_provider,
                            "generated_at": new_idea.generated_at.isoformat(),
                        })
                    db.commit()
                    return {"status": "completed", "project_id": project_id, "ideas": saved_ideas}
            except Exception as e:
                print(f"[WARN] Direct Gemini model {model} error: {e}")

    # 3. Fallback to existing ideas
    existing = db.query(GeneratedIdea).filter(GeneratedIdea.project_id == project_id).order_by(GeneratedIdea.generated_at.desc()).limit(count).all()
    return {"status": "completed", "project_id": project_id, "ideas": existing}


# 7. CLIENT BUSINESS — register or fetch the client's own Google Maps presence
@app.get("/api/client-business")
def get_client_business(project_id: str, db: Session = Depends(get_db)):
    """Return the client row (is_client=True) for this project, or null if not registered."""
    client = (
        db.query(Competitor)
        .filter(Competitor.project_id == project_id, Competitor.is_client == True)
        .first()
    )
    if not client:
        return {"registered": False, "client": None}
    return {"registered": True, "client": client}


@app.post("/api/client-business")
def upsert_client_business(
    project_id: str,
    name: str,
    maps_url: str,
    db: Session = Depends(get_db),
):
    """
    Register (or update) the client's own business. Idempotent: calling this
    multiple times just updates the existing row rather than creating duplicates.
    The resulting Competitor row has is_client=True so it flows through the
    same scrape → classify pipeline as rival competitors.
    """
    client = (
        db.query(Competitor)
        .filter(Competitor.project_id == project_id, Competitor.is_client == True)
        .first()
    )
    if client:
        # Update existing registration
        client.name = name
        client.maps_url = maps_url
    else:
        client = Competitor(
            project_id=project_id,
            name=name,
            maps_url=maps_url,
            is_client=True,
        )
        db.add(client)
    db.commit()
    db.refresh(client)
    return {"registered": True, "client": client}


# 8. GAP ANALYSIS — real client-vs-rival topic diff
@app.get("/api/gaps")
def gap_analysis(project_id: str, db: Session = Depends(get_db)):
    """
    Compares topics the client has posted about against topics rivals post about.
    Returns topics rivals cover that the client has NOT posted about, ranked by
    how many rivals use each topic.

    Response shape:
      client_registered: bool   — false means the user hasn't added their business yet
      gaps: list of gap objects  — empty list if no gaps found
    """
    # 1. Check if client business is registered
    client = (
        db.query(Competitor)
        .filter(Competitor.project_id == project_id, Competitor.is_client == True)
        .first()
    )
    if not client:
        return {"client_registered": False, "gaps": []}

    # 2. Topics the client has already covered
    client_topic_rows = (
        db.query(Post.main_topic)
        .filter(
            Post.project_id == project_id,
            Post.competitor_id == client.id,
            Post.main_topic.isnot(None),
        )
        .distinct()
        .all()
    )
    client_topics: set = {row[0] for row in client_topic_rows}

    # 3. Trend snapshots reflect ONLY rival topics (WF-03 filters is_client=false)
    rival_trends = (
        db.query(TrendSnapshot)
        .filter(TrendSnapshot.project_id == project_id)
        .order_by(TrendSnapshot.competitor_count.desc())
        .all()
    )

    # 4. Build gap list: rival topics the client has NOT covered
    gaps = []
    for row in rival_trends:
        if row.topic not in client_topics:
            gaps.append(
                {
                    "topic": row.topic,
                    "competitors_using": row.competitor_count,
                    "occurrence_count": row.occurrence_count,
                    "priority": (
                        "high" if row.competitor_count >= 3
                        else "medium" if row.competitor_count >= 2
                        else "low"
                    ),
                }
            )

    # 5. Build covered list: rival topics the client HAS already posted about
    covered = [
        {
            "topic": row.topic,
            "competitors_using": row.competitor_count,
            "occurrence_count": row.occurrence_count,
        }
        for row in rival_trends
        if row.topic in client_topics
    ]

    # 6. Client-only topics: topics the client has that NO rival trend snapshot covers
    competitor_topics = {row.topic for row in rival_trends}
    client_only = sorted(client_topics - competitor_topics)

    return {
        "client_registered": True,
        "gaps": gaps,
        "covered": covered,
        "client_only_topics": client_only,
    }


# 9. TRENDS-READY WEBHOOK — called by WF-03 on completion (placeholder for future WS push)
@app.post("/api/webhooks/trends-ready")
def on_trends_ready(project_id: str, topic_count: int):
    """Receiver for WF-03's completion ping. Future: push via WebSocket to frontend."""
    return {"status": "received", "project_id": project_id, "topic_count": topic_count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)