import api from "./api.js";

export const predictionsApi = {
  create: (payload) => api.post("/predictions", payload),
  list: (params = {}) => api.get("/predictions", { params }),
  get: (id) => api.get(`/predictions/${id}`),
  remove: (id) => api.delete(`/predictions/${id}`),
  stats: () => api.get("/predictions/stats"),
};

export const modelsApi = {
  insights: () => api.get("/models/insights"),
  metrics: () => api.get("/models"),
  features: () => api.get("/models/features"),
};
