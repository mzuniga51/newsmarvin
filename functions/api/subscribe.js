export async function onRequestPost(context) {
  const { request, env } = context;

  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  };

  try {
    const { email } = await request.json();

    if (!email || !email.includes("@") || !email.includes(".")) {
      return Response.json({ ok: false, error: "invalid email" }, {
        status: 400,
        headers: corsHeaders,
      });
    }

    const normalized = email.trim().toLowerCase();

    await env.NEWSMARVIN_SUBSCRIBERS.put(normalized, JSON.stringify({
      subscribed_at: new Date().toISOString(),
    }));

    return Response.json({ ok: true }, { headers: corsHeaders });
  } catch (e) {
    return Response.json({ ok: false, error: "bad request" }, {
      status: 400,
      headers: corsHeaders,
    });
  }
}

export async function onRequestOptions() {
  return new Response(null, {
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    },
  });
}
