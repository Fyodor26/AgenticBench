import apiClient from "./client";

/* ---------------- AUTH ---------------- */

export const authAPI = {
  login: (email: string, password: string) =>
    apiClient.post("/auth/login", { email, password }),

  register: (name: string, email: string, password: string) =>
    apiClient.post("/auth/register", {
      name,
      email,
      password,
    }),

  logout: () => {
    localStorage.removeItem("token");
  },
};

/* ---------------- AGENTS ---------------- */

export const agentAPI = {
  listAgents: (skip = 0, limit = 100) =>
    apiClient.get(`/agents?skip=${skip}&limit=${limit}`),

  getAgent: (id: number) => apiClient.get(`/agents/${id}`),

  createAgent: (data: any) =>
    apiClient.post("/agents", data),

  updateAgent: (id: number, data: any) =>
    apiClient.put(`/agents/${id}`, data),

  deleteAgent: (id: number) =>
    apiClient.delete(`/agents/${id}`),

  // Matches POST /agents/{id}/test on the backend (previously this called
  // a route that didn't exist; the Agents page also never actually called
  // it - the "Test" button just showed a fake alert()).
  testConnection: (id: number) =>
    apiClient.post(`/agents/${id}/test`),
};

/* ---------------- LEADERBOARD ---------------- */

export const leaderboardAPI = {
  // Was pointed at "/leaderboard", which doesn't exist on the backend -
  // the real route lives under /evaluations.
  getLeaderboard: (limit = 50, offset = 0) =>
    apiClient.get(`/evaluations/leaderboard/agents?limit=${limit}&offset=${offset}`),
};

/* ---------------- STATS / DASHBOARD ---------------- */

// Was `dashboardAPI.getDashboard()` calling a "/dashboard" route that never
// existed on the backend and was never actually called by Dashboard.tsx
// either. The backend does expose real aggregate stats - wire it up
// properly instead of leaving dead code around.
export const statsAPI = {
  getOverview: () => apiClient.get("/evaluations/stats/overview"),
};

/* ---------------- SETTINGS ---------------- */

export const settingsAPI = {
  getSettings: () => apiClient.get("/settings"),

  saveSettings: (data: any) => apiClient.put("/settings", data),
};

/* ---------------- BENCHMARK ---------------- */

export { benchmarkAPI } from "./benchmark";

export type {
  BenchmarkRequest,
  BenchmarkResponse,
  BenchmarkResult,
} from "./benchmark";
