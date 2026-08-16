import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../services/auth.js";
import { onUnauthorized } from "../services/api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  onUnauthorized(() => setUser(null));

  const checkSession = useCallback(async () => {
    try {
      const { data } = await authApi.me();
      setUser(data);
      return data;
    } catch {
      try {
        await authApi.refresh();
        const { data } = await authApi.me();
        setUser(data);
        return data;
      } catch {
        setUser(null);
        return null;
      }
    }
  }, []);

  useEffect(() => {
    checkSession().finally(() => setLoading(false));
  }, [checkSession]);

  const login = useCallback(async (email, password) => {
    const { data } = await authApi.login({ email, password });
    setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (payload) => {
    const { data } = await authApi.register(payload);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, checkSession }),
    [user, loading, login, register, logout, checkSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside <AuthProvider>");
  return context;
}
