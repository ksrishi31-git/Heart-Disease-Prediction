import api from "./api.js";

export const authApi = {
  register: (data) => api.post("/auth/register", data),
  login: (data) => api.post("/auth/login", data),
  refresh: () => api.post("/auth/refresh"),
  logout: () => api.post("/auth/logout"),
  me: () => api.get("/auth/me"),

  changePassword: (data) => api.post("/users/change-password", data),
  listSessions: () => api.get("/users/sessions"),
  revokeSession: (id) => api.delete(`/users/sessions/${id}`),
  deleteAccount: () => api.delete("/users/me"),
};
