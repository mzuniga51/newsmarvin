// =============================================================================
// Newsmarvin - Google Apps Script translation webhook
// =============================================================================
// Deploy as a Web App (Deploy > New deployment > Web app), Execute as: me,
// Who has access: Anyone. Set a shared secret in Project Settings > Script
// Properties: key=TRANSLATE_SECRET, value=<same secret used by send_digest.py>.
//
// Request body (POST, JSON):
//   {
//     "key": "<shared secret>",
//     "texts": ["hello", "world"],
//     "source_lang": "en",   // or "english"
//     "target_lang":  "es"   // or "spanish"
//   }
//
// Response:
//   { "translations": ["hola", "mundo"] }
// =============================================================================

function doPost(e) {
  try {
    var body = JSON.parse(e.postData.contents);
    var expected = PropertiesService.getScriptProperties().getProperty('TRANSLATE_SECRET');
    if (!expected || body.key !== expected) {
      return _json({ error: 'unauthorized' });
    }

    var texts = body.texts || [];
    var src = _normLang(body.source_lang || 'en');
    var tgt = _normLang(body.target_lang || 'es');

    var out = texts.map(function (t) {
      if (!t) return t;
      try {
        return LanguageApp.translate(t, src, tgt);
      } catch (err) {
        return t;
      }
    });

    return _json({ translations: out });
  } catch (err) {
    return _json({ error: String(err) });
  }
}

function _normLang(v) {
  var s = String(v).toLowerCase();
  if (s === 'english') return 'en';
  if (s === 'spanish') return 'es';
  return s;
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
