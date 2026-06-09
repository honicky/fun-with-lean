/**
 * POST /submit — lead capture (requirement #4).
 *
 * Validates a lead payload, stores it in DynamoDB, and emails a notification
 * via SES. Uses only the AWS SDK v3 modules bundled into the Lambda Node.js
 * runtime, so the deploy artifact is just this file — no node_modules.
 *
 * Env:
 *   TABLE_NAME      DynamoDB table (single-table: pk/sk)
 *   NOTIFY_EMAIL    where lead notifications are sent
 *   SES_FROM        verified SES sender address
 *   ALLOWED_ORIGIN  CORS origin (e.g. https://www.miraomics.bio or *)
 */
import { randomUUID } from "node:crypto";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";
import { SESClient, SendEmailCommand } from "@aws-sdk/client-ses";

const ddb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const ses = new SESClient({});

const TABLE = process.env.TABLE_NAME;
const NOTIFY = process.env.NOTIFY_EMAIL;
const FROM = process.env.SES_FROM;
const ORIGIN = process.env.ALLOWED_ORIGIN || "*";

const cors = {
  "Access-Control-Allow-Origin": ORIGIN,
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST,OPTIONS",
  "Content-Type": "application/json",
};

const clamp = (v, n = 2000) => (typeof v === "string" ? v.slice(0, n) : "");
const isEmail = (s) => /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(s);

function reply(statusCode, body) {
  return { statusCode, headers: cors, body: JSON.stringify(body) };
}

export const handler = async (event) => {
  const method =
    event?.requestContext?.http?.method || event?.httpMethod || "POST";
  if (method === "OPTIONS") return reply(204, {});
  if (method !== "POST") return reply(405, { error: "method_not_allowed" });

  let data;
  try {
    data = JSON.parse(event.body || "{}");
  } catch {
    return reply(400, { error: "invalid_json" });
  }

  // Server-side honeypot: silently accept and drop bot submissions.
  if (data.company_website) return reply(200, { ok: true });

  const name = clamp(data.name, 200).trim();
  const email = clamp(data.email, 320).trim().toLowerCase();
  if (!name || !isEmail(email)) {
    return reply(400, { error: "name_and_valid_email_required" });
  }

  const now = new Date().toISOString();
  const id = randomUUID();
  const att = data.attribution || {};
  const item = {
    pk: "LEAD",
    sk: `${now}#${id}`,
    id,
    ts: now,
    type: "lead",
    intent: clamp(data.intent, 64) || "contact",
    campaign: clamp(data.campaign, 128),
    name,
    email,
    organization: clamp(data.organization, 200),
    role: clamp(data.role, 200),
    message: clamp(data.message, 4000),
    page: clamp(data.page, 512),
    visitor_id: clamp(att.visitor_id, 64),
    session_id: clamp(att.session_id, 64),
    first_touch: att.first_touch || {},
    last_touch: att.last_touch || {},
    source_ip:
      event?.requestContext?.http?.sourceIp ||
      event?.headers?.["x-forwarded-for"] ||
      "",
  };

  try {
    await ddb.send(new PutCommand({ TableName: TABLE, Item: item }));
  } catch (err) {
    console.error("ddb_put_failed", err);
    return reply(500, { error: "store_failed" });
  }

  if (NOTIFY && FROM) {
    const t = item.last_touch || {};
    const lines = [
      `New ${item.intent} lead from the website`,
      "",
      `Name:    ${name}`,
      `Email:   ${email}`,
      `Org:     ${item.organization || "—"}`,
      `Role:    ${item.role || "—"}`,
      `Page:    ${item.page || "—"}`,
      `Campaign:${item.campaign || "—"}`,
      "",
      "Attribution (last touch):",
      `  source:   ${t.utm_source || "(direct)"}`,
      `  medium:   ${t.utm_medium || "—"}`,
      `  campaign: ${t.utm_campaign || "—"}`,
      `  referrer: ${t.referrer || "—"}`,
      `  landing:  ${t.landing_path || "—"}`,
      "",
      "Message:",
      item.message || "—",
    ].join("\n");

    try {
      await ses.send(
        new SendEmailCommand({
          Source: FROM,
          Destination: { ToAddresses: [NOTIFY] },
          ReplyToAddresses: [email],
          Message: {
            Subject: { Data: `New lead: ${name} (${item.intent})` },
            Body: { Text: { Data: lines } },
          },
        }),
      );
    } catch (err) {
      // Storage already succeeded; don't fail the request on email trouble.
      console.error("ses_send_failed", err);
    }
  }

  return reply(200, { ok: true, id });
};
