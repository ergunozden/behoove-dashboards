#!/usr/bin/env python3
"""One-time local OAuth flow. Generates a refresh token for the dashboard pipeline.

Run this once on your laptop:

  pip install -r requirements.txt
  python scripts/get_refresh_token.py /path/to/client_secret.json

It opens a browser, you log in as ergun@behoovestudio.com, grant access, and the
refresh token is printed at the end. Paste that token + the client_id + client_secret
into GitHub Secrets:

  GOOGLE_OAUTH_CLIENT_ID
  GOOGLE_OAUTH_CLIENT_SECRET
  GOOGLE_OAUTH_REFRESH_TOKEN

After that, GitHub Actions (and the fetchers in this repo) can hit GA4 + GSC on
your behalf without any service-account permission dance.

The client_secret.json comes from:
  https://console.cloud.google.com/apis/credentials
  -> Create Credentials -> OAuth client ID -> Application type: Desktop app
  -> Download JSON
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",
    "https://www.googleapis.com/auth/webmasters.readonly",
]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: get_refresh_token.py /path/to/client_secret.json", file=sys.stderr)
        return 2

    secret_path = Path(sys.argv[1]).expanduser().resolve()
    if not secret_path.exists():
        print(f"error: not found: {secret_path}", file=sys.stderr)
        return 2

    flow = InstalledAppFlow.from_client_secrets_file(str(secret_path), SCOPES)
    # access_type=offline + prompt=consent guarantees a refresh token comes back.
    creds = flow.run_local_server(
        port=0,
        access_type="offline",
        prompt="consent",
        open_browser=True,
    )

    with open(secret_path) as f:
        secret = json.load(f)
    body = secret.get("installed") or secret.get("web") or {}
    client_id = body.get("client_id", "")
    client_secret = body.get("client_secret", "")

    print()
    print("=" * 72)
    print("SUCCESS. Add these three values to your GitHub repo secrets:")
    print("=" * 72)
    print(f"GOOGLE_OAUTH_CLIENT_ID")
    print(f"  {client_id}")
    print(f"GOOGLE_OAUTH_CLIENT_SECRET")
    print(f"  {client_secret}")
    print(f"GOOGLE_OAUTH_REFRESH_TOKEN")
    print(f"  {creds.refresh_token}")
    print("=" * 72)
    print("Refresh tokens for installed apps do not expire unless you revoke them.")
    print("Anyone with all three values can read your GA4 + GSC. Treat as a password.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
