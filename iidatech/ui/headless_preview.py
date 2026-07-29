"""Headless customer preview — no Streamlit required."""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from typing import Any


def _esc(text: Any) -> str:
    return html.escape(str(text or ""))


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def markdown_to_html_simple(md: str) -> str:
    """Lightweight markdown render for preview (no extra deps)."""
    lines = str(md or "").splitlines()
    out: list[str] = []
    in_pre = False
    table_rows: list[list[str]] = []

    def _flush_table() -> None:
        nonlocal table_rows
        if not table_rows:
            return
        out.append('<table class="md-table">')
        for i, row in enumerate(table_rows):
            tag = "th" if i == 0 else "td"
            out.append("<tr>" + "".join(f"<{tag}>{_esc(c)}</{tag}>" for c in row) + "</tr>")
        out.append("</table>")
        table_rows = []

    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith("|") and "|" in line[1:]:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(set(c) <= {"-", ":", " "} for c in cells):
                continue
            table_rows.append(cells)
            continue
        _flush_table()
        if line.startswith("```"):
            if in_pre:
                out.append("</pre>")
                in_pre = False
            else:
                out.append('<pre class="md-code">')
                in_pre = True
            continue
        if in_pre:
            out.append(_esc(line))
            continue
        if line.startswith("### "):
            out.append(f"<h3>{_esc(line[4:])}</h3>")
        elif line.startswith("## "):
            out.append(f"<h2>{_esc(line[3:])}</h2>")
        elif line.startswith("# "):
            out.append(f"<h1>{_esc(line[2:])}</h1>")
        elif line.startswith("- "):
            out.append(f"<li>{_esc(line[2:])}</li>")
        elif not line.strip():
            out.append("<br/>")
        else:
            text = _esc(line)
            text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
            out.append(f"<p>{text}</p>")
    _flush_table()
    if in_pre:
        out.append("</pre>")
    return "\n".join(out)


def build_preview_summary(result: dict[str, Any]) -> dict[str, Any]:
    result = result if isinstance(result, dict) else {}
    meta = _as_dict(result.get("metadata"))
    payload = _as_dict(result.get("payload"))
    v3_guard = _as_dict(payload.get("v3_guard") or meta.get("v3_guard"))
    ri = _as_dict(payload.get("research_intelligence") or meta.get("research_intelligence"))
    comp = _as_dict(ri.get("competitor_map"))
    diligence = _as_dict(payload.get("diligence_pack"))
    pricing_harvest = _as_dict(diligence.get("pricing_harvest"))
    canonical = _as_dict(payload.get("canonical_truth"))
    truth_meta = _as_dict(canonical.get("truth_metadata"))
    firewall = _as_dict(v3_guard.get("firewall") or payload.get("hallucination_firewall"))
    audit = _as_dict(payload.get("final_report_audit"))
    inv = _as_dict(audit.get("investor_readiness") or payload.get("investor_readiness"))
    return {
        "success": bool(result.get("success")),
        "topic": payload.get("topic") or meta.get("topic") or result.get("topic"),
        "industry": payload.get("industry") or meta.get("industry"),
        "geography": payload.get("geography") or meta.get("geography"),
        "report_score": meta.get("score") or meta.get("market_style_score"),
        "investor_ready": bool(payload.get("investor_ready") or audit.get("investor_ready")),
        "investor_score": inv.get("investor_ready_score") or inv.get("effective_report_score"),
        "section_average": inv.get("section_average"),
        "funding_audit_score": audit.get("market_style_score") or meta.get("score"),
        "evidence_count": int(ri.get("evidence_count") or len(diligence.get("citation_ledger") or [])),
        "competitor_count": int(
            comp.get("competitor_count")
            or diligence.get("live_competitor_count")
            or len(comp.get("competitor_matrix") or [])
        ),
        "pricing_verified_count": int(pricing_harvest.get("verified_count") or 0),
        "pricing_harvest_status": pricing_harvest.get("status") or "not_run",
        "v3_blocked": bool(v3_guard.get("blocked") or payload.get("v3_render_blocked")),
        "truth_confidence": v3_guard.get("confidence") or payload.get("report_confidence") or truth_meta.get("confidence"),
        "firewall_critical": int(firewall.get("critical_count") or 0),
        "firewall_warnings": int(firewall.get("warning_count") or 0),
        "runtime_sec": meta.get("elapsed_seconds") or result.get("runtime_sec"),
        "report_mode": payload.get("report_mode") or meta.get("report_mode"),
        "synthesis_engine": _as_dict(payload.get("synthesis_engine") or meta.get("synthesis_engine")).get("primary"),
        "serp_enabled": bool(_as_dict(diligence.get("serp_intelligence")).get("enabled")),
        "report_degraded": bool(payload.get("report_degraded") or diligence.get("report_degraded")),
        "degradation_reason": (
            payload.get("degradation_reason")
            or diligence.get("degradation_reason")
            or payload.get("report_degrade_reason")
            or diligence.get("report_degrade_reason")
        ),
        "report_degrade_reason": payload.get("report_degrade_reason") or diligence.get("report_degrade_reason"),
    }


