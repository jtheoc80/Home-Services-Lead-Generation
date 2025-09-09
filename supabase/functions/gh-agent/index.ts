// Deno Edge Function: receives a webhook from Supabase (DB Webhook or outbox poll)
// and calls GitHub REST to create an issue OR dispatch a workflow.

const GH_TOKEN = Deno.env.get("GH_TOKEN")!;
const GH_OWNER = Deno.env.get("GH_OWNER")!;  // e.g. "jtheoc80"
const GH_REPO  = Deno.env.get("GH_REPO")!;   // e.g. "Home-Services-Lead-Generation"
const WEBHOOK_SECRET = Deno.env.get("WEBHOOK_SECRET"); // optional shared secret

type Payload = {
  event: "etl_failed" | "etl_succeeded" | "dispatch_workflow" | "comment_pr",
  etl_id?: string;
  city?: string;
  days?: number;
  pr_number?: number;
  message?: string;
  details?: Record<string, unknown>;
};

async function ghFetch(path: string, body?: unknown, method = "POST") {
  const res = await fetch(`https://api.github.com/repos/${GH_OWNER}/${GH_REPO}${path}`, {
    method,
    headers: {
      "Authorization": `Bearer ${GH_TOKEN}`,
      "Accept": "application/vnd.github+json",
      "User-Agent": "supabase-gh-agent/1.0"
    },
    body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${method} ${path} -> ${res.status}: ${text}`);
  }
  return res.json().catch(() => ({}));
}

Deno.serve(async (req) => {
  try {
    if (WEBHOOK_SECRET) {
      const sig = req.headers.get("X-Webhook-Secret");
      if (sig !== WEBHOOK_SECRET) return new Response("forbidden", { status: 403 });
    }
    const body = await req.json();
    let payload = body;
    if (body?.record && body?.type) {
      // map DB webhook → agent event
      const r = body.record;
      payload = {
        event: r.status === 'failed' ? 'etl_failed' : 'etl_succeeded',
        etl_id: r.id,
        city: r.city,
        days: r.lookback_days,
        details: r.details
      };
    }

    const agentPayload = payload as Payload;

    switch (agentPayload.event) {
      case "etl_failed": {
        const title = `ETL failed${agentPayload.city ? ` — ${agentPayload.city}` : ""}`;
        const body = [
          `**ETL failed**${agentPayload.etl_id ? ` (run id: ${agentPayload.etl_id})` : ""}`,
          agentPayload.city ? `- city: \`${agentPayload.city}\`` : "",
          agentPayload.days ? `- lookback days: \`${agentPayload.days}\`` : "",
          agentPayload.details ? `\n\`\`\`json\n${JSON.stringify(agentPayload.details, null, 2)}\n\`\`\`` : ""
        ].filter(Boolean).join("\n");
        await ghFetch(`/issues`, { title, body, labels: ["etl", "failure"] });
        break;
      }
      case "etl_succeeded": {
        const title = `ETL succeeded${agentPayload.city ? ` — ${agentPayload.city}` : ""}`;
        await ghFetch(`/issues`, { title, body: "✅ ETL completed", labels: ["etl", "success"] });
        break;
      }
      case "dispatch_workflow": {
        // Kick a workflow by file name (change file path to yours)
        const file = ".github/workflows/etl.yml";
        const ref = "main";
        const inputs = { city: agentPayload.city ?? "houston_weekly", days: String(agentPayload.days ?? 14) };
        await ghFetch(`/actions/workflows/${encodeURIComponent(file)}/dispatches`,
          { ref, inputs });
        break;
      }
      case "comment_pr": {
        if (!agentPayload.pr_number) throw new Error("pr_number is required");
        await ghFetch(`/issues/${agentPayload.pr_number}/comments`, { body: agentPayload.message ?? "Update from Supabase agent." });
        break;
      }
      default:
        return new Response("unknown event", { status: 400 });
    }

    return new Response("ok", { status: 200 });
  } catch (e) {
    return new Response(`error: ${e.message}`, { status: 500 });
  }
});