import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import * as authService from "../services/authService";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("scai_access_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    authService
      .getMe()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("scai_access_token");
        localStorage.removeItem("scai_refresh_token");
      })
      .finally(() => setIsLoading(false));
  }, []);

  const persistSession = useCallback((tokenResponse) => {
    localStorage.setItem("scai_access_token", tokenResponse.access_token);
    localStorage.setItem("scai_refresh_token", tokenResponse.refresh_token);
    setUser(tokenResponse.user);
  }, []);

  const login = useCallback(
    async (credentials) => {
      const tokenResponse = await authService.login(credentials);
      persistSession(tokenResponse);
      return tokenResponse.user;
    },
    [persistSession]
  );

  const register = useCallback(
    async (payload) => {
      const tokenResponse = await authService.register(payload);
      persistSession(tokenResponse);
      return tokenResponse.user;
    },
    [persistSession]
  );

  const logout = useCallback(() => {
    localStorage.removeItem("scai_access_token");
    localStorage.removeItem("scai_refresh_token");
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (payload) => {
    const updated = await authService.updateMe(payload);
    setUser(updated);
    return updated;
  }, []);

  const value = useMemo(
    () => ({ user, isLoading, isAuthenticated: !!user, login, register, logout, updateProfile }),
    [user, isLoading, login, register, logout, updateProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
