import axios from "axios";
import { useAuthStore } from "@/store/auth.store";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

let isRedirecting = false;

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401 && !isRedirecting) {
      isRedirecting = true;
      // Clear Zustand state + localStorage in one call so they stay in sync
      useAuthStore.getState().clearAuth();
      // Use replace so the login page doesn't get added to browser history
      window.location.replace("/login");
    }
    return Promise.reject(error);
  },
);

export default api;
