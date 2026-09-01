"""Nightly keyword enrichment for newly ingested company documents.

Sends batches of document text to the vendor extraction API and appends
the results as a new dated partition. Runs as the final stage of the
nightly ingest DAG.
"""

import glob
import logging
import os
import random
import time

import pandas as pd
import requests

logger = logging.getLogger(__name__)

API_URL = "https://api.vendor.invalid/v1/extract"
SUB_BATCH_SIZE = 10  # vendor hard limit per request
MAX_ATTEMPTS = 3


def already_enriched(output_root: str) -> set[str]:
    """Company ids that already have keywords in any previous partition."""
    seen: set[str] = set()
    for path in glob.glob(os.path.join(output_root, "date=*", "part.parquet")):
        ids = pd.read_parquet(path, columns=["company_id"])["company_id"]
        seen.update(ids)
    return seen


def post_sub_batch(rows: list[dict], session: requests.Session) -> list[dict]:
    resp = session.post(API_URL, json={"documents": rows}, timeout=30)
    resp.raise_for_status()
    return resp.json()["results"]


def process_batch(
    batch: list[dict], session: requests.Session, results: list[dict]
) -> None:
    """Send one batch, split into vendor-sized sub-batches, with retry."""
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            for i in range(0, len(batch), SUB_BATCH_SIZE):
                results.extend(post_sub_batch(batch[i : i + SUB_BATCH_SIZE], session))
            return
        except requests.RequestException as exc:
            last_error = exc
            delay = 2**attempt + random.random()
            logger.warning(
                "batch failed on attempt %d/%d, retrying in %.1fs",
                attempt + 1,
                MAX_ATTEMPTS,
                delay,
            )
            time.sleep(delay)
    raise RuntimeError(
        f"batch of {len(batch)} documents failed after {MAX_ATTEMPTS} attempts"
    ) from last_error


def run(
    input_path: str, output_root: str, run_date: str, batch_size: int = 200
) -> None:
    df = pd.read_parquet(input_path)
    skip = already_enriched(output_root)
    todo = df[~df["company_id"].isin(skip)]
    logger.info("enriching %d of %d documents", len(todo), len(df))

    session = requests.Session()
    results: list[dict] = []
    batch: list[dict] = []
    for row in todo.itertuples():
        batch.append({"company_id": row.company_id, "text": row.text})
        if len(batch) == batch_size:
            process_batch(batch, session, results)
            batch = []
    if batch:
        process_batch(batch, session, results)

    out_dir = os.path.join(output_root, f"date={run_date}")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "part.parquet")
    tmp_path = out_path + ".tmp"
    pd.DataFrame(results).to_parquet(tmp_path, index=False)
    os.replace(tmp_path, out_path)
    logger.info("wrote %d rows to %s", len(results), out_path)
