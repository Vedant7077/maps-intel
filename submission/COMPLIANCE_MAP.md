# Requirements Compliance Map

| Requirement | Implementation | Evidence |
|---|---|---|
| Python-based scraper, Selenium required | `scraper/main.py` — Selenium + Chromium | Live scrapes completed on Mary Lodge by Subko, Starbucks Bandra West, Tuskin Coffee, Boojee Cafe |
| 2+ AI providers, keys never exposed to frontend | Gemini (primary) + Grok via OpenRouter (fallback), both called only from n8n backend workflows | Forced-fallback test: Gemini key deliberately invalidated, Grok correctly classified posts, then reverted and Gemini path re-confirmed working — see `AI_PROVIDERS.md` |
| CAPTCHA handled gracefully (pause, notify, resume) | `detect_captcha()` in scraper, `/api/jobs/{id}/resume` endpoint, WF-05 email alert | Code path verified via audit; not naturally triggered during testing (documented honestly rather than faked) |
| Pre-populated demo dataset, evaluator can't rely on live scrape | `seed_demo.py` seeds a complete dataset — client business, 3 rivals, posts with a deliberately partial topic overlap so gap analysis produces meaningful results with zero live scraping | `GET /api/gaps` on the seeded project returns non-empty `gaps`/`covered`/`client_only_topics` immediately after a fresh seed, before any scrape runs |
| Hosted publicly, no auth wall | Vercel (frontend) + Render (backend, n8n, scraper, Postgres) | Live URLs in `README.md` |
| Duplicate detection, SHA-256 content_hash | Project-scoped, normalized-input hash (see `ARCHITECTURE.md` bugs #1 and #2) | Re-scraping the same business returns `0 new, N duplicates` |
| Post extraction: business name, URL, text, date, images, CTA | `Post` model + scraper extraction | `data/sample_posts.csv` |
| AI classification: topic, sub-topic, keywords, content type, CTA, promotion detection | WF-02 (Gemini/Grok), `Post.main_topic`/`sub_topic`/`keywords`/`content_type`/`cta_type`/`has_promotion` | `data/ai_classification_example.json` |
| Trend analysis across competitors | WF-03 aggregation, `GET /api/trends` | Live trend data on the seeded project |
| Content idea generation with drafts | WF-04, `GET /api/generate/ideas` | `data/generated_drafts_sample.json` |
| Duplicate-idea prevention | WF-04 injects prior idea titles into the generation prompt | Verified: 0 title overlap between two consecutive generation batches |
| Fact-safe AI generation (no invented names/events) | Explicit prompt constraint in WF-04 | Generated content stays generic/plausible (e.g. "Live Acoustic Thursday") rather than inventing specific unsupported claims |
| Full web interface, non-technical user can operate it end to end | React frontend, 8 screens (Dashboard, Projects, Rivals, My Business, Repository, Monitor, Analysis, Generator) | Live frontend URL |
| Gap analysis: competitor topics the client is missing | `is_client` flag on `Competitor`, `GET /api/gaps` real diff | `data/ai_classification_example.json` topic matrix; live `/api/gaps` response in `ARCHITECTURE.md` |
| System resilient to scraping failures (per assignment's own note that live Maps access can be unreliable) | Seed dataset is fully independent of live scraping; zero-post businesses handled gracefully, not as errors | `seed_demo.py` design |
