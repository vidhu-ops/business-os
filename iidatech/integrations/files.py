"""Document generation: proposals, contracts, SOPs."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def write_document(out_dir: Path, *, filename: str, title: str, sections: list[str]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / filename
    body = [f"# {title}", "", f"_Generated {datetime.now(timezone.utc).isoformat()}_", ""]
    for i, section in enumerate(sections, 1):
        body.append(f"## Section {i}")
        body.append(str(section))
        body.append("")
    path.write_text("\n".join(body), encoding="utf-8")
    return {"path": str(path), "title": title, "sections": len(sections)}


def write_proposal(out_dir: Path, *, account_name: str, offer: str) -> dict[str, Any]:
    return write_document(
        out_dir,
        filename=f"proposal_{_stamp()}.md",
        title=f"Proposal for {account_name}",
        sections=[
            f"Executive summary for {account_name}.",
            f"Offer: {offer}",
            "Implementation timeline and success metrics.",
            "Pricing and next steps.",
        ],
    )


def write_contract(out_dir: Path, *, party: str, terms: str) -> dict[str, Any]:
    return write_document(
        out_dir,
        filename=f"contract_{_stamp()}.md",
        title=f"Service Agreement - {party}",
        sections=["Parties", terms or "Standard IIDATECH service terms.", "Signatures"],
    )