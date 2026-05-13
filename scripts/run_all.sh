#!/usr/bin/env bash
# Pull all data for a single client. Driven by env vars; safe to call locally or from CI.
#
# Required env:
#   CLIENT                  -- e.g. "awarion"
#   GOOGLE_APPLICATION_CREDENTIALS -- path to service-account JSON
#   GA4_PROPERTY_ID         -- numeric GA4 property ID
#   GSC_SITE_URL            -- e.g. "sc-domain:awarion.com" or "https://awarion.com/"
set -euo pipefail

: "${CLIENT:?CLIENT env required}"
: "${GOOGLE_APPLICATION_CREDENTIALS:?GOOGLE_APPLICATION_CREDENTIALS env required}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -n "${GA4_PROPERTY_ID:-}" ]]; then
  python scripts/fetch_ga4.py "$CLIENT"
else
  echo "skip: GA4_PROPERTY_ID not set"
fi

if [[ -n "${GSC_SITE_URL:-}" ]]; then
  python scripts/fetch_gsc.py "$CLIENT"
else
  echo "skip: GSC_SITE_URL not set"
fi

echo "done: $CLIENT"
