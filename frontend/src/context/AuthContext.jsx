import { createContext, useContext, useEffect, useState } from "react";

import api, { clearTokens, getTokens, setTokens } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const tokens = getTokens();
    if (!tokens?.access) {
      setLoading(false);
      return;
    }
    api
      .get("/auth/me/")
      .then((res) => setUser(res.data))
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  async function loginWithPassword(username, password, role) {
    const res = await api.post("/auth/login/", { username, password, ...(role ? { role } : {}) });
    setTokens({ access: res.data.access, refresh: res.data.refresh });
    setUser(res.data.user);
    return res.data.user;
  }

  async function requestOtp(phone_number) {
    const res = await api.post("/auth/otp/request/", { phone_number });
    return res.data;
  }

  async function verifyOtp(phone_number, code, role) {
    const res = await api.post("/auth/otp/verify/", { phone_number, code, ...(role ? { role } : {}) });
    setTokens({ access: res.data.access, refresh: res.data.refresh });
    setUser(res.data.user);
    return res.data.user;
  }

  async function registerAccount(payload) {
    const res = await api.post("/auth/register/", payload);
    setTokens({ access: res.data.access, refresh: res.data.refresh });
    setUser(res.data.user);
    return res.data.user;
  }

  async function promoteAdmin(identifier) {
    let payload = identifier;

    if (typeof identifier === "string") {
      const trimmed = identifier.trim();
      payload = trimmed ? { username: trimmed } : { username: "" };
    } else if (typeof identifier === "number") {
      payload = { user_id: identifier };
    }

    const res = await api.post("/auth/promote-admin/", payload);
    return res.data;
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, loading, loginWithPassword, requestOtp, verifyOtp, registerAccount, promoteAdmin, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
