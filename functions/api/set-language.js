export async function onRequestGet(context) {
  const { request, env } = context;
  const url = new URL(request.url);
  const email = (url.searchParams.get("email") || "").trim().toLowerCase();
  const lang = (url.searchParams.get("lang") || "").trim().toLowerCase();

  if (!email || !email.includes("@")) {
    return new Response(page("Invalid link.", "en", false), {
      status: 400,
      headers: { "Content-Type": "text/html;charset=utf-8" },
    });
  }

  if (lang !== "es" && lang !== "en") {
    return new Response(page("Invalid language.", "en", false), {
      status: 400,
      headers: { "Content-Type": "text/html;charset=utf-8" },
    });
  }

  const existing = await env.NEWSMARVIN_SUBSCRIBERS.get(email);
  if (!existing) {
    return new Response(page("You're not subscribed.", lang, false), {
      status: 404,
      headers: { "Content-Type": "text/html;charset=utf-8" },
    });
  }

  let data;
  try {
    data = JSON.parse(existing);
  } catch (e) {
    data = { subscribed_at: new Date().toISOString() };
  }

  if (lang === "en") {
    delete data.lang;
  } else {
    data.lang = "es";
  }

  await env.NEWSMARVIN_SUBSCRIBERS.put(email, JSON.stringify(data));

  const msg = lang === "es"
    ? "Listo. A partir de mañana recibirás Newsmarvin en Español."
    : "Done. From tomorrow you'll receive Newsmarvin in English.";
  return new Response(page(msg, lang, true), {
    headers: { "Content-Type": "text/html;charset=utf-8" },
  });
}

function page(message, lang, success) {
  const back = lang === "es" ? "Volver a Newsmarvin" : "Back to Newsmarvin";
  return `<!DOCTYPE html>
<html lang="${lang}"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Newsmarvin</title></head>
<body style="margin:0;padding:60px 20px;background:#f6f6f0;font-family:Verdana,Geneva,sans-serif;text-align:center;">
<div style="max-width:480px;margin:0 auto;">
<h1 style="font-size:18px;color:${success ? '#826eb4' : '#c00'};line-height:1.5;">${message}</h1>
<p style="color:#666;font-size:13px;margin-top:20px;">
<a href="https://newsmarvin.com" style="color:#826eb4;">${back}</a>
</p>
</div>
</body></html>`;
}
