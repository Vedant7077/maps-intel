# AI Provider Evidence

## Providers Used
- **Primary**: Google Gemini (`gemini-1.5-flash` / `gemini-flash-lite-latest`), called directly via the Generative Language API
- **Secondary (fallback)**: Grok (`x-ai/grok-4.3`), called via OpenRouter

Both are called only from n8n workflows running server-side (Render); API keys are stored as environment variables on the n8n and scraper-worker services and are never sent to or accessible from the frontend.

## Forced Fallback Test

To confirm the fallback path genuinely works — not just that a second API key is present in configuration — `GEMINI_API_KEY` was deliberately set to an invalid value and n8n restarted, then a classification run was triggered.

**Result:**
- Gemini node failed with `400 API_KEY_INVALID`, as expected
- The IF node correctly routed to the Grok fallback branch
- Grok returned valid classification JSON, which was parsed and saved
- Sample post classified via Grok during this test: `main_topic: "Seasonal Drink Promotion"`, `sub_topic: "Cold Brew"`, `keywords: ["cold brew", "monsoon cold brew", "limited batch", "seasonal"]`

`GEMINI_API_KEY` was then reverted and n8n restarted again; a subsequent classification run correctly used the Gemini path (not Grok), confirming normal operation was fully restored.

## Duplicate-Prevention Test (Content Generation)

Two consecutive idea-generation batches were requested for the same project (3 ideas, then 5 more). Comparing `topic_title` across both batches as a set showed **zero overlap** — confirming the prompt's history-injection (querying prior `generated_ideas.topic_title` values and instructing the model not to repeat them) works as designed, not just that the feature exists in code.
