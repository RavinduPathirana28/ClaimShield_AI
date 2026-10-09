import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import * as api from '../services/api';

const AuthContext = createContext(null);

function readStoredUser() {
  try {
    const saved = localStorage.getItem('cs_user');
    return saved ? JSON.parse(saved) : null;
  } catch {
    return null;
  }
}

const PRO_ROLES = new Set(['pro', 'premium', 'newsroom_admin']);

/**
 * Basic session handling: the token + user live in localStorage and are
 * hydrated synchronously — no server round-trip blocks the first render.
 * The JWT itself is the session; if it expires, the next API call returns
 * 401 and the shared handler drops it.
 */
export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('cs_token') || null);
  const [user, setUser] = useState(readStoredUser);
  const [profile, setProfile] = useState(null);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setProfile(null);
    localStorage.removeItem('cs_token');
    localStorage.removeItem('cs_user');
  }, []);

  // Any 401 from the API means the stored JWT is stale — drop the session.
  useEffect(() => {
    api.setUnauthorizedHandler(logout);
    return () => api.setUnauthorizedHandler(null);
  }, [logout]);

  const refreshProfile = useCallback(async () => {
    if (!token) return null;
    try {
      const data = await api.getProfile(token);
      setProfile(data);
      setUser((prev) => {
        if (prev && prev.role !== data.role) {
          const updated = { ...prev, role: data.role };
          localStorage.setItem('cs_user', JSON.stringify(updated));
          return updated;
        }
        return prev;
      });
      return data;
    } catch (err) {
      if (err.status !== 401) console.error('Failed to load profile:', err);
      return null;
    }
  }, [token]);

  // Silent background fill for quota/stats — never gates rendering.
  useEffect(() => {
    if (token) refreshProfile();
  }, [refreshProfile]);

  const persistSession = useCallback(async (res) => {
    setToken(res.token);
    localStorage.setItem('cs_token', res.token);
    const u = {
      username: res.username,
      role: res.role,
      email: res.email || res.username,
      name: res.name || res.username,
      picture: res.picture || '',
    };
    setUser(u);
    localStorage.setItem('cs_user', JSON.stringify(u));
    return res;
  }, []);

  const loginUser = useCallback(
    async (username, password) => persistSession(await api.login(username, password)),
    [persistSession]
  );

  const registerUser = useCallback(
    async (username, password, role = 'user') =>
      persistSession(await api.register(username, password, role)),
    [persistSession]
  );

  const loginWithGoogle = useCallback(
    async (credential) => persistSession(await api.googleLogin(credential)),
    [persistSession]
  );

  /** Adopt a freshly issued JWT (plan change / checkout re-issues one). */
  const saveToken = useCallback((newToken) => {
    if (!newToken) return;
    setToken(newToken);
    localStorage.setItem('cs_token', newToken);
  }, []);

  const value = useMemo(
    () => ({
      token,
      user,
      profile,
      isAuthenticated: !!token,
      isPro: profile?.is_pro || PRO_ROLES.has(user?.role),
      isAdmin: user?.role === 'newsroom_admin' || profile?.role === 'newsroom_admin',
      login: loginUser,
      register: registerUser,
      loginWithGoogle,
      logout,
      saveToken,
      refreshProfile,
    }),
    [token, user, profile, loginUser, registerUser, loginWithGoogle, logout, saveToken, refreshProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
