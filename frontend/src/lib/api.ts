import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { useAuthStore } from "@/store/auth";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = useAuthStore.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshando: Promise<string | null> | null = null;

async function renovarToken(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const { data } = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh/`, { refresh: refreshToken });
    useAuthStore.getState().setTokens(data.access, refreshToken);
    return data.access as string;
  } catch {
    useAuthStore.getState().logout();
    return null;
  }
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && original && !original._retry) {
      original._retry = true;
      refreshando = refreshando ?? renovarToken();
      const novoToken = await refreshando;
      refreshando = null;
      if (novoToken && original.headers) {
        original.headers.Authorization = `Bearer ${novoToken}`;
        return api(original);
      }
    }
    return Promise.reject(error);
  }
);
