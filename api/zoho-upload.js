const DEFAULT_WEB_APP_URL = 'https://script.google.com/macros/s/AKfycbwSfhr2jxN8zAHpvtebkOzffb5M5p4k9AW25vfQHIoqQfaKsTTHEVjFZJwVqTmvmYHx/exec';

function readRequestBody(req) {
  return new Promise((resolve, reject) => {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => resolve(body));
    req.on('error', reject);
  });
}

function isPlainObject(value) {
  return value && typeof value === 'object' && !Array.isArray(value);
}

async function readJsonPayload(req) {
  if (isPlainObject(req.body)) return req.body;
  const raw = typeof req.body === 'string' ? req.body : await readRequestBody(req);
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch (error) {
    return { rawBody: raw };
  }
}

function normalizeUpstreamResponse(upstreamOk, text) {
  try {
    const json = JSON.parse(text || '{}');
    return isPlainObject(json) ? json : { ok: upstreamOk, success: upstreamOk, data: json };
  } catch (error) {
    return { ok: upstreamOk, success: false, error: 'Zoho proxy returned non JSON response', raw: text || '' };
  }
}

export default async function handler(req, res) {
  res.setHeader('Content-Type', 'application/json; charset=utf-8');

  if (req.method === 'GET') {
    return res.status(200).json({ ok: true, success: true, message: 'MZJ Zoho upload proxy is running' });
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ ok: false, success: false, error: 'Method not allowed' });
  }

  try {
    const payload = await readJsonPayload(req);
    if (process.env.MZJ_ZOHO_AUTH_TOKEN && !payload.authToken) {
      payload.authToken = process.env.MZJ_ZOHO_AUTH_TOKEN;
      payload.token = process.env.MZJ_ZOHO_AUTH_TOKEN;
    }
    if (!payload || !payload.fileName || !(payload.base64 || payload.fileData)) {
      return res.status(400).json({ ok: false, success: false, error: 'Missing file payload. Send JSON with fileName and base64/fileData.' });
    }

    let webAppUrl = process.env.MZJ_DRIVE_UPLOAD_WEB_APP_URL || DEFAULT_WEB_APP_URL;
    if (process.env.MZJ_ZOHO_AUTH_TOKEN && !webAppUrl.includes('token=')) {
      const joiner = webAppUrl.includes('?') ? '&' : '?';
      webAppUrl += joiner + 'token=' + encodeURIComponent(process.env.MZJ_ZOHO_AUTH_TOKEN);
    }
    const upstream = await fetch(webAppUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify(payload)
    });

    const text = await upstream.text();
    const json = normalizeUpstreamResponse(upstream.ok, text);
    return res.status(upstream.ok && json.success !== false && json.ok !== false ? 200 : 502).json(json);
  } catch (error) {
    return res.status(500).json({ ok: false, success: false, error: String(error && error.message ? error.message : error) });
  }
}
