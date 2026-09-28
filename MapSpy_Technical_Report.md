# MapSpy — Technical Documentation & Evaluation Report

**AI-Powered Google Maps Competitor Intelligence & Counter-Marketing Strategy Engine**  
**Repository:** [https://github.com/Vedant7077/maps-intel](https://github.com/Vedant7077/maps-intel)  
**Live Frontend:** [https://mapspy-app.vercel.app](https://mapspy-app.vercel.app)  
**Backend API:** [https://mapspy-backend.onrender.com](https://mapspy-backend.onrender.com) (Swagger Docs: `/docs`)  
**n8n Workflow Engine:** [https://mapspy-n8n.onrender.com](https://mapspy-n8n.onrender.com)  

---

## 1. Executive Summary

Local brick-and-mortar businesses frequently lose foot traffic to competitors because monitoring Google Maps "Updates" (local posts, limited-time offers, and events) manually across dozens of local businesses is labor-intensive and sporadic.

**MapSpy** solves this through an autonomous competitor intelligence engine:
1. **Stealth Scraper**: Extracts real-time Google Maps local updates using a containerized Selenium Chromium worker with Chrome DevTools Protocol (CDP) evasion.
2. **Dual-AI Classification Pipeline**: Automatically categorizes extracted updates by marketing topic, sub-topic, keywords, content type, and CTA category using Google Gemini 1.5 Flash with automatic fallback to Grok (`x-ai/grok-4.3` via OpenRouter).
3. **Client-vs-Rival Gap Analysis**: Ingests the client's own business through the same pipeline to calculate exact competitor topic gaps and differentiators.
4. **Counter-Marketing Generator**: Generates high-converting, fact-constrained Google Maps posts with duplicate prevention to exploit rival content weaknesses.

---

## 2. System Architecture

```
[ Client Browser (Evaluator) ]
            │
            ▼
[ Frontend: React 19 + Vite + TailwindCSS ] (Vercel)
            │  HTTPS (REST / Polling)
            ▼
[ Backend API: FastAPI + Python 3.11 ] (Render)
      │                     │
      │ Webhooks            │ Read/Write
      ▼                     ▼
[ n8n Automation Engine ] ◄──► [ PostgreSQL 15 DB ] (Render Managed)
      │                     ▲
      │ Trigger Scrape      │ Saves Posts & Hash Dedup
      ▼                     │
[ Scraper Worker: Chromium Headless ] (Render Docker Worker)
      │
      ▼
[ Google Maps Competitor Profiles ]
```

### Architectural Decisions
- **Decoupled Scraper Worker**: The FastAPI API never runs Chromium directly. Scraping is offloaded to a standalone containerized worker, keeping the API image lightweight (~200MB) while the worker carries the Chromium binary and dependencies (~650MB).
- **n8n Orchestration**: Post-scrape workflows (AI classification, trend snapshots, error handling) are handled by n8n. This eliminates hand-rolled queue systems and allows real-time inspection of pipeline stages.
- **Self-Contained Worker Models**: The scraper carries standalone database models, ensuring Docker images run identically in local Docker Compose and on cloud platforms (Render) without host volume-mount dependencies.

---

## 3. Web Scraping & Anti-Detection Engineering

- **Evasion & CDP Stealth**: Standard Selenium is detected by Google's bot detection. MapSpy uses Debian-packaged Chromium with Chrome DevTools Protocol (CDP) execution hooks to remove `navigator.webdriver`, spoof realistic screen color depth, hardware concurrency, and user-agent fingerprints.
- **Scoped Updates-Tab Parsing**: Avoids false positives from generic place cards. The scraper explicitly locates the verified Updates panel before parsing, handling businesses without active posts gracefully rather than scraping directory metadata.
- **Project-Scoped SHA-256 Deduplication**:
  $$\text{content\_hash} = \text{SHA256}(\text{project\_id} + \text{normalized\_post\_url} + \text{normalized\_post\_text}[:100])$$
  URL tracking parameters (`g_ep`, `entry`) and volatile listing text (live star ratings, opening hours) are stripped before hashing to ensure idempotent scraping.
- **CAPTCHA Graceful Handling**: When a verification screen or CAPTCHA is detected:
  1. The scraper pauses execution and updates the job status to `paused`.
  2. An email alert is triggered via n8n (WF-05).
  3. Scrapes can be resumed cleanly via `POST /api/jobs/{job_id}/resume`.

---

## 4. Dual AI Provider & Fallback Architecture

To ensure high availability against rate limits and upstream outages, MapSpy implements a resilient dual-provider architecture:

| Provider | Model / Endpoint | Role | Execution Context |
|---|---|---|---|
| **Primary** | Google Gemini 1.5 Flash (`generativelanguage.googleapis.com`) | Post Classification & Strategy Generation | n8n WF-02 & FastAPI Fallback |
| **Secondary** | Grok (`x-ai/grok-4.3` via OpenRouter) | Seamless Classification Fallback | n8n WF-02 Fallback Branch |

### Fallback Verification
During testing, `GEMINI_API_KEY` was deliberately invalidated. The n8n conditional routing node detected the HTTP 400 error and routed payloads to Grok, which parsed topics and saved records with zero pipeline downtime.

### Duplicate-Prevention & Fact-Safety Constraints
1. **Dynamic Prompt Injection**: Prior idea titles from `generated_ideas` are injected into the generation prompt, ensuring 0% title collision across consecutive batches.
2. **Fact Grounding**: Prompts forbid inventing dates, employee names, or unverified claims, keeping generated drafts realistic and compliance-safe.

---

## 5. Competitor Gap Analysis Methodology

Rather than maintaining separate schemas, the client's own business is stored as a first-class entity with `is_client = True`.

When `GET /api/gaps` is called:
$$\text{Gaps} = \text{RivalTopics} \setminus \text{ClientTopics}$$
$$\text{Covered} = \text{RivalTopics} \cap \text{ClientTopics}$$
$$\text{Client Only} = \text{ClientTopics} \setminus \text{RivalTopics}$$

### Production Findings (Boojee Cafe Demo Project):
- **Competitor Gaps**: Happy Hour (18.8% of rival posts), Collaboration (12.5%), Loyalty Program (12.5%)
- **Covered Overlaps**: New Menu Item, Seasonal Offer, Weekend Special
- **Client Strength**: Signature Drink (25.0% of client posts, 0% of rival posts)

---

## 6. Real Engineering Bugs Found and Fixed

1. **Cross-Project Hash Collision**: Hash was originally global, causing multiple projects tracking the same business to drop posts as duplicates. Fixed by scoping hashes to `project_id`.
2. **Hash Volatility**: Ephemeral URL parameters (`g_ep`) caused identical posts to re-save on every scrape. Fixed via URL and text normalization before hashing.
3. **Container Import Failure on Cloud**: Scraper imported models from backend directory via docker-compose host mounts. In Render cloud containers, bind mounts do not exist. Fixed by self-containing database models inside the scraper package.
4. **Render Free-Tier Cold-Start Lock**: Frontend flashed "No project selected" when the Render backend was waking up from sleep (50-90s). Fixed by persisting the active project in `localStorage`, adding default seed project fallback, and implementing exponential retry backoff in React Query.

---

## 7. Requirements Compliance Matrix

| Requirement | Implementation | Evidence |
|---|---|---|
| Python Scraper (Selenium required) | `scraper/main.py` (Selenium + Chromium CDP) | 23 live posts extracted from 4 real businesses |
| 2+ AI Providers (Server-side keys) | Gemini 1.5 Flash + Grok (`x-ai/grok-4.3`) in n8n / backend | Forced-fallback test documented in `AI_PROVIDERS.md` |
| CAPTCHA Handling | Pause, notify via email, resume via `/api/jobs/{id}/resume` | `detect_captcha()` code & WF-05 email notification |
| Pre-populated Demo Dataset | `seed_demo.py` with 23 posts & 3 competitors | Instant evaluation with zero live scraping dependency |
| Public Web Deployment (No Auth Wall) | Vercel (Frontend) + Render (Backend, n8n, Scraper, DB) | https://mapspy-app.vercel.app |
| Duplicate Detection (SHA-256) | Project-scoped normalized SHA-256 hash | Re-scraping yields `0 new, N duplicates` |
| Gap Analysis | Set diff between client topics and competitor topics | Live `/api/gaps` endpoint and Analysis screen |
| Full Web Interface | React 19 SPA with 8 dedicated screens | Dashboard, Projects, Rivals, Repository, Analysis, Generator |
