# Architecture

## System Overview

```
Browser (evaluator)
   │
   ▼
Frontend (Vercel)
   │  HTTPS
   ▼
Backend API (Render, FastAPI)
   │                              │
   │ webhook triggers             │ reads/writes
   ▼                              ▼
n8n (Render)                  PostgreSQL (Render)
   │  webhook: scrape-start        ▲
   ▼                               │
Scraper Worker (Render)  ──────────┘
   │  Selenium + Chromium
   ▼
Google Maps
```

- **Backend** never talks to Chromium directly — it delegates scraping to a separate `scraper-worker` service over HTTP, so the backend image stays small (~200MB) and only the scraper carries the Chromium dependency (~600MB+).
- **n8n owns all orchestration** after a scrape completes: AI classification (with automatic Gemini→Grok fallback), trend aggregation, and content idea generation. This replaced what would otherwise be hand-written Celery task chains, retry wrappers, and notification code.
- **The scraper is fully self-contained** — it carries its own copies of the SQLAlchemy models and DB session code rather than depending on a shared folder mount, so the exact same Docker image works identically in local `docker-compose` and on Render (a live bind-mount like `docker-compose` uses has no equivalent in most cloud container platforms).

## Data Flow: Scrape → Classify → Aggregate → Generate

1. User clicks "Scrape Now" → `POST /api/scrape/start` → backend creates a `ScrapeJob` row, delegates to `scraper-worker` via HTTP.
2. Scraper navigates to the business's Google Maps profile, looks specifically for the Updates/"local posts" panel (not just any `role="article"` element on the page — see the contamination bug below for why this distinction matters), extracts posts, deduplicates by a project-scoped content hash, saves to Postgres.
3. Scraper calls n8n's `/webhook/scrape-complete`, which triggers **WF-02** (AI classification: Gemini primary, Grok fallback on failure).
4. WF-02 completing triggers **WF-03** (trend aggregation — explicitly excludes the client's own business so rival trend data stays uncontaminated by the client's own posts).
5. User can trigger **WF-04** (content idea generation) any time via `POST /api/generate/ideas` — it reads current trends plus prior idea history (to avoid repeats) and generates fact-grounded post drafts.
6. **WF-05** handles CAPTCHA/failure/completion email alerts.

## Gap Analysis Design

The client's own business is stored as a normal row in the `competitors` table, flagged `is_client=true`, and flows through the *exact same* scrape → classify pipeline as rivals — no parallel data model. `GET /api/gaps` then does a simple set diff: topics rivals cover that the client doesn't (`gaps`), topics both cover (`covered`), and topics only the client covers (`client_only_topics`, framed as a differentiator rather than a warning).

## Real Bugs Found and Fixed During Development

Documenting these because catching and fixing them is part of the engineering story, not something to hide:

1. **Cross-project content-hash collision.** `content_hash` was originally `SHA256(post_url + post_text[:100])` with a database-wide unique constraint. Two different projects scraping the same real business collided on that hash, silently dropping all posts in the second project as "duplicates." Fixed by scoping the hash to `project_id`, with a one-time backfill script for previously-scraped data.
2. **Hash instability from volatile source content.** Even after project-scoping, hashes changed between scrapes of the same business because Google Maps URLs carry an ephemeral tracking parameter (`g_ep`) that changes per session, and place-card text includes live data (star ratings, "Open ⋅ Closes 11pm") that changes hour to hour. Fixed by normalizing the URL (strip query params) and text (strip rating/hours patterns) before hashing.
3. **Selector over-matching real content vs. generic listing metadata.** The scraper's fallback selector (`//div[@role='article']`) matched Google Maps' generic search-result and place-info cards, not just genuine Updates posts — for businesses with no active Updates tab, it was extracting business-listing metadata (name, rating, hours) and feeding that to the AI classifier, producing meaningless generic topics ("Business Information," "Business Profile"). Fixed by scoping extraction to a verified Updates-tab container, with an explicit "zero posts, no Updates tab" outcome when that container can't be found, rather than falling through to a page-wide search.
4. **Scraper's dependency on a local-only file mount.** `scraper/main.py` imported SQLAlchemy models from `backend/app/`, which only resolved locally because `docker-compose.yml` bind-mounted the backend folder into the scraper container at runtime. Render's Docker deployment model has no equivalent to a live host-folder mount, so this import failed silently in production (job stuck in `running` forever, `started_at` never set). Fixed by giving the scraper its own self-contained copies of the models/database code.

## Deployment Notes

- Production database is always fresh — provisioned via Alembic migrations + `python -m app.seed_demo`, never a copy of local development data. This is deliberate: local dev accumulated test/QA scratch data over the course of development that must never reach the evaluator-facing environment.
- The scraper runs on Render's free tier successfully, after tuning Chrome flags for memory (disabling unused browser subsystems — extensions, background sync, WebGL) and replacing fixed sleep-based waits with explicit `WebDriverWait` conditions tolerant of shared-CPU rendering delays.
