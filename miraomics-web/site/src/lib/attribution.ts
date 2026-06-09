/**
 * Inbound-traffic attribution (requirement #5).
 *
 * Runs in the browser. On every page load it:
 *   1. Parses UTM params + ad click ids (gclid/fbclid/msclkid/li_fat_id).
 *   2. Records a FIRST-TOUCH snapshot (persisted, never overwritten) and a
 *      LAST-TOUCH snapshot (refreshed whenever new campaign params appear).
 *   3. Fires a lightweight pageview beacon to the /track endpoint.
 *
 * Form submissions read `getAttribution()` and attach it, so every lead is
 * tied back to the campaign / referrer / landing page that produced it.
 *
 * No cookies, no third-party scripts — first-party localStorage only.
 */

const STORAGE_KEY = "mira_attr_v1";
const VISITOR_KEY = "mira_vid_v1";
const SESSION_KEY = "mira_sid_v1";

type Touch = {
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_term?: string;
  utm_content?: string;
  gclid?: string;
  fbclid?: string;
  msclkid?: string;
  li_fat_id?: string;
  referrer?: string;
  landing_path?: string;
  ts: string;
};

export type Attribution = {
  visitor_id: string;
  session_id: string;
  first_touch: Touch;
  last_touch: Touch;
};

const UTM_KEYS = [
  "utm_source",
  "utm_medium",
  "utm_campaign",
  "utm_term",
  "utm_content",
] as const;
const CLICK_KEYS = ["gclid", "fbclid", "msclkid", "li_fat_id"] as const;

function uuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function readParams(): Touch {
  const params = new URLSearchParams(window.location.search);
  const touch: Touch = { ts: new Date().toISOString() };
  for (const k of UTM_KEYS) {
    const v = params.get(k);
    if (v) touch[k] = v.slice(0, 256);
  }
  for (const k of CLICK_KEYS) {
    const v = params.get(k);
    if (v) touch[k] = v.slice(0, 256);
  }
  const ref = document.referrer;
  if (ref && !ref.includes(window.location.host)) {
    touch.referrer = ref.slice(0, 512);
  }
  touch.landing_path = window.location.pathname + window.location.search;
  return touch;
}

function hasCampaignSignal(t: Touch): boolean {
  return UTM_KEYS.some((k) => t[k]) || CLICK_KEYS.some((k) => t[k]) || !!t.referrer;
}

function persistent<T>(key: string, factory: () => T): T {
  try {
    const existing = localStorage.getItem(key);
    if (existing) return JSON.parse(existing) as T;
  } catch {
    /* storage may be unavailable (private mode) */
  }
  const value = factory();
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* ignore */
  }
  return value;
}

/** Initialise attribution + fire a pageview beacon. Call once per page load. */
export function initAttribution(apiBaseUrl: string): Attribution {
  const current = readParams();

  const visitorId = persistent(VISITOR_KEY, () => uuid());
  // Session id rolls over after 30 min of inactivity.
  let sessionId = sessionStorage.getItem(SESSION_KEY) || "";
  if (!sessionId) {
    sessionId = uuid();
    sessionStorage.setItem(SESSION_KEY, sessionId);
  }

  let stored: Attribution | null = null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) stored = JSON.parse(raw) as Attribution;
  } catch {
    /* ignore */
  }

  const attribution: Attribution = stored ?? {
    visitor_id: visitorId,
    session_id: sessionId,
    first_touch: current,
    last_touch: current,
  };

  attribution.visitor_id = visitorId;
  attribution.session_id = sessionId;
  // First touch is sticky; only fill it if it had no real signal yet.
  if (!hasCampaignSignal(attribution.first_touch) && hasCampaignSignal(current)) {
    attribution.first_touch = current;
  }
  // Last touch refreshes whenever a new campaign signal arrives.
  if (hasCampaignSignal(current)) {
    attribution.last_touch = current;
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(attribution));
  } catch {
    /* ignore */
  }

  sendPageview(apiBaseUrl, attribution);
  return attribution;
}

/** Returns the stored attribution, or a minimal stub if none yet. */
export function getAttribution(): Attribution | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as Attribution;
  } catch {
    /* ignore */
  }
  return null;
}

function sendPageview(apiBaseUrl: string, attribution: Attribution) {
  if (!apiBaseUrl) return;
  const payload = JSON.stringify({
    type: "pageview",
    path: window.location.pathname,
    title: document.title,
    visitor_id: attribution.visitor_id,
    session_id: attribution.session_id,
    first_touch: attribution.first_touch,
    last_touch: attribution.last_touch,
    screen: { w: window.screen?.width, h: window.screen?.height },
    ts: new Date().toISOString(),
  });
  const url = `${apiBaseUrl.replace(/\/$/, "")}/track`;
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([payload], { type: "application/json" }));
      return;
    }
  } catch {
    /* fall through to fetch */
  }
  // keepalive lets the request finish even as the page unloads.
  fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
    keepalive: true,
  }).catch(() => {});
}