def render_preview_html(result: dict[str, Any], *, title: str = "IIDATECH Research Preview") -> str:
    summary = build_preview_summary(result)
    meta = _as_dict(result.get("metadata"))
    payload = _as_dict(result.get("payload"))
    v3_md = (
        payload.get("report_v3_markdown")
        or meta.get("report_v3_markdown")
        or result.get("report")
        or "_No report_"
    )
    legacy_md = str(result.get("report") or "") if result.get("report") != v3_md else ""
    blocked = summary.get("v3_blocked")
    status = "BLOCKED" if blocked else ("OK" if summary.get("success") else "FAILED")
    status_color = "#b45309" if blocked else ("#15803d" if summary.get("success") else "#b91c1c")
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    truth = summary.get("truth_confidence")
    truth_display = f"{truth:.1f}" if isinstance(truth, (int, float)) else _esc(truth or "n/a")
    rendered = markdown_to_html_simple(v3_md)
    degrade_banner = ""
    if summary.get("report_degraded"):
        reason = _esc(
            summary.get("degradation_reason")
            or summary.get("report_degrade_reason")
            or "unknown"
        )
        degrade_banner = (
            '<p style="background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:.75rem 1rem;color:#92400e">'
            f"⚠ This report was generated with a partial data failure and may be incomplete. Reason: {reason}"
            "</p>"
        )
    legacy_tab = (
        '<button class="tab" onclick="showTab(\'panel-legacy\')">Legacy report</button>'
        if legacy_md
        else ""
    )
    legacy_panel = (
        f'<div id="panel-legacy" class="panel"><pre class="raw">{_esc(legacy_md)}</pre></div>'
        if legacy_md
        else ""
    )
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{_esc(title)}</title>
<style>
body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#f1f5f9;color:#0f172a;line-height:1.5}}
header{{background:linear-gradient(135deg,#0f172a,#1e3a5f);color:#fff;padding:1.25rem 1.5rem}}
header h1{{margin:0 0 .25rem;font-size:1.35rem}}header p{{margin:0;opacity:.85;font-size:.95rem}}
.wrap{{max-width:980px;margin:0 auto;padding:1rem 1.25rem 2rem}}
.badge{{display:inline-block;padding:.2rem .55rem;border-radius:999px;font-size:.8rem;font-weight:600}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:.65rem;margin:1rem 0}}
.metric{{background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:.7rem .85rem;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.metric span{{display:block;font-size:.72rem;color:#64748b;text-transform:uppercase;letter-spacing:.04em}}
.metric strong{{font-size:1.15rem}}
.tabs{{display:flex;gap:.5rem;margin:1rem 0 .5rem;flex-wrap:wrap}}
.tab{{padding:.45rem .9rem;border:1px solid #cbd5e1;background:#fff;border-radius:8px;cursor:pointer;font-size:.9rem}}
.tab.active{{background:#0f172a;color:#fff;border-color:#0f172a}}
.panel{{display:none;background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:1rem 1.1rem}}
.panel.active{{display:block}}
.md-table{{width:100%;border-collapse:collapse;font-size:.88rem;margin:.5rem 0}}
.md-table th,.md-table td{{border:1px solid #e2e8f0;padding:.4rem .55rem;text-align:left}}
.md-table th{{background:#f8fafc}}
pre.raw{{white-space:pre-wrap;font-size:.82rem;background:#f8fafc;padding:.75rem;border-radius:8px}}
.md-code{{background:#f8fafc;padding:.75rem;border-radius:8px;overflow:auto}}
h1,h2,h3{{margin:1rem 0 .5rem}}li{{margin:.25rem 0 .25rem 1.25rem}}
</style>
<script>
function showTab(id){{document.querySelectorAll('.panel').forEach(p=>p.classList.remove('active'));
document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
document.getElementById(id).classList.add('active');
event.target.classList.add('active');}}
</script></head><body>
<header><h1>{_esc(title)}</h1><p>{_esc(summary.get('topic'))} · {_esc(summary.get('industry'))} · {_esc(summary.get('geography'))}</p></header>
<div class="wrap">
<p><span class="badge" style="background:{status_color};color:#fff">{status}</span>
 · Generated {generated} · Runtime {_esc(summary.get('runtime_sec') or '?')}s</p>
{degrade_banner}
<div class="metrics">
<div class="metric"><span>Investor ready</span><strong>{'yes' if summary.get('investor_ready') else 'no'}</strong></div>
<div class="metric"><span>Investor score</span><strong>{_esc(summary.get('investor_score') or 'n/a')}</strong></div>
<div class="metric"><span>Section avg</span><strong>{_esc(summary.get('section_average') or 'n/a')}</strong></div>
<div class="metric"><span>Funding audit</span><strong>{_esc(summary.get('funding_audit_score') or 'n/a')}</strong></div>
<div class="metric"><span>Truth confidence</span><strong>{truth_display}</strong></div>
<div class="metric"><span>Evidence</span><strong>{summary.get('evidence_count',0)}</strong></div>
<div class="metric"><span>Competitors</span><strong>{summary.get('competitor_count',0)}</strong></div>
<div class="metric"><span>Pricing verified</span><strong>{summary.get('pricing_verified_count',0)}</strong></div>
<div class="metric"><span>Firewall</span><strong>{summary.get('firewall_critical',0)} crit / {summary.get('firewall_warnings',0)} warn</strong></div>
<div class="metric"><span>Engine</span><strong>{_esc(summary.get('synthesis_engine') or 'n/a')}</strong></div>
<div class="metric"><span>SERP live</span><strong>{'yes' if summary.get('serp_enabled') else 'no'}</strong></div>
<div class="metric"><span>Pricing harvest</span><strong>{_esc(summary.get('pricing_harvest_status'))}</strong></div>
</div>
<div class="tabs">
<button class="tab active" onclick="showTab('panel-v3')">V3 Report</button>
<button class="tab" onclick="showTab('panel-raw')">Raw markdown</button>
{legacy_tab}
</div>
<div id="panel-v3" class="panel active"><div class="md-body">{rendered}</div></div>
<div id="panel-raw" class="panel"><pre class="raw">{_esc(v3_md)}</pre></div>
{legacy_panel}
</div></body></html>"""


def export_preview_files(result: dict[str, Any], out_dir: str) -> dict[str, str]:
    from pathlib import Path

    root = Path(out_dir)
    root.mkdir(parents=True, exist_ok=True)
    summary = build_preview_summary(result)
    html_path = root / "report_preview.html"
    json_path = root / "report_preview.json"
    md_path = root / "report_preview.md"
    html_path.write_text(render_preview_html(result), encoding="utf-8")
    payload = _as_dict(result.get("payload"))
    v3_md = payload.get("report_v3_markdown") or result.get("report") or ""
    md_path.write_text(str(v3_md), encoding="utf-8")
    json_path.write_text(
        json.dumps({"summary": summary, "result_success": result.get("success")}, indent=2),
        encoding="utf-8",
    )
    return {"html": str(html_path), "json": str(json_path), "markdown": str(md_path)}
