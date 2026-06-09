// @ts-check
import { defineConfig } from "astro/config";
import tailwind from "@astrojs/tailwind";
import sitemap from "@astrojs/sitemap";

// The public site URL is used for canonical URLs and sitemap generation.
// Override at build time with PUBLIC_SITE_URL (set by CI / Terraform output).
const site = process.env.PUBLIC_SITE_URL || "https://www.miraomics.bio";

// https://astro.build/config
export default defineConfig({
  site,
  output: "static",
  trailingSlash: "ignore",
  integrations: [
    tailwind({ applyBaseStyles: false }),
    sitemap({ filter: (page) => !page.includes("/dashboard") }),
  ],
  build: {
    // Emit clean URLs: /miratyper -> /miratyper/index.html
    format: "directory",
  },
});
