import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";
const TOKEN_KEY = "wbs_admin_token";

export const http = axios.create({
  baseURL,
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function extractApiError(error, fallback = "Terjadi kesalahan pada server") {
  if (!error) {
    return fallback;
  }

  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    if (typeof first === "string") {
      return first;
    }
    if (first?.msg) {
      return first.msg;
    }
  }

  if (error.message) {
    return error.message;
  }
  return fallback;
}

export { TOKEN_KEY };
