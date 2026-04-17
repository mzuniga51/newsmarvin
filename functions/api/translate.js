// Translate one or more strings via Cloudflare Workers AI (m2m100-1.2b).
// Called server-to-server by send_digest.py. Requires a shared secret.
//
// POST /api/translate
// Headers: X-Translate-Key: <TRANSLATE_SECRET>
// Body: { "texts": ["...", "..."], "source_lang": "english", "target_lang": "spanish" }
// Response: { "translations": ["...", "..."] }

export async function onRequestPost(context) {
  const { request, env } = context;

  const provided = request.headers.get("X-Translate-Key") || "";
  if (!env.TRANSLATE_SECRET || provided !== env.TRANSLATE_SECRET) {
    return Response.json({ ok: false, error: "unauthorized" }, { status: 401 });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return Response.json({ ok: false, error: "invalid json" }, { status: 400 });
  }

  const texts = Array.isArray(body.texts) ? body.texts : null;
  const sourceLang = body.source_lang || "english";
  const targetLang = body.target_lang || "spanish";

  if (!texts || texts.length === 0) {
    return Response.json({ ok: false, error: "texts array required" }, { status: 400 });
  }
  if (texts.length > 100) {
    return Response.json({ ok: false, error: "max 100 texts per call" }, { status: 400 });
  }

  const translations = [];
  for (const text of texts) {
    if (!text || typeof text !== "string") {
      translations.push("");
      continue;
    }
    try {
      const res = await env.AI.run("@cf/meta/m2m100-1.2b", {
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
      });
      translations.push(res.translated_text || "");
    } catch (e) {
      translations.push("");
    }
  }

  return Response.json({ ok: true, translations });
}
