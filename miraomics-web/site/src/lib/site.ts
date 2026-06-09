/**
 * Single source of truth for site-wide config: company facts, navigation and
 * environment-derived endpoints. Edit nav here to change the menu everywhere.
 */

export const company = {
  name: "Miraomics",
  legalName: "Miraomics, Inc.",
  tagline: "Universal cell classification, production-ready.",
  email: "hello@miraomics.bio",
  linkedin: "https://www.linkedin.com/company/miraomics",
  year: new Date().getFullYear(),
};

/** Primary navigation. Product (MiraTyper) leads; services are secondary. */
export const primaryNav: { label: string; href: string }[] = [
  { label: "Platform", href: "/miratyper" },
  { label: "Benchmarks", href: "/miratyper#benchmarks" },
  { label: "Services", href: "/services" },
  { label: "About", href: "/about" },
];

export const footerNav: { heading: string; links: { label: string; href: string }[] }[] = [
  {
    heading: "Product",
    links: [
      { label: "MiraTyper", href: "/miratyper" },
      { label: "Benchmarks", href: "/miratyper#benchmarks" },
      { label: "Request a demo", href: "/contact?intent=demo" },
    ],
  },
  {
    heading: "Company",
    links: [
      { label: "About", href: "/about" },
      { label: "Services", href: "/services" },
      { label: "Contact", href: "/contact" },
    ],
  },
];

export const primaryCta = { label: "Request a demo", href: "/contact?intent=demo" };

/** Environment-derived endpoints (compiled into the static build). */
export const env = {
  apiBaseUrl: import.meta.env.PUBLIC_API_BASE_URL ?? "",
  cognitoDomain: import.meta.env.PUBLIC_COGNITO_DOMAIN ?? "",
  cognitoClientId: import.meta.env.PUBLIC_COGNITO_CLIENT_ID ?? "",
  cognitoRegion: import.meta.env.PUBLIC_COGNITO_REGION ?? "us-east-1",
  dashboardRedirectUri: import.meta.env.PUBLIC_DASHBOARD_REDIRECT_URI ?? "",
};
