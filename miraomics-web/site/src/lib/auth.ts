/**
 * Client-side OAuth2 Authorization Code + PKCE against the Cognito Hosted UI
 * (requirement #7 — standard, hosted access control for a small admin group).
 *
 * Flow:
 *   login()            -> redirect to Cognito Hosted UI
 *   handleCallback()   -> exchange ?code= for tokens (called on /dashboard/callback)
 *   getIdToken()       -> returns a valid id token, refreshing if needed
 *   logout()           -> clear tokens + redirect to Cognito logout
 *
 * Tokens live in sessionStorage (cleared on tab close). No client secret —
 * the app client is configured as a public SPA client, PKCE-only.
 */
import { env } from "@/lib/site";

const TOKENS_KEY = "mira_dash_tokens_v1";
const VERIFIER_KEY = "mira_pkce_verifier";
const SCOPES = "openid email profile";

type Tokens = {
  id_token: string;
  access_token: string;
  refresh_token?: string;
  expires_at: number; // epoch ms
};

function base64url(bytes: ArrayBuffer): string {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function sha256(input: string): Promise<ArrayBuffer> {
  return crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
}

function randomString(len = 64): string {
  const bytes = crypto.getRandomValues(new Uint8Array(len));
  return base64url(bytes.buffer).slice(0, len);
}

function loadTokens(): Tokens | null {
  try {
    const raw = sessionStorage.getItem(TOKENS_KEY);
    return raw ? (JSON.parse(raw) as Tokens) : null;
  } catch {
    return null;
  }
}

function saveTokens(t: Tokens) {
  sessionStorage.setItem(TOKENS_KEY, JSON.stringify(t));
}

function configured(): boolean {
  return Boolean(env.cognitoDomain && env.cognitoClientId && env.dashboardRedirectUri);
}

export async function login(): Promise<void> {
  if (!configured()) {
    alert("Dashboard auth is not configured. Set PUBLIC_COGNITO_* env vars.");
    return;
  }
  const verifier = randomString(64);
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  const challenge = base64url(await sha256(verifier));

  const url = new URL(`${env.cognitoDomain}/oauth2/authorize`);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("client_id", env.cognitoClientId);
  url.searchParams.set("redirect_uri", env.dashboardRedirectUri);
  url.searchParams.set("scope", SCOPES);
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("code_challenge", challenge);
  url.searchParams.set("state", randomString(16));
  window.location.assign(url.toString());
}

export async function handleCallback(): Promise<boolean> {
  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  if (!code) return false;

  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  if (!verifier) return false;

  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: env.cognitoClientId,
    code,
    redirect_uri: env.dashboardRedirectUri,
    code_verifier: verifier,
  });

  const res = await fetch(`${env.cognitoDomain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) return false;

  const data = await res.json();
  saveTokens({
    id_token: data.id_token,
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_at: Date.now() + (data.expires_in ?? 3600) * 1000 - 30_000,
  });
  sessionStorage.removeItem(VERIFIER_KEY);
  return true;
}

async function refresh(tokens: Tokens): Promise<Tokens | null> {
  if (!tokens.refresh_token) return null;
  const body = new URLSearchParams({
    grant_type: "refresh_token",
    client_id: env.cognitoClientId,
    refresh_token: tokens.refresh_token,
  });
  const res = await fetch(`${env.cognitoDomain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) return null;
  const data = await res.json();
  const next: Tokens = {
    id_token: data.id_token,
    access_token: data.access_token,
    refresh_token: tokens.refresh_token,
    expires_at: Date.now() + (data.expires_in ?? 3600) * 1000 - 30_000,
  };
  saveTokens(next);
  return next;
}

/** Returns a valid id token (used as the API Authorization bearer), or null. */
export async function getIdToken(): Promise<string | null> {
  let tokens = loadTokens();
  if (!tokens) return null;
  if (Date.now() >= tokens.expires_at) {
    tokens = await refresh(tokens);
    if (!tokens) return null;
  }
  return tokens.id_token;
}

export function getProfile(): { email?: string; name?: string } | null {
  const tokens = loadTokens();
  if (!tokens) return null;
  try {
    const payload = JSON.parse(atob(tokens.id_token.split(".")[1]));
    return { email: payload.email, name: payload.name ?? payload["cognito:username"] };
  } catch {
    return null;
  }
}

export function logout(): void {
  sessionStorage.removeItem(TOKENS_KEY);
  if (!configured()) {
    window.location.assign("/");
    return;
  }
  const url = new URL(`${env.cognitoDomain}/logout`);
  url.searchParams.set("client_id", env.cognitoClientId);
  url.searchParams.set("logout_uri", new URL("/", window.location.origin).toString());
  window.location.assign(url.toString());
}
