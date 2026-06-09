/**
 * Dashboard read API (requirement #6). Routes:
 *   GET /admin/summary       KPIs + attribution breakdown (last 30 days)
 *   GET /admin/leads?limit=  most recent leads
 *
 * Protected at the API Gateway by a Cognito JWT authorizer (requirement #7),
 * so this function only runs for authenticated admins. AWS SDK v3 is provided
 * by the Lambda runtime — no node_modules.
 *
 * Env:
 *   TABLE_NAME      DynamoDB table (pk/sk)
 *   ALLOWED_ORIGIN  CORS origin
 */
import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, QueryCommand } from "@aws-sdk/lib-dynamodb";

const ddb = DynamoDBDocumentClient.from(new DynamoDBClient({}));
const TABLE = process.env.TABLE_NAME;
const ORIGIN = process.env.ALLOWED_ORIGIN || "*";

const cors = {
  "Access-Control-Allow-Origin": ORIGIN,
  "Access-Control-Allow-Headers": "Authorization,Content-Type",
  "Access-Control-Allow-Methods": "GET,OPTIONS",
  "Access-Control-Allow-Credentials": "true",
  "Content-Type": "application/json",
};
const reply = (statusCode, body) => ({
  statusCode,
  headers: cors,
  body: JSON.stringify(body),
});

const DEMO_INTENTS = new Set(["demo", "demo-pharma", "demo-pricing"]);

/** Query every item under a partition with sk >= cutoff, following pages. */
async function querySince(pk, cutoffIso, limit = 5000) {
  const items = [];
  let ExclusiveStartKey;
  do {
    const res = await ddb.send(
      new QueryCommand({
        TableName: TABLE,
        KeyConditionExpression: "pk = :pk AND sk >= :cut",
        ExpressionAttributeValues: { ":pk": pk, ":cut": cutoffIso },
        ExclusiveStartKey,
      }),
    );
    items.push(...(res.Items || []));
    ExclusiveStartKey = res.LastEvaluatedKey;
  } while (ExclusiveStartKey && items.length < limit);
  return items;
}

async function recentLeads(limit) {
  const res = await ddb.send(
    new QueryCommand({
      TableName: TABLE,
      KeyConditionExpression: "pk = :pk",
      ExpressionAttributeValues: { ":pk": "LEAD" },
      ScanIndexForward: false, // newest first (sk is timestamp-prefixed)
      Limit: Math.min(Math.max(limit, 1), 200),
    }),
  );
  return (res.Items || []).map((l) => ({
    id: l.id,
    ts: l.ts,
    name: l.name,
    email: l.email,
    organization: l.organization,
    role: l.role,
    intent: l.intent,
    campaign: l.campaign,
    page: l.page,
    message: l.message,
    first_touch: l.first_touch,
    last_touch: l.last_touch,
  }));
}

async function summary() {
  const cutoff = new Date(Date.now() - 30 * 86400 * 1000).toISOString();
  const [leads, views] = await Promise.all([
    querySince("LEAD", cutoff),
    querySince("PV", cutoff),
  ]);

  const demoRequests = leads.filter((l) => DEMO_INTENTS.has(l.intent)).length;

  const buckets = new Map();
  for (const l of leads) {
    const t = l.last_touch || l.first_touch || {};
    const source = t.utm_source || (t.referrer ? "referral" : "(direct)");
    const medium = t.utm_medium || (t.referrer ? "referral" : "none");
    const campaign = t.utm_campaign || l.campaign || "—";
    const key = `${source}|${medium}|${campaign}`;
    const b = buckets.get(key) || { source, medium, campaign, count: 0 };
    b.count += 1;
    buckets.set(key, b);
  }
  const byAttribution = [...buckets.values()].sort((a, b) => b.count - a.count);
  const topSource = byAttribution[0]?.source || "(direct)";

  return {
    leads_30d: leads.length,
    pageviews_30d: views.length,
    demo_requests: demoRequests,
    top_source: topSource,
    by_attribution: byAttribution.slice(0, 25),
    generated_at: new Date().toISOString(),
  };
}

export const handler = async (event) => {
  const method =
    event?.requestContext?.http?.method || event?.httpMethod || "GET";
  if (method === "OPTIONS") return { statusCode: 204, headers: cors, body: "" };

  const path =
    event?.requestContext?.http?.path || event?.rawPath || event?.path || "";

  try {
    if (path.endsWith("/admin/summary")) {
      return reply(200, await summary());
    }
    if (path.endsWith("/admin/leads")) {
      const limit = Number(event?.queryStringParameters?.limit || 50);
      return reply(200, { items: await recentLeads(limit) });
    }
    return reply(404, { error: "not_found" });
  } catch (err) {
    console.error("dashboard_error", err);
    return reply(500, { error: "internal_error" });
  }
};
