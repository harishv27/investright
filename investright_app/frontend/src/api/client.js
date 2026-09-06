const rawBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
const BASE_URL = rawBase.replace(/\/+$/, "");

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = body instanceof FormData ? {} : { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      detail = data.detail || detail;
    } catch {
      // Response body was not valid JSON; fall back to statusText.
    }
    const error = new Error(detail);
    error.status = res.status;
    throw error;
  }

  return res.status === 204 ? null : res.json();
}

export const api = {
  signup: (fullName, email, password, age) =>
    request("/api/auth/signup", { method: "POST", body: { full_name: fullName, email, password, age }, auth: false }),

  login: (email, password) =>
    request("/api/auth/login", { method: "POST", body: { email, password }, auth: false }),
  loginWithGoogle: (credential) =>
    request("/api/auth/google", { method: "POST", body: { credential }, auth: false }),
  getUser: () => request("/api/auth/me"),
  updateUser: (fullName) => request("/api/auth/me", { method: "PATCH", body: { full_name: fullName } }),

  saveProfile: (profile) => request("/api/profile", { method: "POST", body: profile }),
  getProfile: () => request("/api/profile"),
  extractProfileMedia: (file) => {
    const body = new FormData();
    body.append("file", file);
    return request("/api/profile/extract-media", { method: "POST", body });
  },
  getEvidence: () => request("/api/profile/evidence"),
  confirmEvidence: (id, value) =>
    request(`/api/profile/evidence/${id}/confirm`, { method: "POST", body: { value } }),

  submitRiskAssessment: (responses) =>
    request("/api/risk-assessment", { method: "POST", body: { responses } }),

  getDashboard: () => request("/api/dashboard"),
  getPortfolio: () => request("/api/portfolio"),
  addHolding: (holding) => request("/api/portfolio", { method: "POST", body: holding }),
  deleteHolding: (id) => request(`/api/portfolio/${id}`, { method: "DELETE" }),

  askAgent: (message) => request("/api/agent/query", { method: "POST", body: { message } }),
  getConversations: () => request("/api/agent/conversations"),

  submitFeedback: (payload) => request("/api/feedback", { method: "POST", body: payload }),
  getFeedbackSummary: () => request("/api/feedback/summary"),
  getAllFeedbacks: () => request("/api/feedback"),
  getUserBenchmark: () => request("/api/evaluation/benchmark-5-users"),
  reEvaluateBenchmark: () => request("/api/evaluation/re-evaluate", { method: "POST" }),
  getPaperLatex: () => request("/api/evaluation/paper-latex"),
  downloadEvaluationZip: async () => {
    const token = getToken();
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const res = await fetch(`${BASE_URL}/api/evaluation/export-zip`, { headers });
    if (!res.ok) throw new Error("Failed to download research zip");
    return res.blob();
  },

  setToken: (token) => localStorage.setItem("token", token),
  clearToken: () => localStorage.removeItem("token"),
  hasToken: () => !!getToken(),
};
