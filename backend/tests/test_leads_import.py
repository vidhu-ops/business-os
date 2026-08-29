from backend.services.lead_import import parse_lead_sheet
from backend.services.page_taxonomy import classify_page, normalize_path


def test_normalize_demo_path():
    assert "demo_readonly" in normalize_path("/app/research", "https://x.test/app/research?project=demo_readonly")
    classified = classify_page("/app/research", "https://x.test/app/research?project=demo_readonly")
    assert classified["area"] == "demo"
    assert classified["part"] == "Research"


def test_parse_csv_sheet():
    rows = parse_lead_sheet(b"Email,Full Name,Company\none@test.com,One,Acme\n", "leads.csv")
    assert rows == [{"email": "one@test.com", "name": "One", "company": "Acme"}]
