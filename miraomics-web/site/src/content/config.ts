import { defineCollection, z } from "astro:content";

/**
 * Landing-page collection (requirement #8).
 *
 * To add a campaign / workshop / ad landing page, drop a Markdown file in
 * `src/content/landing/<slug>.md` with the frontmatter below. It is published
 * automatically at `/lp/<slug>` — no code changes, no new route, no deploy
 * config. The body Markdown renders inside the page.
 */
const landing = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    // Hero
    eyebrow: z.string().optional(),
    headline: z.string(),
    subheadline: z.string().optional(),
    // Primary call-to-action
    ctaLabel: z.string().default("Request a demo"),
    ctaHref: z.string().default("/contact?intent=demo"),
    // Optional inline lead-capture form on the landing page
    showForm: z.boolean().default(true),
    formIntent: z.string().default("landing"),
    // Quick proof points rendered as stat pills
    stats: z
      .array(z.object({ value: z.string(), label: z.string() }))
      .default([]),
    // Campaign attribution defaults (used if the visitor arrives without UTMs)
    campaign: z.string().optional(),
    // Visual accent + publishing controls
    accent: z.enum(["teal", "sky", "violet"]).default("teal"),
    draft: z.boolean().default(false),
    publishDate: z.coerce.date().optional(),
  }),
});

export const collections = { landing };
