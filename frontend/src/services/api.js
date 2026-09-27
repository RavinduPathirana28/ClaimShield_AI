const API_BASE = '/api';

export async function login(username, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  return data;
}

export async function register(username, password, role = 'user') {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, role })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Registration failed');
  return data;
}

export async function getProfile(token) {
  const res = await fetch(`${API_BASE}/user/profile`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to fetch profile');
  return data;
}

export async function changePlan(token, plan) {
  const res = await fetch(`${API_BASE}/user/plan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ plan })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to change plan');
  return data;
}

export async function checkout(token, cardData) {
  const res = await fetch(`${API_BASE}/payment/checkout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(cardData)
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Payment failed');
  return data;
}

export async function verifyClaim(token, claim, engineMode = 'Standard A2A Protocol') {
  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/verify`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ claim, engine_mode: engineMode })
  });
  const data = await res.json();
  if (!res.ok) {
    if (res.status === 429) {
      throw new Error(`Rate limit exceeded! ${data.detail}`);
    }
    throw new Error(data.detail || 'Verification request failed');
  }
  return data;
}

export async function exportPdf(result) {
  const res = await fetch(`${API_BASE}/export-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ result })
  });
  if (!res.ok) throw new Error('Failed to generate PDF');
  return await res.blob();
}

export async function getAuditLogs(token) {
  const res = await fetch(`${API_BASE}/audit-logs`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to fetch audit logs');
  return data.logs || [];
}

export async function getHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return await res.json();
}
