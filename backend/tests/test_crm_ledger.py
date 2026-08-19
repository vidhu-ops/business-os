from __future__ import annotations

from backend.routers.admin import _ledger_summary


def test_ledger_summary_uses_newest_first():
    record = {
        "credit_ledger": [
            {"action": "mentor", "amount": 1, "at": "2026-08-20T12:00:00Z"},
            {"action": "employee_work", "amount": 1, "at": "2026-08-20T11:00:00Z"},
            {"action": "admin_grant", "amount": -100, "at": "2026-08-19T10:00:00Z"},
        ]
    }
    rows = _ledger_summary(record)
    assert rows[0]["action"] == "mentor"
    assert rows[0]["direction"] == "spend"
    assert rows[2]["direction"] == "grant"