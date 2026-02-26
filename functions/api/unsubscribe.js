export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const email = (url.searchParams.get("email") || "").trim().toLowerCase();

  if (!email || !email.includes("@")) {
    return new Response(page("Invalid link.", false), {
      status: 400,
      headers: { "Content-Type": "text/html;charset=utf-8" },
    });
  }

  try {
    await env.NEWSMARVIN_SUBSCRIBERS.delete(email);
  } catch (e) {
    // Already gone or never existed — that's fine
  }

  return new Response(page("You've been unsubscribed. No more emails.", true), {
    headers: { "Content-Type": "text/html;charset=utf-8" },
  });
}

function page(message, success) {
  return `<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Unsubscribe — Marvin AI News</title></head>
<body style="margin:0;padding:60px 20px;background:#f6f6f0;font-family:Verdana,Geneva,sans-serif;text-align:center;">
<div style="max-width:400px;margin:0 auto;">
<h1 style="font-size:18px;color:${success ? '#826eb4' : '#c00'};">${message}</h1>
<p style="color:#666;font-size:13px;margin-top:20px;">
<a href="https://newsmarvin.com" style="color:#826eb4;">Back to NewsMarvin</a>
</p>
</div>
</body></html>`;
}
