// Shankis Tea — lightweight API client shared by all pages.
const API_BASE = "/api";
const TOKEN_KEY = "shankis_token";

export const auth = {
  get token() {
    return localStorage.getItem(TOKEN_KEY);
  },
  set token(v) {
    if (v) localStorage.setItem(TOKEN_KEY, v);
    else localStorage.removeItem(TOKEN_KEY);
  },
  get isLoggedIn() {
    return !!this.token;
  },
  logout() {
    this.token = null;
    localStorage.removeItem("shankis_user");
  },
  get user() {
    try {
      return JSON.parse(localStorage.getItem("shankis_user"));
    } catch {
      return null;
    }
  },
  set user(u) {
    if (u) localStorage.setItem("shankis_user", JSON.stringify(u));
    else localStorage.removeItem("shankis_user");
  },
};

async function request(method, path, body, { authed = false } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (authed && auth.token) headers["Authorization"] = `Bearer ${auth.token}`;
  const res = await fetch(API_BASE + path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data.detail || data.message || `Request failed (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data;
}

export const api = {
  // auth
  signup: (d) => request("POST", "/auth/signup", d),
  login: (d) => request("POST", "/auth/login", d),
  me: () => request("GET", "/auth/me", undefined, { authed: true }),
  requestReset: (d) => request("POST", "/auth/password-reset/request", d),
  confirmReset: (d) => request("POST", "/auth/password-reset/confirm", d),

  // profile
  getProfile: () => request("GET", "/users/me", undefined, { authed: true }),
  updateProfile: (d) => request("PATCH", "/users/me", d, { authed: true }),

  // products (public)
  products: (qs = "") => request("GET", `/products${qs}`),
  product: (slug) => request("GET", `/products/${slug}`),
  // products (admin)
  createProduct: (d) => request("POST", "/products", d, { authed: true }),
  updateProduct: (id, d) => request("PUT", `/products/${id}`, d, { authed: true }),
  updateStock: (id, d) => request("PATCH", `/products/${id}/stock`, d, { authed: true }),
  deleteProduct: (id) => request("DELETE", `/products/${id}`, undefined, { authed: true }),

  // cart
  cart: () => request("GET", "/cart", undefined, { authed: true }),
  addToCart: (d) => request("POST", "/cart/items", d, { authed: true }),
  updateCartItem: (id, d) => request("PATCH", `/cart/items/${id}`, d, { authed: true }),
  removeCartItem: (id) => request("DELETE", `/cart/items/${id}`, undefined, { authed: true }),
  clearCart: () => request("DELETE", "/cart", undefined, { authed: true }),

  // orders
  checkout: (d) => request("POST", "/orders/checkout", d, { authed: true }),
  myOrders: () => request("GET", "/orders", undefined, { authed: true }),
  order: (id) => request("GET", `/orders/${id}`, undefined, { authed: true }),
  updateOrderStatus: (id, d) =>
    request("PATCH", `/orders/${id}/status`, d, { authed: true }),

  // reviews
  reviews: (productId) => request("GET", `/products/${productId}/reviews`),
  addReview: (productId, d) =>
    request("POST", `/products/${productId}/reviews`, d, { authed: true }),
  updateReview: (id, d) => request("PUT", `/reviews/${id}`, d, { authed: true }),
  deleteReview: (id) => request("DELETE", `/reviews/${id}`, undefined, { authed: true }),

  // dashboard / admin
  dashboardSummary: () => request("GET", "/dashboard/summary", undefined, { authed: true }),
  allOrders: () => request("GET", "/dashboard/orders", undefined, { authed: true }),
  inventory: () => request("GET", "/dashboard/inventory", undefined, { authed: true }),
  auditLogs: () => request("GET", "/dashboard/audit-logs", undefined, { authed: true }),

  // users (super admin)
  users: () => request("GET", "/users", undefined, { authed: true }),
  createAdmin: (d) => request("POST", "/users/admins", d, { authed: true }),
  setRole: (id, d) => request("PATCH", `/users/${id}/role`, d, { authed: true }),
  deactivateUser: (id) =>
    request("PATCH", `/users/${id}/deactivate`, {}, { authed: true }),
  activateUser: (id) => request("PATCH", `/users/${id}/activate`, {}, { authed: true }),
  deleteUser: (id) => request("DELETE", `/users/${id}`, undefined, { authed: true }),
};

// Tiny helpers used across pages.
export const money = (n) => "₹ " + Number(n).toLocaleString("en-IN");

export function requireLogin(redirect = "login.html") {
  if (!auth.isLoggedIn) {
    window.location.href = `${redirect}?next=${encodeURIComponent(location.pathname)}`;
    return false;
  }
  return true;
}
