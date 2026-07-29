"""Sales connectors: CRM, leads, pipeline."""

from __future__ import annotations

import csv
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iidatech.integrations.registry import is_configured
from iidatech.storage.db import ensure_execution_schema, get_connection, sql_placeholder

_PLACEHOLDER_COMPANY = re.compile(
    r"^(company\s*\d+|prospect|example|sample|n/?a|tbd|unknown|target\s+company)$",
    re.I,
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_FAKE_EMAIL_DOMAIN = re.compile(r"@(?:example\.com|test\.com|email\.com|domain\.com)$", re.I)

LEAD_CSV_FIELDS = [
    "company",
    "contact_name",
    "title",
    "email",
    "phone",
    "website",
    "linkedin_url",
    "location",
    "source_url",
    "notes",
    "source",
]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def store_leads(report_id: str, leads: list[dict[str, Any]], *, source: str = "lead_scraper") -> dict[str, Any]:
    ensure_execution_schema()
    stored = 0
    p = sql_placeholder()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            for lead in leads:
                if not isinstance(lead, dict):
                    continue
                lid = _new_id("lead")
                cur.execute(
                    f"""INSERT INTO pipeline_leads
                    (lead_id, report_id, name, email, company, title, source, status, score, metadata_json, created_at, updated_at)
                    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    [
                        lid, report_id,
                        str(lead.get("name") or lead.get("contact_name") or ""), str(lead.get("email") or ""),
                        str(lead.get("company") or ""), str(lead.get("title") or ""),
                        source, str(lead.get("status") or "new"),
                        float(lead.get("score") or 0),
                        json.dumps(lead.get("metadata") or {}, ensure_ascii=False),
                        _now(), _now(),
                    ],
                )
                stored += 1
            conn.commit()
        finally:
            cur.close()
    return {"stored": stored, "report_id": report_id, "source": source}


def list_pipeline_leads(report_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    from iidatech.storage.db import row_to_dict

    ensure_execution_schema()
    p = sql_placeholder()
    rows: list[dict[str, Any]] = []
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"""SELECT name, email, company, title, source, status, score, metadata_json, created_at
                FROM pipeline_leads WHERE report_id = {p}
                ORDER BY created_at DESC LIMIT {p}""",
                [report_id, int(limit)],
            )
            for row in cur.fetchall():
                d = row_to_dict(row, drop_id=False) if hasattr(row, "keys") else {
                    "name": row[0], "email": row[1], "company": row[2], "title": row[3],
                    "source": row[4], "status": row[5], "score": row[6], "created_at": row[8],
                }
                rows.append(d)
        finally:
            cur.close()
    return rows


def upsert_crm_records(report_id: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    updated = 0
    errors: list[str] = []
    if is_configured("nocodb"):
        try:
            from backend_integrations import create_nocodb_record
            for rec in records:
                if not isinstance(rec, dict):
                    continue
                out = create_nocodb_record({**rec, "report_id": report_id})
                if out.get("ok"):
                    updated += 1
                else:
                    errors.append(str(out.get("message") or "nocodb error")[:120])
            if updated:
                return {"records_updated": updated, "backend": "nocodb", "errors": errors}
        except ImportError:
            pass
    if is_configured("runtime_crm"):
        try:
            from production_runtime import upsert_crm_contact
            for rec in records:
                if not isinstance(rec, dict):
                    continue
                upsert_crm_contact(
                    report_id,
                    name=str(rec.get("name") or ""),
                    email=str(rec.get("email") or ""),
                    company=str(rec.get("company") or ""),
                    title=str(rec.get("title") or ""),
                    source=str(rec.get("source") or "employee_os"),
                    status=str(rec.get("status") or "new"),
                    metadata=rec,
                )
                updated += 1
            return {"records_updated": updated, "backend": "runtime_crm", "errors": errors}
        except Exception as exc:
            errors.append(str(exc)[:120])
    out = store_leads(report_id, records, source="crm_update")
    return {"records_updated": out.get("stored", 0), "backend": "local_crm", "errors": errors}


def score_leads_file(leads_path: str, *, threshold: float = 0.5) -> dict[str, Any]:
    path = Path(leads_path)
    if not path.exists():
        return {"ok": False, "error": "leads file not found"}
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            score = 0.0
            if row.get("email"):
                score += 0.4
            if row.get("company"):
                score += 0.3
            if row.get("title"):
                score += 0.2
            if row.get("source"):
                score += 0.1
            row["score"] = round(min(score, 1.0), 2)
            row["qualified"] = "yes" if row["score"] >= threshold else "no"
            rows.append(row)
    out_path = path.with_name(path.stem + "_scored.csv")
    if rows:
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    qualified = sum(1 for r in rows if r.get("qualified") == "yes")
    return {
        "ok": True,
        "scored_count": len(rows),
        "qualified_count": qualified,
        "scores_path": str(out_path),
        "threshold": threshold,
    }


def leads_from_search_rows(rows: list[dict], *, limit: int) -> list[dict[str, Any]]:
    """Legacy fallback: map generic search rows to minimal lead stubs."""
    leads: list[dict[str, Any]] = []
    for row in rows[:limit]:
        title = str(row.get("title") or "")
        company = title.split(" - ")[0][:80] if title else ""
        url = str(row.get("url") or "").strip()
        leads.append({
            "company": company or title[:80],
            "contact_name": "",
            "title": "",
            "email": "",
            "phone": "",
            "website": url if url and "linkedin.com" not in url.lower() else "",
            "linkedin_url": url if "linkedin.com" in url.lower() else "",
            "location": "",
            "source_url": url,
            "notes": str(row.get("snippet") or "")[:300],
            "source": row.get("provider") or "search",
            "metadata": {"url": url, "snippet": row.get("snippet")},
        })
    return leads


def _clean_field(value: Any, *, max_len: int = 200) -> str:
    return str(value or "").strip()[:max_len]


def _valid_email(email: str) -> str:
    e = _clean_field(email, max_len=120)
    if not e or not _EMAIL_RE.match(e) or _FAKE_EMAIL_DOMAIN.search(e):
        return ""
    return e


def _valid_company(company: str) -> bool:
    c = _clean_field(company, max_len=120)
    if len(c) < 2:
        return False
    if _PLACEHOLDER_COMPANY.match(c):
        return False
    return True


def normalize_lead_records(
    parsed: dict[str, Any] | list[Any] | None,
    *,
    citations: list[Any] | None = None,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Deterministic normalization of Perplexity lead JSON into CRM-ready rows."""
    raw_rows: list[Any] = []
    if isinstance(parsed, dict):
        raw_rows = list(parsed.get("leads") or parsed.get("companies") or [])
    elif isinstance(parsed, list):
        raw_rows = parsed
    citation_urls = [str(u).strip() for u in (citations or []) if str(u or "").strip()]

    leads: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        company = _clean_field(row.get("company") or row.get("company_name") or row.get("name"))
        if not _valid_company(company):
            continue
        key = company.lower()
        if key in seen:
            continue
        website = _clean_field(row.get("website") or row.get("url") or row.get("domain"))
        source_url = _clean_field(row.get("source_url") or row.get("source") or "")
        if not website and not source_url and citation_urls:
            source_url = citation_urls[min(len(seen), len(citation_urls) - 1)]
        if not website and not source_url:
            continue
        if website and not website.startswith(("http://", "https://")):
            website = f"https://{website.lstrip('/')}"
        if source_url and not source_url.startswith(("http://", "https://")):
            source_url = f"https://{source_url.lstrip('/')}"

        linkedin = _clean_field(row.get("linkedin_url") or row.get("linkedin"))
        lead = {
            "company": company,
            "contact_name": _clean_field(row.get("contact_name") or row.get("contact")),
            "title": _clean_field(row.get("title") or row.get("role")),
            "email": _valid_email(str(row.get("email") or "")),
            "phone": _clean_field(row.get("phone") or row.get("telephone"), max_len=40),
            "website": website,
            "linkedin_url": linkedin,
            "location": _clean_field(row.get("location") or row.get("city") or row.get("geography")),
            "source_url": source_url or website,
            "notes": _clean_field(row.get("notes") or row.get("fit") or row.get("snippet"), max_len=400),
            "source": "perplexity_live",
            "metadata": {"source_url": source_url or website},
        }
        if not lead["contact_name"] and row.get("contact"):
            lead["contact_name"] = _clean_field(row.get("contact"))
        seen.add(key)
        leads.append(lead)
        if len(leads) >= limit:
            break
    return leads


def format_leads_preview(leads: list[dict[str, Any]], *, max_rows: int = 8) -> str:
    if not leads:
        return ""
    lines = ["| Company | Contact | Title | Website |", "| --- | --- | --- | --- |"]
    for row in leads[:max_rows]:
        lines.append(
            "| {company} | {contact} | {title} | {website} |".format(
                company=_clean_field(row.get("company"), max_len=40) or "—",
                contact=_clean_field(row.get("contact_name"), max_len=30) or "—",
                title=_clean_field(row.get("title"), max_len=30) or "—",
                website=_clean_field(row.get("website") or row.get("source_url"), max_len=40) or "—",
            )
        )
    if len(leads) > max_rows:
        lines.append(f"\n*Showing {max_rows} of {len(leads)} leads.*")
    return "\n".join(lines)


def read_leads_csv(path: str | Path) -> list[dict[str, str]]:
    p = Path(path)
    if not p.is_file():
        return []
    with p.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write_leads_csv(path: Path, leads: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEAD_CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            meta = lead.get("metadata") if isinstance(lead.get("metadata"), dict) else {}
            writer.writerow({
                "company": lead.get("company", lead.get("name", "")),
                "contact_name": lead.get("contact_name", lead.get("name", "")),
                "title": lead.get("title", ""),
                "email": lead.get("email", ""),
                "phone": lead.get("phone", ""),
                "website": lead.get("website", meta.get("url", "")),
                "linkedin_url": lead.get("linkedin_url", ""),
                "location": lead.get("location", ""),
                "source_url": lead.get("source_url", meta.get("url", "")),
                "notes": lead.get("notes", meta.get("snippet", "")),
                "source": lead.get("source", "lead_scraper"),
            })