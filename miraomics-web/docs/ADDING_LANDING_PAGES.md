# Adding a landing page

Landing pages (campaign pages, ad destinations, workshop sign-ups) are just
Markdown files. No code, no new route, no deploy config.

## 1. Create the file

Add `site/src/content/landing/<slug>.md`. The `<slug>` becomes the URL:
`/lp/<slug>`.

```markdown
---
title: "Free Workshop: Scalable Cell Typing"        # <title> + OG title
description: "60-minute hands-on workshop."          # meta description
eyebrow: "Live Workshop"                             # small label above headline
headline: "Stop hand-tuning cell types"              # H1
subheadline: "A practical session on atlas-scale annotation."
ctaLabel: "Save my seat"                             # button / form heading
ctaHref: "/contact?intent=workshop"                  # used when showForm: false
showForm: true                                       # inline lead form on the page
formIntent: "workshop"                               # tags the lead in the dashboard
campaign: "scrna-workshop-2026q3"                    # default campaign attribution
accent: "teal"                                        # teal | sky | violet
stats:                                                # optional proof points
  - value: "377"
    label: "cell types, one model"
  - value: "110M"
    label: "cells in ~30 min"
draft: false                                          # true hides it from the build
publishDate: 2026-06-01
---

## Body is normal Markdown

Headings, **bold**, lists, > quotes, and [links](/miratyper) all render in the
landing-page style. Everything below the frontmatter is the page body.
```

The frontmatter schema is enforced at build time in
`site/src/content/config.ts`, so a typo fails the build instead of shipping
broken.

## 2. Preview

```bash
cd miraomics-web/site
npm run dev      # visit http://localhost:4321/lp/<slug>
```

## 3. Ship

Open a PR. On merge to `main`, `web-deploy` builds and publishes it. The page
is automatically:

- styled in the site design language,
- given a lead-capture form posting to the same backend (when `showForm: true`),
- wired to **attribution** — UTMs on the ad URL (e.g.
  `/lp/<slug>?utm_source=linkedin&utm_campaign=spring`) are captured and attached
  to any lead, and show up in the dashboard's attribution breakdown.

## Tips

- **Drafts:** set `draft: true` to keep a page out of the build while you work.
- **No form, just a button:** set `showForm: false` and point `ctaHref` wherever
  you like (Calendly, a typeform, `/contact?intent=...`).
- **Tracking link template:**
  `https://www.miraomics.bio/lp/<slug>?utm_source=<src>&utm_medium=<medium>&utm_campaign=<campaign>`
- **Excluded from sitemap?** No — landing pages are included. To hide one from
  search while keeping it live, leave it out of paid links and add it to
  `robots.txt` if needed.
```
