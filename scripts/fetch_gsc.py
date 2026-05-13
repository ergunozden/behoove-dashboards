#!/usr/bin/env python3
"""Fetch Search Console metrics and merge into dashboards/<client>/data.json.

Usage:
  GSC_SITE_URL='sc-domain:awarion.com' GOOGLE_APPLICATION_CREDENTIALS=./sa.json \
    python scripts/fetch_gsc.py awarion

GSC_SITE_URL accepts either a URL-prefix property (e.g. 'https://awarion.com/')
or a Domain property prefixed 'sc-domain:awarion.com'.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def client():
    creds = service_account.Credentials.from_service_account_file(
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPES
    )
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def query(svc, site: str, start: str, end: str, dimensions: list[str], row_limit: int = 25) -> list[dict]:
    body = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": row_limit,
    }
    resp = svc.searchanalytics().query(siteUrl=site, body=body).execute()
    return resp.get("rows", [])


def fetch(site: str) -> dict:
    svc = client()
    today = date.today()
    # GSC data has 2-3 day lag; use a 28-day window ending 3 days ago.
    end = today - timedelta(days=3)
    start = end - timedelta(days=27)
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=27)

    def totals(s: str, e: str) -> dict:
        rows = query(svc, site, s, e, dimensions=[], row_limit=1)
        if not rows:
            return {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
        r = rows[0]
        return {
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }

    current = totals(start.isoformat(), end.isoformat())
    prior = totals(prev_start.isoformat(), prev_end.isoformat())

    daily_rows = query(svc, site, start.isoformat(), end.isoformat(), ["date"], 100)
    daily = [
        {
            "date": r["keys"][0],
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }
        for r in daily_rows
    ]
    daily.sort(key=lambda x: x["date"])

    top_queries = [
        {
            "query": r["keys"][0],
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }
        for r in query(svc, site, start.isoformat(), end.isoformat(), ["query"], 25)
    ]

    top_pages = [
        {
            "page": r["keys"][0],
            "clicks": int(r.get("clicks", 0)),
            "impressions": int(r.get("impressions", 0)),
            "ctr": float(r.get("ctr", 0)),
            "position": float(r.get("position", 0)),
        }
        for r in query(svc, site, start.isoformat(), end.isoformat(), ["page"], 25)
    ]

    return {
        "site": site,
        "window": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "priorStart": prev_start.isoformat(),
            "priorEnd": prev_end.isoformat(),
        },
        "totals": {"current": current, "prior": prior},
        "daily": daily,
        "topQueries": top_queries,
        "topPages": top_pages,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_gsc.py <client-slug>", file=sys.stderr)
        return 2
    client_slug = sys.argv[1]
    site = os.environ.get("GSC_SITE_URL")
    if not site:
        print("error: GSC_SITE_URL env not set", file=sys.stderr)
        return 2

    gsc = fetch(site)

    out_dir = ROOT / "dashboards" / client_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.json"

    existing: dict = {}
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
        except json.JSONDecodeError:
            existing = {}

    existing["gsc"] = gsc
    existing["client"] = client_slug
    existing["generatedAt"] = date.today().isoformat()

    out_path.write_text(json.dumps(existing, indent=2) + "\n")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
