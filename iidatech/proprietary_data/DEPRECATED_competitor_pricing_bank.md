# DEPRECATED — competitor_pricing_bank.jsonl

Audit 2026-07-06: 258 rows, 0% live-verified, 28% explicit synthetic placeholders,
72% unrefreshed seed from tools/seed_proprietary_datasets.py (single date 2026-06-26).

**Do not use for competitor_matrix or real_confidence scoring.**

Competitor rows must come from Perplexity Sonar + Firecrawl verification only.

Still read by (legacy / opt-in):
- `iidatech/evidence_bank/seed_bank_refresh.py` — backfill evidence_bank placeholders
- `iidatech/services/pricing_bank_bridge.py` — only when IIDATECH_COMPETITOR_PRICING_BANK=1
- `tools/seed_proprietary_datasets.py` — regeneration
- `tools/migrate_jsonl_to_sql.py` — SQL migration

Re-enable bank reads: set env `IIDATECH_COMPETITOR_PRICING_BANK=1`
