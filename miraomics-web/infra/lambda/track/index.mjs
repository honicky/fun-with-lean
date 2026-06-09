/**
 * POST /track — pageview / attribution beacon (requirement #5).
 *
 * Stores a lightweight pageview event with first/last-touch attribution so the
 * dashboard can attribute traffic. Pageview rows carry a TTL so storage stays
 * cheap. AWS SDK v3 is provided by the Lambda runtime — no node_modules.
 *
 * Env:
 *   TABLE_NAME      DynamoDB table (pk/sk)
 *   PV_TTL_DAYS     days to retain pageview rows (default 400)
 *   ALLOWED_ORIGIN  CORS origin
 */
import { randomUUID } from "node:crypto";
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, PutCommand } from "@aws-sdk/lib-dynamodb";

const ddb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const TABLE = process.env.TABLE_NAME;
const TTL_DAYS = Number(process.env.PV_TTL_DAYS || 400);
const ORIGIN = process.env.ALLOWED_ORIGIN || "*";

const cors = {
  "Access-Control-Allow-Origin": ORIGIN,
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Allow-Methods": "POST,OPTIONS",
  "Content-Type": "application/json",
};
const clamp = (v, n = 512) => (typeof v === "string" ? v.slice(0, n) : "");

export const handler = async (event) => {
  const method =
    event?.requestContext?.http?.method || event?.httpMethod || "POST";
  if (method === "OPTIONS")
    return { statusCode: 204, headers: cors, body: "" };

  let data = {};
  try {
    data = JSON.parse(event.body || "{}");
  } catch {
    return { statusCode: 400, headers: cors, body: '{"error":"invalid_json"}' };
  }

  const now = new Date();
  const iso = now.toISOString();
  const id = randomUUID();
  const first = data.first_touch || {};
  const last = data.last_touch || {};

  const item = {
    pk: "PV",
    sk: `${iso}#${id}`,
    id,
    ts: iso,
    type: "pageview",
    path: clamp(data.path, 512),
    title: clamp(data.title, 256),
    visitor_id: clamp(data.visitor_id, 64),
    session_id: clamp(data.session_id, 64),
    utm_source: clamp(last.utm_source || first.utm_source, 128),
    utm_medium: clamp(last.utm_medium || first.utm_medium, 128),
    utm_campaign: clamp(last.utm_campaign || first.utm_campaign, 128),
    referrer: clamp(last.referrer || first.referrer, 512),
    landing_path: clamp(first.landing_path, 512),
    ttl: Math.floor(now.getTime() / 1000) + TTL_DAYS * 86400,
  };

  try {
    await ddb.send(new PutCommand({ TableName: TABLE, Item: item }));
  } catch (err) {
    console.error("ddb_put_failed", err);
    return { statusCode: 500, headers: cors, body: '{"error":"store_failed"}' };
  }

  return { statusCode: 202, headers: cors, body: '{"ok":true}' };
};
