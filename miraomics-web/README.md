# Miraomics website

A product-first rebuild of [miraomics.bio](https://www.miraomics.bio/) — a fast,
static marketing site in the MiraTyper design language, plus the AWS plumbing to
run it on a modern, low-cost, CI/CD-driven stack instead of a managed
WordPress/Wix host.

```
miraomics-web/
├── site/                 Astro + Tailwind static site (marketing + dashboard)
│   ├── src/pages/        Home, MiraTyper, Services, About, Contact, 404
│   ├── src/pages/lp/     Landing-page renderer (one page per content file)
│   ├── src/pages/dashboard/  Internal dashboard (Cognito-gated)
│   ├── src/content/landing/  Markdown landing pages (drop-in)
│   ├── src/components/   Nav, Footer, Hero pieces, ContactForm, ...
│   └── src/lib/          site config, attribution, auth (PKCE)
├── infra/
│   ├── terraform/        Root + modules (static-site, app-api, auth, github-oidc)
│   └── lambda/           submit-form, track, dashboard-api (Node ESM, no deps)
└── (CI lives in repo-root .github/workflows/web-*.yml)
```

## How this maps to the request

| # | Requirement | Where it lives |
|---|-------------|----------------|
| 1 | Redesign in the MiraTyper design language, new menu bar | `site/tailwind.config.mjs` + `src/styles/global.css` (design tokens: deep-navy canvas, teal→sky accent, Inter); `src/components/Nav.astro` is a product-first, sticky, responsive nav |
| 2 | Emphasize MiraTyper (product), services secondary | `src/pages/index.astro` leads with the product; services are a single secondary section. Dedicated `src/pages/miratyper.astro`; `services.astro` framed as "backs the platform" |
| 3 | CI/CD + Terraform instead of managed Wix/WordPress | `infra/terraform/` (S3 + CloudFront + Route53 + ACM); `.github/workflows/web-terraform.yml` (plan/apply via OIDC) and `web-deploy.yml` (build + S3 sync + CF invalidation) |
| 4 | Low-cost form handling (Lambda + S3) | `infra/lambda/submit-form` → API Gateway HTTP API → DynamoDB + SES; `src/components/ContactForm.astro` posts JSON |
| 5 | Attribute inbound traffic | `src/lib/attribution.ts` captures UTM + click-ids (first/last touch), beacons pageviews to `infra/lambda/track`; attribution rides along on every lead |
| 6 | Internal dashboard | `src/pages/dashboard/` reads KPIs, attribution breakdown and recent leads from `infra/lambda/dashboard-api` |
| 7 | Access control for a few people | Cognito Hosted UI (OAuth2 + PKCE), admin-create-only user pool, JWT authorizer on the dashboard API — `infra/terraform/modules/auth` |
| 8 | Easy landing pages for ads/workshops | `src/content/landing/*.md` → auto-published at `/lp/<slug>` via `src/pages/lp/[...slug].astro`. See `docs/ADDING_LANDING_PAGES.md` |

## Architecture

```
                 ┌──────────────┐   build    ┌─────────────┐
   git push ───▶ │ GitHub Actions│ ─────────▶ │  S3 (site)  │
                 │  (OIDC→AWS)   │  tf apply  └──────┬──────┘
                 └──────────────┘                    │ OAC
                                                ┌────▼─────┐   HTTPS
   visitor ────────────────────────────────────▶ CloudFront│◀─────── www / apex
                                                └────┬─────┘
        forms / pageview beacons / dashboard XHR     │
                       ▼                              ▼
              ┌─────────────────┐            (static HTML/CSS/JS)
              │ API Gateway (HTTP)│
              │  /submit  /track  │──▶ Lambda ──▶ DynamoDB (leads + pageviews)
              │  /admin/* (JWT)   │            └─▶ SES (lead email)
              └────────┬──────────┘
                       │ JWT authorizer
                  ┌────▼─────┐
                  │ Cognito  │  Hosted UI (PKCE) for the dashboard
                  └──────────┘
```

Everything is serverless and pay-per-use. Idle cost is dominated by Route53
(~$0.50/zone/mo) and is otherwise near zero at low traffic; see "Cost" below.

## Local development

```bash
cd miraomics-web/site
npm install
cp .env.example .env       # fill PUBLIC_* (or leave blank — forms no-op gracefully)
npm run dev                # http://localhost:4321
npm run build              # static output in ./dist
```

The site builds and runs with no backend; form posts and the dashboard simply
won't reach an API until `PUBLIC_API_BASE_URL` / `PUBLIC_COGNITO_*` are set.

## Deploy (first time)

Prerequisites: an AWS account, a Route53 hosted zone for `miraomics.bio` (for
custom domains + TLS), and the GitHub repo.

1. **Bootstrap remote state** (one-time) — see the commands in
   `infra/terraform/backend.tf`.

2. **Configure variables**
   ```bash
   cd miraomics-web/infra/terraform
   cp terraform.tfvars.example terraform.tfvars   # set zone id, emails, admins
   ```

3. **Apply** (locally for the first run, since CI needs the role this creates)
   ```bash
   terraform init
   terraform apply
   ```

4. **Wire CI** — copy outputs into GitHub repo **Variables**
   (Settings → Secrets and variables → Actions → Variables):
   ```bash
   terraform output     # shows everything below
   ```
   | GitHub Variable | Terraform output |
   |---|---|
   | `AWS_DEPLOY_ROLE_ARN` | `github_actions_role_arn` |
   | `AWS_REGION` | (your region, e.g. us-east-1) |
   | `SITE_BUCKET` | `site_bucket` |
   | `CLOUDFRONT_DISTRIBUTION_ID` | `cloudfront_distribution_id` |
   | `PUBLIC_SITE_URL` | `site_url` |
   | `PUBLIC_API_BASE_URL` | `public_api_base_url` |
   | `PUBLIC_COGNITO_DOMAIN` | `public_cognito_domain` |
   | `PUBLIC_COGNITO_CLIENT_ID` | `public_cognito_client_id` |
   | `PUBLIC_COGNITO_REGION` | `public_cognito_region` |
   | `PUBLIC_DASHBOARD_REDIRECT_URI` | `public_dashboard_redirect_uri` |

5. **Push to `main`** — `web-deploy` builds and publishes the site;
   `web-terraform` keeps infra (and Lambda code) in sync. Subsequent changes
   deploy automatically.

After that, day-to-day is just: open a PR (gets a build check + a plan comment),
merge, done.

## Adding a landing page (ads / workshops)

Drop a Markdown file in `site/src/content/landing/` — it's live at `/lp/<slug>`
with a lead-capture form wired to attribution. Full guide:
[`docs/ADDING_LANDING_PAGES.md`](docs/ADDING_LANDING_PAGES.md).

## The dashboard

`/dashboard` is excluded from search engines and gated by Cognito. Admins are
seeded from `admin_emails` in `terraform.tfvars` (Cognito emails each a
temporary password). Sign-in is the standard Cognito Hosted UI; the SPA uses
OAuth2 Authorization Code + PKCE and calls the JWT-authorized `/admin/*` API.

## Cost (order of magnitude, low traffic)

| Service | Driver | ~Monthly |
|---|---|---|
| Route53 | 1 hosted zone | $0.50 |
| S3 + CloudFront | a few GB transfer | < $1 |
| Lambda + API Gateway | thousands of requests | ~$0 (free-tier-ish) |
| DynamoDB | on-demand, small | ~$0 |
| Cognito | < 50 MAU | $0 (free tier) |
| SES | hundreds of emails | < $0.10 |

Realistically a few dollars a month until traffic grows — versus a managed
site-builder subscription.

## Migrating off WordPress/Wix

See [`docs/MIGRATION.md`](docs/MIGRATION.md) for DNS cutover, content parity, and
redirect notes.

## Notes / decisions

- **Stack:** Astro (static) + Tailwind. Zero JS shipped except the small
  attribution + form + dashboard scripts. Fast, cheap, easy to template.
- **Single DynamoDB table** (`pk`/`sk`) holds both leads and pageviews; pageview
  rows carry a TTL so storage stays small. Aggregation happens in the dashboard
  Lambda — fine at boutique scale; add a GSI or rollups if traffic grows.
- **Design tokens** live in one place (`tailwind.config.mjs`) so the palette can
  be retuned globally.
- Content figures on the marketing pages mirror the public MiraTyper claims and
  are easy to edit in the page sources; treat benchmark numbers as placeholders
  to confirm against the latest published results.
```
