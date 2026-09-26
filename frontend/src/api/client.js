import axios from "axios";

const TOKEN_KEY = "trueblue.tokens";

export function getTokens() {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_KEY) || "null");
  } catch {
    return null;
  }
}

export function setTokens(tokens) {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});

api.interceptors.request.use((config) => {
  const tokens = getTokens();
  if (tokens?.access) {
    config.headers.Authorization = `Bearer ${tokens.access}`;
  }
  return config;
});

let refreshing = null;

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retried) {
      original._retried = true;
      const tokens = getTokens();
      if (tokens?.refresh) {
        refreshing =
          refreshing ||
          axios
            .post("/api/auth/token/refresh/", { refresh: tokens.refresh })
            .then((res) => {
              setTokens({ ...tokens, access: res.data.access });
              return res.data.access;
            })
            .finally(() => {
              refreshing = null;
            });
        try {
          const access = await refreshing;
          original.headers.Authorization = `Bearer ${access}`;
          return api(original);
        } catch {
          clearTokens();
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
