// All calls are relative (/api/...). Nginx (docker compose) or the Ingress (k8s)
// decides where they actually go, so the browser never needs a backend hostname.
const BASE = import.meta.env.VITE_API_BASE ?? '';

async function request(path, { method = 'GET', body } = {}) {
  const response = await fetch(`${BASE}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => `${d.loc?.at(-1)}: ${d.msg}`).join(', ')
      : detail || `Request failed (${response.status})`;
    throw new Error(message);
  }
  return data;
}

function query(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const text = search.toString();
  return text ? `?${text}` : '';
}

export const api = {
  info: () => request('/api/info'),
  stats: () => request('/api/stats'),
  categories: () => request('/api/categories'),
  movements: (limit = 12) => request(`/api/movements?limit=${limit}`),
  products: (filters = {}) => request(`/api/products${query(filters)}`),
  createProduct: (payload) => request('/api/products', { method: 'POST', body: payload }),
  updateProduct: (id, payload) => request(`/api/products/${id}`, { method: 'PUT', body: payload }),
  deleteProduct: (id) => request(`/api/products/${id}`, { method: 'DELETE' }),
  adjustStock: (id, payload) => request(`/api/products/${id}/adjust`, { method: 'POST', body: payload }),
};
