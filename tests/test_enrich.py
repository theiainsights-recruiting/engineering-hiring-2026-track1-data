"""Tests for the enrichment stage.

Stage as tests/test_enrich.py on the PR branch.
"""

from unittest.mock import Mock

import pandas as pd
import pytest
import requests

from pipelines.enrich import process_batch, run


def echo_session():
    """A session whose post() echoes back one result per document sent."""
    session = Mock()

    def post(url, json, timeout):
        resp = Mock()
        resp.raise_for_status.return_value = None
        resp.json.return_value = {
            "results": [
                {"company_id": d["company_id"], "keywords": ["kw"]}
                for d in json["documents"]
            ]
        }
        return resp

    session.post = post
    return session


def test_happy_path(tmp_path, monkeypatch):
    docs = pd.DataFrame(
        {"company_id": [f"C{i:03d}" for i in range(25)], "text": ["text"] * 25}
    )
    input_path = tmp_path / "docs.parquet"
    docs.to_parquet(input_path, index=False)
    output_root = tmp_path / "keywords"
    output_root.mkdir()

    monkeypatch.setattr("pipelines.enrich.requests.Session", echo_session)
    run(str(input_path), str(output_root), "2026-08-01")

    out = pd.read_parquet(output_root / "date=2026-08-01" / "part.parquet")
    assert len(out) == len(docs)
    assert set(out["company_id"]) == set(docs["company_id"])


def test_batch_fails_all_attempts(monkeypatch):
    monkeypatch.setattr("pipelines.enrich.time.sleep", lambda s: None)
    session = Mock()
    session.post = Mock(side_effect=requests.ConnectionError("boom"))
    results: list[dict] = []

    with pytest.raises(RuntimeError):
        process_batch([{"company_id": "C001", "text": "text"}], session, results)

    assert results == []
