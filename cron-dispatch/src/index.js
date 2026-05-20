// Newsmarvin cron dispatcher.
//
// scheduled(): fires daily at 12:00 UTC and triggers the daily-digest workflow
// via GitHub's workflow_dispatch API. workflow_dispatch runs start within
// seconds, unlike GitHub's `schedule` event which queued us hours late.
//
// fetch(): liveness + a read-only /health check that verifies the token can
// reach GitHub WITHOUT triggering a send. There is intentionally no public
// endpoint that dispatches a digest (that would be an abuse / double-send
// vector). To trigger a send by hand, use: gh workflow run daily-digest.yml
//
// Required secret: GITHUB_TOKEN — fine-grained PAT scoped to the repo with
// "Actions: Read and write".

const GH_API = "https://api.github.com";

function workflowUrl(env) {
  return `${GH_API}/repos/${env.GITHUB_OWNER}/${env.GITHUB_REPO}/actions/workflows/${env.GITHUB_WORKFLOW}`;
}

function ghHeaders(env) {
  return {
    Authorization: `Bearer ${env.GITHUB_TOKEN}`,
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "newsmarvin-cron-dispatch",
    "Content-Type": "application/json",
  };
}

// Trigger the workflow. Returns the raw fetch Response.
async function dispatch(env) {
  return fetch(`${workflowUrl(env)}/dispatches`, {
    method: "POST",
    headers: ghHeaders(env),
    body: JSON.stringify({ ref: env.GITHUB_REF }),
  });
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(
      (async () => {
        if (!env.GITHUB_TOKEN) {
          console.error("GITHUB_TOKEN not set; cannot dispatch digest");
          return;
        }
        const resp = await dispatch(env);
        if (resp.status === 204) {
          console.log(`Dispatched ${env.GITHUB_WORKFLOW} @ ${event.cron}`);
        } else {
          console.error(`Dispatch failed: ${resp.status} ${await resp.text()}`);
        }
      })()
    );
  },

  async fetch(request, env) {
    const path = new URL(request.url).pathname;

    if (path === "/health") {
      if (!env.GITHUB_TOKEN) {
        return new Response("GITHUB_TOKEN not set\n", { status: 500 });
      }
      // Read-only: confirms the token reaches GitHub. Does NOT send a digest.
      const r = await fetch(workflowUrl(env), { headers: ghHeaders(env) });
      const ok = r.status === 200;
      return new Response(
        ok ? "ok: token can reach the workflow\n" : `fail: ${r.status} ${await r.text()}\n`,
        { status: ok ? 200 : 502 }
      );
    }

    return new Response(
      "newsmarvin cron dispatcher — fires daily-digest.yml at 12:00 UTC\n",
      { headers: { "Content-Type": "text/plain" } }
    );
  },
};
