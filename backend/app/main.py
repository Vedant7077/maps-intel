from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.database import engine, SessionLocal, Base
from subprocess import Popen
import uuid
from app.models import *
import os

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
def list_competitors(project_id: str, db: Session = Depends(get_db)):
    return db.query(Competitor).filter(Competitor.project_id == project_id).all()

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
    competitors = db.query(Competitor).filter(Competitor.project_id == project_id).count()
    new_posts = db.query(Post).filter(Post.project_id == project_id).order_by(Post.created_at.desc()).limit(7).count()
    
    return {
        "total_posts": total_posts,
        "competitors_count": competitors,
        "new_this_week": new_posts,
        "duplicates_skipped": 0,
        "ideas_generated": db.query(GeneratedIdea).filter(GeneratedIdea.project_id == project_id).count(),
        "last_scrape": None
    }

@app.post("/api/scrape/start")
def start_scrape(competitor_id: str, project_id: str, db: Session = Depends(get_db)):
    """Start a scraping job"""
    job_id = str(uuid.uuid4())
    
    job = ScrapeJob(
        id=job_id,
        project_id=project_id,
        competitor_id=competitor_id,
        status="running"
    )
    db.add(job)
    db.commit()
    
    # Start scraper in background
    env = os.environ.copy()
    env["JOB_ID"] = job_id
    
    Popen([
        "python", "-m", "scraper.main",
        "--competitor_id", competitor_id,
        "--project_id", project_id
    ], env=env)
    
    return {"job_id": job_id, "status": "started"}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get scrape job details"""
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)