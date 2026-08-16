import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
  withCredentials: true,
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
});

export function onUnauthorized(handler) {
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        handler();
      }
      return Promise.reject(error);
    },
  );
}

export function errorMessage(error, fallback = "Something went wrong. Please try again.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail) return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail[0]?.msg || fallback;
  }
  if (error?.code === "ECONNABORTED") return "The request timed out. Please try again.";
  if (!error?.response) return "Cannot reach the server. Is the backend running?";
  return fallback;
}

export default api;
