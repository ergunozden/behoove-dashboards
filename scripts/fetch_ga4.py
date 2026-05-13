#!/usr/bin/env python3
"""Fetch GA4 metrics and write to dashboards/<client>/data.json.

Usage:
  GA4_PROPERTY_ID=123456789 GOOGLE_APPLICATION_CREDENTIALS=./sa.json \
    python scripts/fetch_ga4.py awarion

Reads:  GOOGLE_APPLICATION_CREDENTIALS (path to service-account JSON)
        GA4_PROPERTY_ID                (numeric GA4 property ID)
Writes: dashboards/<client>/data.json -- merged with any existing GSC block.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

ROOT = Path(__file__).resolve().parents[1]


def fetch(property_id: str) -> dict:
    client = BetaAnalyticsDataClient()
    today = date.today()
    start = today - timedelta(days=28)
    prev_start = start - timedelta(days=28)
    prev_end = start - timedelta(days=1)

    # Daily series: 28d window, sessions + users + engaged sessions.
    daily = client.run_report(
        RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="date")],
            metrics=[
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="engagedSessions"),
                Metric(name="averageSessionDuration"),
            ],
            date_ranges=[DateRange(start_date=start.isoformat(), end_date=today.isoformat())],
        )
    )

    series = []
    for row in daily.rows:
        d = row.dimension_values[0].value  # YYYYMMDD
        series.append(
            {
                "date": f"{d[:4]}-{d[4:6]}-{d[6:]}",
                "sessions": int(row.metric_values[0].value),
                "users": int(row.metric_values[1].value),
                "engagedSessions": int(row.metric_values[2].value),
                "avgSessionDuration": float(row.metric_values[3].value or 0),
            }
        )
    series.sort(key=lambda r: r["date"])

    # Totals current vs prior 28d.
    def totals(s: str, e: str) -> dict:
        r = client.run_report(
            RunReportRequest(
                property=f"properties/{property_id}",
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="engagedSessions"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                ],
                date_ranges=[DateRange(start_date=s, end_date=e)],
            )
        )
        row = r.rows[0] if r.rows else None
        if row is None:
            return {"sessions": 0, "users": 0, "engagedSessions": 0, "pageviews": 0, "bounceRate": 0.0}
        return {
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
            "engagedSessions": int(row.metric_values[2].value),
            "pageviews": int(row.metric_values[3].value),
            "bounceRate": float(row.metric_values[4].value or 0),
        }

    current = totals(start.isoformat(), today.isoformat())
    prior = totals(prev_start.isoformat(), prev_end.isoformat())

    # Top pages last 28d.
    pages = client.run_report(
        RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="pagePath")],
            metrics=[Metric(name="screenPageViews"), Metric(name="sessions")],
            date_ranges=[DateRange(start_date=start.isoformat(), end_date=today.isoformat())],
            limit=20,
        )
    )
    top_pages = [
        {
            "path": row.dimension_values[0].value,
            "pageviews": int(row.metric_values[0].value),
            "sessions": int(row.metric_values[1].value),
        }
        for row in pages.rows
    ]

    # Sources last 28d.
    sources = client.run_report(
        RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[Dimension(name="sessionSource"), Dimension(name="sessionMedium")],
            metrics=[Metric(name="sessions"), Metric(name="totalUsers")],
            date_ranges=[DateRange(start_date=start.isoformat(), end_date=today.isoformat())],
            limit=15,
        )
    )
    top_sources = [
        {
            "source": row.dimension_values[0].value,
            "medium": row.dimension_values[1].value,
            "sessions": int(row.metric_values[0].value),
            "users": int(row.metric_values[1].value),
        }
        for row in sources.rows
    ]

    return {
        "window": {
            "start": start.isoformat(),
            "end": today.isoformat(),
            "priorStart": prev_start.isoformat(),
            "priorEnd": prev_end.isoformat(),
        },
        "totals": {"current": current, "prior": prior},
        "daily": series,
        "topPages": top_pages,
        "topSources": top_sources,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_ga4.py <client-slug>", file=sys.stderr)
        return 2
    client_slug = sys.argv[1]
    property_id = os.environ.get("GA4_PROPERTY_ID")
    if not property_id:
        print("error: GA4_PROPERTY_ID env not set", file=sys.stderr)
        return 2

    ga4 = fetch(property_id)

    out_dir = ROOT / "dashboards" / client_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "data.json"

    existing: dict = {}
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text())
        except json.JSONDecodeError:
            existing = {}

    existing["ga4"] = ga4
    existing["client"] = client_slug
    existing["generatedAt"] = date.today().isoformat()

    out_path.write_text(json.dumps(existing, indent=2) + "\n")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
