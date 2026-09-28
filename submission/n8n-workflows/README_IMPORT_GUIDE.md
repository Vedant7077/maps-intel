# n8n Workflow Import Guide — Day 3

These 5 workflows are built against your **actual** schema and endpoints as of Day 2 (real `Post`/`ScrapeJob`/`TrendSnapshot`/`GeneratedIdea` fields, real webhook paths your scraper already calls).

## Before importing anything

### 1. Create the Postgres credential once
n8n UI → Credentials → New → **Postgres**
- Host: `postgres`
- Port: `5432` (the internal Docker network port — NOT 5433, that's only for your host machine)
- Database: `mapspy`
- User: `postgres`
- Password: (your `POSTGRES_PASSWORD`)
- Name it something memorable, e.g. `MapsPy Postgres`

### 2. Create the SMTP credential (only needed for WF-05)
n8n UI → Credentials → New → **SMTP**
- Host: `smtp.gmail.com`, Port: `587`, User: your Gmail, Password: your Gmail **app password** (not your normal password)
- Name it `Gmail SMTP`

### 3. Set environment variables on the n8n container
Add to `docker-compose.yml` under the `n8n` service's `environment:` block:
```yaml
- GEMINI_API_KEY=${GEMINI_API_KEY}
- GROK_API_KEY=${GROK_API_KEY}
- ALERT_EMAIL=${ALERT_EMAIL}
```
(They're already in your root `.env` — this just makes n8n's Code/HTTP nodes able to read `$env.GEMINI_API_KEY` etc.)

## Import order

Import in this order, since later workflows reference earlier webhook paths:

1. **WF-05-alert-system.json** — import first so `/webhook/alert` exists before the scraper calls it
2. **WF-02-ai-classifier.json** — has `/webhook/scrape-complete`, which your scraper already calls today
3. **WF-03-trend-aggregator.json** — chained from WF-02's last node
4. **WF-04-content-generator.json** — standalone, called from your `/api/generate/ideas` backend endpoint
5. **WF-01-scrape-orchestrator.json** — the "run everything" entry point, import last

For each file: n8n canvas → **"..."** menu (top right) → **Import from File** → select the JSON.

## After each import — required manual step

n8n does **not** export credential bindings (this is by design, for security). After importing, every Postgres node will show a red "credential not set" warning. Click each Postgres node → select your `MapsPy Postgres` credential from the dropdown → save. Same for the 3 Email nodes in WF-05 → select `Gmail SMTP`.

## Activate

Toggle each workflow **Active** (top-right switch) once credentials are wired. Only WF-01 needs to be Active for its nightly schedule to actually run — the others are pure webhook receivers and work as soon as they're active, regardless of the toggle being about the schedule specifically.

## Test the full chain end-to-end

```bash
# 1. Trigger orchestrator manually (bypasses the 2am schedule)
curl -X POST http://localhost:5678/webhook/trigger-scrape \
  -H "Content-Type: application/json" \
  -d '{"project_id":"<your-project-id>"}'

# 2. Watch it flow: WF-01 -> backend /api/scrape/start -> scraper container
docker-compose logs scraper-worker -f

# 3. Once scrape finishes, scraper calls /webhook/scrape-complete itself (WF-02 picks up)
#    Check n8n's Executions tab (left sidebar) to see WF-02 -> WF-03 fire automatically

# 4. Check trends landed
curl "http://localhost:8000/api/trends?project_id=<your-project-id>"

# 5. Generate ideas directly (tests WF-04 in isolation)
curl -X POST "http://localhost:8000/api/generate/ideas?project_id=<your-project-id>&count=3"
```

## Known gaps / things to add later, not blockers

- **`trend_snapshots` has no unique constraint on `(project_id, topic)`** — WF-03 works around this with a delete-then-insert instead of a true `ON CONFLICT` upsert. Fine for now; add the constraint via Alembic later if you want proper upserts.
- **No `alerts` table exists** — WF-05 only emails, it doesn't log alert history to Postgres. Add a table later if you want alert history visible in the UI (not required by the PDF).
- **WF-04's webhook uses `responseMode: responseNode`**, meaning it holds the HTTP connection open until Gemini responds and the idea is saved — your backend's `httpx.post(..., timeout=30)` call to it needs to keep that 30s timeout (it already does).
