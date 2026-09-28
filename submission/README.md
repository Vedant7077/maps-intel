# MapSpy — Google Maps Competitor Update Intelligence Tool

## Live Deployment
| Component | URL |
|---|---|
| Frontend (evaluator-facing) | https://mapspy-app.vercel.app |
| Backend API | https://mapspy-backend.onrender.com |
| n8n Workflow Engine | https://mapspy-n8n.onrender.com |

No login required — open the frontend URL directly.

## Demo Video
`[link once recorded]`

## Tech Stack
| Layer | Technology |
|---|---|
| Backend | Python 3.11 + FastAPI |
| Scraper | Selenium + standard Chromium (Debian-packaged), CDP-based stealth |
| Database | PostgreSQL 15 (SQLAlchemy + Alembic) |
| Orchestration | n8n (self-hosted on Render) |
| Frontend | React 18 + Vite + TailwindCSS |
| AI Primary | Google Gemini 1.5 Flash |
| AI Secondary (fallback) | Grok via OpenRouter (`x-ai/grok-4.3`) |
| Hosting | Render (backend, n8n, scraper, Postgres) + Vercel (frontend) |
| Dedup | SHA-256(project_id + normalized_post_url + normalized_post_text[:100]) |

See `AI_PROVIDERS.md` for evidence both providers genuinely work, not just that both are configured.

## How to Run Locally
```bash
git clone <repo>
cd maps-intel
cp .env.example .env   # fill in GEMINI_API_KEY, GROK_API_KEY, POSTGRES_PASSWORD, ALERT_EMAIL
docker-compose up -d
docker-compose exec backend alembic upgrade head
docker-compose exec backend python -m app.seed_demo
```
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- n8n: http://localhost:5678 (import the 5 workflows from `n8n-workflows/`, see `n8n-workflows/README_IMPORT_GUIDE.md`)

## What's in this submission
- `ARCHITECTURE.md` — system design, data flow, and the real bugs found and fixed during development
- `COMPLIANCE_MAP.md` — every assignment requirement mapped to where it's implemented
- `AI_PROVIDERS.md` — evidence both Gemini and Grok genuinely work, including a forced-fallback test
- `n8n-workflows/` — all 5 workflow JSONs, ready to import, plus an import guide covering credential setup
- `data/sample_posts.csv` — CSV export of scraped/seeded post data
- `data/ai_classification_example.json` — a real post before/after AI classification
- `data/generated_drafts_sample.json` — 5 real AI-generated content ideas from production

## Key Features
- Google Maps post scraping via Selenium, with graceful zero-post handling for businesses without an active Updates tab, and CAPTCHA detection with pause/resume
- Dual-AI-provider classification (Gemini primary, Grok fallback) — every post gets a topic, sub-topic, keywords, content type, and CTA classification
- Trend aggregation across competitors
- **Client-vs-competitor gap analysis** — registers the client's own business through the same scrape/classify pipeline as rivals, then diffs topics to surface real content opportunities
- AI content idea generation with duplicate-prevention (injects prior idea history into the prompt) and fact-safety constraints (no invented names, dates, or events)
- Full web interface for non-technical users — no API knowledge required to operate the tool
- Pre-populated demo dataset that does not depend on live scraping succeeding (per the assignment's own acknowledgment that live Maps scraping can be unreliable)
