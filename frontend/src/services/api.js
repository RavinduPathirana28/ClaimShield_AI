const API_BASE = (import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/$/, '') : '') + '/api';

export class ApiError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

let unauthorizedHandler = null;

/**
 * Register a callback invoked whenever the API answers 401 so the auth
 * layer can clear a stale session. Set once by AuthContext.
 */
export function setUnauthorizedHandler(handler) {
  unauthorizedHandler = handler;
}

function normalizeDetail(data, fallback) {
  const detail = data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d?.msg || JSON.stringify(d)).join('; ');
  }
  return fallback;
}

async function request(path, { method = 'GET', token, body, accept } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (accept) headers['Accept'] = accept;

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError('Could not reach the ClaimShield backend. Is it running?', 0);
  }

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    if (res.status === 401 && unauthorizedHandler) unauthorizedHandler();
    throw new ApiError(normalizeDetail(data, `Request failed (${res.status})`), res.status);
  }
  return data;
}

// ------------------------------------------------------------------ auth
export function login(username, password) {
  return request('/auth/login', { method: 'POST', body: { username, password } });
}

export function register(username, password, role = 'user') {
  return request('/auth/register', { method: 'POST', body: { username, password, role } });
}

export function getProfile(token) {
  return request('/user/profile', { token });
}

export function changePlan(token, plan) {
  return request('/user/plan', { method: 'POST', token, body: { plan } });
}

export function changePassword(token, currentPassword, newPassword) {
  return request('/user/password', {
    method: 'POST',
    token,
    body: { current_password: currentPassword, new_password: newPassword },
  });
}

// --------------------------------------------------------------- payment
export function checkout(token, card) {
  return request('/payment/checkout', { method: 'POST', token, body: card });
}

// -------------------------------------------------------------- verify
export function verifyClaim(token, claim, engineMode = 'Standard A2A Protocol') {
  return request('/verify', {
    method: 'POST',
    token,
    body: { claim, engine_mode: engineMode },
  });
}

/**
 * Run a verification over Server-Sent Events.
 *
 * `onStep({ step, label, detail })` fires for every live pipeline step;
 * resolves with `{ result, agent_logs }` once the terminal event arrives.
 */
export async function streamVerify(token, claim, engineMode, onStep) {
  const headers = { 'Content-Type': 'application/json', Accept: 'text/event-stream' };
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}/verify/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ claim, engine_mode: engineMode }),
    });
  } catch {
    throw new ApiError('Could not reach the ClaimShield backend. Is it running?', 0);
  }

  if (!res.ok) {
    const text = await res.text();
    let data = null;
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
    if (res.status === 401 && unauthorizedHandler) unauthorizedHandler();
    throw new ApiError(normalizeDetail(data, `Verification failed (${res.status})`), res.status);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let terminal = null;

  const handleEvent = (payload) => {
    if (payload.type === 'step') {
      onStep?.(payload);
    } else {
      terminal = payload; // result | error (exactly one)
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const dataLine = chunk.split('\n').find((line) => line.startsWith('data: '));
      if (!dataLine) continue;
      try {
        handleEvent(JSON.parse(dataLine.slice(6)));
      } catch {
        // ignore malformed frames rather than killing the stream
      }
    }
  }

  if (!terminal) {
    throw new ApiError('Connection closed before verification finished.', 0);
  }
  if (terminal.type === 'error') {
    if (terminal.code === 401 && unauthorizedHandler) unauthorizedHandler();
    throw new ApiError(terminal.detail || 'Verification failed.', terminal.code || 500);
  }
  return { result: terminal.result, agent_logs: terminal.agent_logs || [] };
}

// ------------------------------------------------------------- voice
export async function transcribeAudio(token, audioBlob, filename = 'claim_voice.webm') {
  const formData = new FormData();
  formData.append('file', audioBlob, filename);

  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${API_BASE}/transcribe`, {
      method: 'POST',
      headers,
      body: formData,
    });
  } catch {
    throw new ApiError('Could not reach the voice transcription service. Is the backend running?', 0);
  }

  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    if (res.status === 401 && unauthorizedHandler) unauthorizedHandler();
    throw new ApiError(normalizeDetail(data, `Audio transcription failed (${res.status})`), res.status);
  }

  return data;
}

// ---------------------------------------------------------------- misc
export async function exportPdf(result) {
  let res;
  try {
    res = await fetch(`${API_BASE}/export-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ result }),
    });
  } catch {
    throw new ApiError('Could not reach the ClaimShield backend. Is it running?', 0);
  }
  if (!res.ok) throw new ApiError('Failed to generate the PDF report.', res.status);
  return await res.blob();
}

export function getAuditLogs(token) {
  return request('/audit-logs', { token }).then((data) => data.logs || []);
}

// ---------------------------------------------------------------- admin
export function adminListUsers(token) {
  return request('/admin/users', { token }).then((data) => data.users || []);
}

export function adminSetRole(token, username, role) {
  return request('/admin/users', { method: 'PATCH', token, body: { username, role } });
}
