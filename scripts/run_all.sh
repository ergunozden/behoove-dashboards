#!/usr/bin/env bash
# Pull all data for a single client. Safe to call locally or from CI.
#
# Required env:
#   CLIENT                          -- e.g. "behoove"
#   GOOGLE_OAUTH_CLIENT_ID
#   GOOGLE_OAUTH_CLIENT_SECRET
#   GOOGLE_OAUTH_REFRESH_TOKEN
# Optional env (per source; skip silently when blank):
#   GA4_PROPERTY_ID                 -- numeric GA4 property ID
#   GSC_SITE_URL                    -- e.g. "sc-domain:behoovestudio.com"
set -euo pipefail

: "${CLIENT:?CLIENT env required}"
: "${GOOGLE_OAUTH_CLIENT_ID:?GOOGLE_OAUTH_CLIENT_ID env required}"
: "${GOOGLE_OAUTH_CLIENT_SECRET:?GOOGLE_OAUTH_CLIENT_SECRET env required}"
: "${GOOGLE_OAUTH_REFRESH_TOKEN:?GOOGLE_OAUTH_REFRESH_TOKEN env required}"

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
