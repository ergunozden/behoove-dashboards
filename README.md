# behoove-dashboards

Public, unlisted, free, Claude-updatable client dashboards.

- **Hosting:** Cloudflare Pages (auto-deploys on push to `main`)
- **Domain:** `dashboards.behoovestudio.com` (CNAME on Cloudflare)
- **Refresh:** GitHub Actions cron, Mondays 06:00 UTC
- **Data:** static JSON committed by the workflow, rendered client-side

## Layout

```
dashboards/
  index.html                -- root landing (link list)
  awarion/
    index.html              -- Chart.js dashboard
    data.json               -- written by scripts/, committed by Actions
scripts/
  fetch_ga4.py              -- Analytics Data API v1
  fetch_gsc.py              -- Search Console API
  run_all.sh                -- runs both, driven by env
.github/workflows/
  refresh.yml               -- weekly cron + manual dispatch
```

## One-time setup (Ergun)

### 1. Create GitHub repo

```
cd /root/repos/behoove-dashboards
gh repo create ergunozden/behoove-dashboards --public --source=. --remote=origin
git add .
git commit -m "init: dashboards scaffold + awarion v0"
git push -u origin main
```

### 2. Create OAuth client (one time)

We use OAuth user credentials, not a service account. Service-account emails are
rejected by some Google Workspace tenants (the "This email doesn't match a Google
Account" error). OAuth uses your existing access, so no admin grants are needed.

1. https://console.cloud.google.com - pick or create a project (any project)
2. Enable APIs:
   - Google Analytics Data API
   - Google Search Console API
3. APIs and Services - OAuth consent screen - configure as External, app name
   "Behoove Dashboards", add yourself as a Test user. (No need to publish.)
4. APIs and Services - Credentials - Create credentials - OAuth client ID
   - Application type: **Desktop app**
   - Name: `behoove-dashboards`
5. Download the JSON. Save somewhere safe (do NOT commit it).

### 3. Generate the refresh token (one time)

On your laptop:

```
cd /root/repos/behoove-dashboards
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/get_refresh_token.py ~/Downloads/client_secret_*.json
```

A browser opens. Log in as `ergun@behoovestudio.com`, grant the requested scopes.
The script prints three values: client_id, client_secret, refresh_token.

### 4. Get the property identifiers

- **GA4 property ID:** numeric, in GA4 - Admin - Property Settings (e.g. `412345678`).
- **GSC site URL:** `sc-domain:behoovestudio.com` if Domain property, or
  `https://behoovestudio.com/` if URL-prefix.

### 5. Add GitHub repo secrets

`gh secret set` or Settings - Secrets - Actions:

| Secret | Value |
|---|---|
| `GOOGLE_OAUTH_CLIENT_ID` | printed by step 3 |
| `GOOGLE_OAUTH_CLIENT_SECRET` | printed by step 3 |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | printed by step 3 |
| `BEHOOVE_GA4_PROPERTY_ID` | e.g. `412345678` |
| `BEHOOVE_GSC_SITE_URL` | e.g. `sc-domain:behoovestudio.com` |

Later, for Awarion or other clients: add `AWARION_GA4_PROPERTY_ID` and
`AWARION_GSC_SITE_URL` (the OAuth secrets are shared across all clients).

### 6. Manually trigger first run

```
gh workflow run refresh-dashboards
gh run watch
```

### 7. Connect Cloudflare Pages

1. Cloudflare dashboard - Workers and Pages - Create - Pages - Connect to Git
2. Pick `behoove-dashboards`
3. Build settings:
   - Framework preset: None
   - Build command: (leave empty)
   - Build output directory: `dashboards`
4. Deploy. Note the `*.pages.dev` URL.
5. Custom domains - add `dashboards.behoovestudio.com`. Cloudflare auto-creates the CNAME.

### 8. Share with Alp

URL: `https://dashboards.behoovestudio.com/awarion/`

Optional: rename the path to a hard-to-guess slug if you want extra opacity (e.g. `awarion-h3k9/`). Site-wide robots meta is already `noindex,nofollow`.

## Local development

```
cd /root/repos/behoove-dashboards
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export GOOGLE_APPLICATION_CREDENTIALS=./sa.json
export CLIENT=awarion
export GA4_PROPERTY_ID=412345678
export GSC_SITE_URL='sc-domain:awarion.com'
bash scripts/run_all.sh

# Preview locally
python -m http.server -d dashboards 8080
# open http://localhost:8080/awarion/
```

## Adding a new client

1. Duplicate `dashboards/awarion/` to `dashboards/<slug>/`. Adjust the `<title>` in `index.html`.
2. Add a job to `.github/workflows/refresh.yml` mirroring the `awarion` job.
3. Add `<SLUG>_GA4_PROPERTY_ID` and `<SLUG>_GSC_SITE_URL` secrets.
4. Link the new dashboard from `dashboards/index.html`.

## Why not Looker Studio / Evidence.dev / Notion

- Looker Studio: hard for Claude to edit.
- Evidence.dev: great, but heavier dev loop. Static HTML + Chart.js covers the SEO use case with zero build step.
- Notion: chart support is weak.

Static-files-in-a-repo is the most Claude-friendly path. Trivial to swap to Evidence later by re-pointing Cloudflare Pages at a different output dir.
