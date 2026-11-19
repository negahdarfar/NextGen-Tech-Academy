import json
from nextgen_academy.evidence_audit import audit_storyboard_claims, enrich_sources, write_evidence_audit


def test_claim_audit_reports_overlap_without_claiming_truth():
    sources = [{
        "id": "s1", "title": "Robotics research report", "publisher": "Lab",
        "url": "https://example.org/report", "summary": "Robotics systems improve factory automation.",
        "audit": {"status": "reachable", "page_title": "Factory robotics automation",
                  "description": "", "extracted_text": "Robotics systems automate manufacturing."},
    }]
    storyboard = {"topic": "Robotics", "claims": [
        {"text": "Robotics systems automate factory manufacturing", "source_ids": ["s1"]}
    ]}
    report = audit_storyboard_claims(storyboard, sources)
    assert report["is_fact_checked"] is False
    assert report["human_review_required"] is True
    assert report["claims"][0]["sources"][0]["term_overlap_ratio"] > 0
    assert report["claims"][0]["sources"][0]["interpretation"] == "textual_overlap_only_not_proof"


def test_unknown_source_id_is_visible():
    report = audit_storyboard_claims(
        {"claims": [{"text": "A factual statement", "source_ids": ["missing"]}]}, []
    )
    assert report["claims"][0]["sources"][0]["status"] == "unknown_source_id"


def test_enrich_sources_records_fetch_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError("test timeout")
    monkeypatch.setattr("nextgen_academy.evidence_audit._fetch_page", fail)
    result = enrich_sources([{"id": "s1", "url": "https://example.org"}])
    assert result[0]["audit"]["status"] == "unavailable"
    assert "TimeoutError" in result[0]["audit"]["error"]


def test_write_evidence_audit_creates_json(tmp_path):
    path = write_evidence_audit({"topic": "Test", "claims": []}, [], tmp_path / "audit.json")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["topic"] == "Test"
    assert data["human_review_required"] is True
