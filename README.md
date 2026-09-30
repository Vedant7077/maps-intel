# 🗺️ MapSpy — Google Maps Competitor Intelligence & AI Content Engine

**MapSpy** is an end-to-end intelligence and content generation platform for local businesses. It autonomously monitors competitor Google Maps profiles ("Updates" / Local Posts), extracts real-time updates using an evasion-hardened headless Chromium scraper, analyzes marketing trends via AI, and automatically generates counter-marketing campaign ideas.


## 🚀 Live Deployment

| Component | Status | URL | Description |
|---|---|---|---|
| **Frontend Application** | 🟢 Live | [https://mapspy-app.vercel.app](https://mapspy-app.vercel.app) | Evaluator-facing React dashboard (no login required) |
| **Backend API** | 🟢 Live | [https://mapspy-backend.onrender.com](https://mapspy-backend.onrender.com) | FastAPI REST service (Interactive Swagger docs: [`/docs`](https://mapspy-backend.onrender.com/docs)) |
| **n8n Workflow Engine** | 🟢 Live | [https://mapspy-n8n.onrender.com](https://mapspy-n8n.onrender.com) | Autonomous orchestration & AI classification pipelines |

---

## 📑 Table of Contents

- [Live Deployment](#-live-deployment)
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Directory Structure](#-directory-structure)
- [Local Development Setup](#-local-development-setup)
  - [Prerequisites](#prerequisites)
  - [Running with Docker Compose (Recommended)](#running-with-docker-compose-recommended)
  - [Manual / Local Service Setup](#manual--local-service-setup)
- [Environment Variables](#-environment-variables)
- [Production Deployment](#-production-deployment)
  - [Live Endpoints](#live-endpoints)
  - [Backend & Workers on Render](#backend--workers-on-render)
  - [Frontend on Vercel](#frontend-on-vercel)
- [Render 512MB Free Tier Optimizations](#-render-512mb-free-tier-optimizations)
- [n8n Automation Workflows](#-n8n-automation-workflows)
- [API Reference](#-api-reference)
- [Database Seeding](#-database-seeding)
- [Troubleshooting](#-troubleshooting)

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Client Layer
        UI["React 19 + Vite Frontend\n(Vercel)"]
    end

    subgraph Core Services
        API["FastAPI Backend\n(Render / Docker)"]
        DB[("PostgreSQL 15\n(Render DB)")]
        N8N["n8n Workflow Engine\n(5 Automations)"]
        SCRAPER["Headless Chromium Scraper\n(Selenium + CDP Stealth)"]
    end

    subgraph External & AI Providers
        GMAPS[("Google Maps\nCompetitor Profiles")]
        GEMINI["Google Gemini AI"]
        GROQ["Groq / xAI LLM"]
    end

    UI -->|REST / Polling| API
    API -->|Read / Write| DB
    API -->|Trigger Scrape| SCRAPER
    API -->|Trigger Workflows| N8N
    SCRAPER -->|Crawl Updates Tab| GMAPS
    SCRAPER -->|Save Posts & Status| DB
    SCRAPER -->|Webhook On Complete| N8N
    N8N -->|Classify & Aggregate| DB
    API -->|Prompt & Generate Ideas| GEMINI
    API -->|Prompt & Generate Ideas| GROQ
```

---

## ✨ Key Features

1. **Autonomous Google Maps Scraper**
   - Headless Chromium with Chrome DevTools Protocol (CDP) evasion (`navigator.webdriver` suppression, automation flag stripping, custom user agents).
   - Scrapes competitor posts, announcements, promotional offers, and publication dates.
   - SHA-256 content deduplication prevents redundant database records.
   - Memory-engineered to execute reliably within Render's **512MB RAM free tier**.

2. **Real-time Scrape Job Monitoring**
   - Background subprocess execution with non-blocking FastAPI endpoints.
   - Frontend live status monitor polling job state (`started` → `running` → `completed` / `failed`) with post extraction metrics.

3. **Content Repository & Intelligence**
   - Searchable, filterable repository of all captured competitor updates.
   - Multi-competitor comparison, activity cadence, and historical post analytics.

4. **Competitive Gap & Trend Analysis**
   - Automatically clusters posts into categories (Promotions, Events, New Offerings, Community).
   - Identifies content gaps where rivals are actively publishing but your business is silent.

5. **AI Content Idea Generator**
   - Generates tailored local marketing copy and campaign concepts based on competitor activities.
   - Powered by **Google Gemini** and **Groq (Llama / Mixtral)**.

6. **n8n Orchestration Workflows**
   - Automated post-scraping triggers, AI classification pipelines, trend aggregation, and email alert notifications.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Frontend** | React 19, Vite, Tailwind CSS, Recharts, Lucide Icons | Responsive modern SPA with interactive charts and real-time polling |
| **Backend API** | Python 3.11, FastAPI, SQLAlchemy, Alembic | Async REST API handling business logic, jobs, and analytics |
| **Scraper Worker** | Python, Selenium, Debian Chromium, Chromedriver | Headless browser scraper with CDP stealth flags |
| **Database** | PostgreSQL 15 | Relational storage for projects, competitors, posts, and jobs |
| **Workflow Engine**| n8n | Low-code orchestration for AI classification, pipelines, and alerts |
| **AI / LLMs** | Google Gemini, Groq / xAI | Post categorization, gap analysis, and creative ideation |
| **DevOps** | Docker, Docker Compose, Render Blueprint, Vercel | Multi-service orchestration and CI/CD hosting |

---

## 📂 Directory Structure

```text
maps-intel/
├── backend/                  # FastAPI Application
│   ├── app/
│   │   ├── main.py           # API endpoints and route definitions
│   │   ├── database.py       # SQLAlchemy engine & session config
│   │   ├── models.py         # Database ORM models
│   │   └── seed_demo.py      # Deterministic demo dataset seeder
│   ├── alembic/              # Database migration scripts
│   ├── Dockerfile            # Backend container configuration
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React 19 Single Page App
│   ├── src/
│   │   ├── pages/            # Dashboard, Rivals, Monitor, Repository, Analysis, Generator
│   │   ├── components/       # UI navigation, cards, charts, modals
│   │   ├── context/          # App state & project context
│   │   └── lib/              # API clients and utilities
│   ├── package.json          # Frontend packages & scripts
│   └── vite.config.js        # Vite build & proxy settings
├── scraper/                  # Headless Scraping Microservice
│   ├── main.py               # Core Selenium scraper & CDP stealth logic
│   ├── server.py             # FastAPI HTTP wrapper for job dispatching
│   ├── models.py             # Shared DB schemas
│   ├── Dockerfile            # Chromium + chromedriver Debian image
│   └── requirements.txt      # Scraper dependencies
├── n8n-workflows/            # Exported n8n workflow definitions (.json)
│   ├── SGaZ4aKg4nu2OV7A.json # WF-01 Scrape Orchestrator
│   ├── nBI11ypW34Jw8cMK.json # WF-02 AI Post Classifier
│   ├── j760djR2dHvTWcHJ.json # WF-03 Trend Aggregator
│   ├── Igawa7psDoQEA2r0.json # WF-04 Content Idea Generator
│   └── 03Iya4B9URMsQVeR.json # WF-05 Alert System
├── postgres-init/            # Initial DB setup scripts
├── docker-compose.yml        # Local multi-container development environment
├── render.yaml               # Render Infrastructure-as-Code Blueprint
└── .env                      # Environment variables configuration
```

---

## 🚀 Local Development Setup

### Prerequisites
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- Python 3.11+ (if running bare-metal)
- Node.js 18+ & npm (if running bare-metal)

### Running with Docker Compose (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd maps-intel
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env  # Or edit the existing .env file
   ```

3. **Start all services:**
   ```bash
   docker compose up --build
   ```

   This launches:
   - **PostgreSQL**: `localhost:5433` (mapped internally to `5432`)
   - **Backend API**: `http://localhost:8000` (docs at `/docs`)
   - **Scraper Worker**: `http://localhost:8001`
   - **n8n Workflow Engine**: `http://localhost:5678`
   - **Redis**: `localhost:6379`

4. **Start the Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory:

```ini
# PostgreSQL Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/mapspy
POSTGRES_PASSWORD=postgres

# AI Provider API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROK_API_KEY=your_grok_or_openrouter_api_key_here

# Service URLs
N8N_BASE_URL=http://localhost:5678
SCRAPER_BASE_URL=http://localhost:8001
ALERT_EMAIL=alerts@yourdomain.com

# Frontend Configuration (frontend/.env)
VITE_API_BASE_URL=http://localhost:8000
```

---

## 🌐 Production Deployment

The project is deployed and live across **Render** (backend services, PostgreSQL, n8n, scraper) and **Vercel** (frontend).

### Live Endpoints
- **Frontend Dashboard:** [https://mapspy-app.vercel.app](https://mapspy-app.vercel.app) *(No login required)*
- **Backend API:** [https://mapspy-backend.onrender.com](https://mapspy-backend.onrender.com)
- **API Documentation (Swagger):** [https://mapspy-backend.onrender.com/docs](https://mapspy-backend.onrender.com/docs)
- **n8n Workflow Engine:** [https://mapspy-n8n.onrender.com](https://mapspy-n8n.onrender.com)

### Backend & Workers on Render
The repository includes a root `render.yaml` Blueprint defining:
1. `mapspy-postgres`: Managed PostgreSQL instance.
2. `mapspy-backend`: FastAPI application with automatic migration execution (`alembic upgrade head`).
3. `mapspy-scraper`: Dockerized Chromium worker executing scraping tasks.
4. `mapspy-n8n`: Official n8n Docker image connected to PostgreSQL.

To deploy on Render:
1. Connect your GitHub repository to Render.
2. Navigate to **Blueprints** and select `render.yaml`.
3. Fill in the required environment secrets (`GEMINI_API_KEY`, `GROK_API_KEY`, `ALERT_EMAIL`).
4. Click **Apply Blueprint**.

### Frontend on Vercel
1. Import the `frontend/` directory into Vercel.
2. Set Framework Preset to **Vite**.
3. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://mapspy-backend.onrender.com`
4. Deploy.

---

## 💡 Render 512MB Free Tier Optimizations

Headless Chromium running modern Google Maps typically demands 800MB–1.2GB of RAM. To run reliably on Render's **Free Tier (512MB limit)** without out-of-memory (OOM) crashes, the scraper incorporates targeted flags and wait patterns:

1. **V8 Memory Constraints:**
   - `--js-flags=--max-old-space-size=256`: Constrains JavaScript heap to 256MB.
2. **Process Architecture:**
   - `--single-process`: Unifies renderer and browser processes into a single address space.
3. **Graphics & WebGL Suppression:**
   - `--disable-webgl`, `--disable-gpu`, `--disable-software-rasterizer`: Drops heavy 3D canvas and WebGL rendering passes.
4. **Feature Stripping:**
   - Disables background sync, timers, extensions, translate prompts, and crash reporting (`--disable-background-networking`, `--disable-sync`, etc.).
5. **Explicit Wait Condition:**
   - Replaced fixed `time.sleep()` with an explicit `WebDriverWait(driver, 20)` targeting post card selector patterns (`cKbrCd`, `local-post`, `aria-label='Update'`), ensuring completion even under shared-CPU throttling.

---

## 🔄 n8n Automation Workflows

The `n8n-workflows/` directory contains 5 modular workflows ready for import:

| Workflow ID | Name | Trigger | Action |
| :--- | :--- | :--- | :--- |
| `WF-01` | **Scrape Orchestrator** | Cron schedule or manual API trigger | Dispatches scrape requests across active competitors |
| `WF-02` | **AI Post Classifier** | Webhook `/scrape-complete` | Evaluates unclassified posts and labels marketing categories |
| `WF-03` | **Trend Aggregator** | Scheduled weekly | Aggregates posting frequency and emergent themes |
| `WF-04` | **Content Idea Generator** | Webhook `/generate-ideas` | Uses competitor post history to craft actionable campaign ideas |
| `WF-05` | **Alert System** | Webhook on competitor activity | Sends email alert when a rival launches a high-impact campaign |

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status |
| `GET` | `/api/projects` | List all client projects |
| `POST` | `/api/projects` | Create a new project workspace |
| `GET` | `/api/competitors` | List rivals for a given project (`?project_id=...`) |
| `POST` | `/api/competitors` | Add a new competitor with Google Maps URL |
| `POST` | `/api/scrape/start` | Trigger an asynchronous scrape job |
| `GET` | `/api/jobs/{job_id}` | Poll scrape job progress and statistics |
| `GET` | `/api/posts` | Query and filter extracted competitor posts |
| `GET` | `/api/trends` | Retrieve aggregated trend snapshots |
| `GET` | `/api/gaps` | Compute competitor content gaps |
| `POST` | `/api/generate/ideas` | Generate AI marketing ideas from competitor data |

---

## 🧪 Database Seeding

To initialize the database with deterministic demo data (featuring client **Boojee Cafe** and rivals **Mary Lodge by Subko**, **Tuskin Coffee**, and **Starbucks Bandra West**):

```bash
# Inside backend container or locally with virtualenv active:
python -m app.seed_demo
```

This clears old records and inserts:
- 1 Canonical Project (`Boojee Cafe`)
- 3 Direct Rivals + 1 Client Profile
- 20+ Pre-classified historical posts
- Trend metrics and sample AI ideas

---

## ❓ Troubleshooting

- **Scraper returns 0 posts:**
  - Verify that the target Google Maps business actually has an **Updates** tab. (Many businesses only have Overview/Reviews).
  - Ensure the Chromium container is running with proper memory flags if deployed on a memory-constrained host.
- **n8n webhooks not triggering:**
  - Ensure `N8N_BASE_URL` in the backend environment matches the reachable address of your n8n instance.
  - In n8n, verify that imported workflows have been toggled to **Active**.
- **CORS errors on frontend:**
  - Confirm `VITE_API_BASE_URL` points to your active backend host. The FastAPI backend is configured with permissive CORS defaults (`allow_origins=["*"]`).
