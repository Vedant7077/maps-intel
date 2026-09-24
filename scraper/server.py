"""
scraper/server.py
Minimal FastAPI HTTP gateway that accepts scrape requests from n8n / backend
and launches scraper/main.py as a background subprocess.
"""
import subprocess
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Scraper Worker")


class ScrapeRequest(BaseModel):
    competitor_id: str
    project_id: str
    job_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/scrape")
def start_scrape(req: ScrapeRequest):
    cmd = [
        "python", "main.py",
        "--competitor_id", req.competitor_id,
        "--project_id", req.project_id,
    ]
    if req.job_id:
        cmd += ["--job_id", req.job_id]

    try:
        subprocess.Popen(cmd, cwd="/app")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "scraping_started", "competitor_id": req.competitor_id}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
