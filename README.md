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

### 2. Create Google Cloud service account

Once - reused for every client.

1. https://console.cloud.google.com - create or pick a project (e.g. `behoove-dashboards`)
2. Enable APIs:
   - Google Analytics Data API
   - Google Search Console API
3. IAM and Admin - Service Accounts - Create
   - Name: `dashboards-reader`
   - Role: none (access is granted per-property)
4. Open the SA - Keys - Add key - JSON - download
5. Save the JSON locally (do NOT commit it). You'll paste its contents into GitHub Secrets next.

### 3. Share properties with the SA email

The SA has an email like `dashboards-reader@<project>.iam.gserviceaccount.com`.

- **GA4:** GA4 property - Property Settings - Property Access Management - Add user with `Viewer` role.
- **GSC:** Search Console - Settings - Users and permissions - Add user, `Restricted` role.

### 4. Get the property identifiers

- **GA4 property ID:** numeric, in GA4 - Admin - Property Settings (e.g. `412345678`).
- **GSC site URL:** `sc-domain:awarion.com` if you use a Domain property; `https://awarion.com/` if URL-prefix. Use whichever exists.

### 5. Add GitHub repo secrets

`gh secret set` or web UI - Settings - Secrets - Actions:

| Secret | Value |
|---|---|
| `GCP_SA_KEY` | Full contents of the downloaded SA JSON |
| `AWARION_GA4_PROPERTY_ID` | e.g. `412345678` |
| `AWARION_GSC_SITE_URL` | e.g. `sc-domain:awarion.com` |

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
