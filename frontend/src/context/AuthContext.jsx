import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import * as api from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('cs_token') || null);
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('cs_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = useCallback(async () => {
    if (!token) {
      setProfile(null);
      return;
    }
    try {
      const data = await api.getProfile(token);
      setProfile(data);
      // Synchronize role if changed
      if (user && data.role !== user.role) {
        const updated = { ...user, role: data.role };
        setUser(updated);
        localStorage.setItem('cs_user', JSON.stringify(updated));
      }
    } catch (err) {
      console.error('Failed to load profile:', err);
      if (err.message.includes('token') || err.message.includes('401')) {
        logout();
      }
    }
  }, [token, user]);

  useEffect(() => {
    if (token) {
      refreshProfile().finally(() => setLoading(false));
      // Refresh profile every 20 seconds to update live token bucket
      const interval = setInterval(refreshProfile, 20000);
      return () => clearInterval(interval);
    } else {
      setLoading(false);
    }
  }, [token, refreshProfile]);

  const loginUser = async (username, password) => {
    const res = await api.login(username, password);
    setToken(res.token);
    localStorage.setItem('cs_token', res.token);
    const u = { username: res.username, role: res.role };
    setUser(u);
    localStorage.setItem('cs_user', JSON.stringify(u));
    // Trigger profile fetch
    try {
      const p = await api.getProfile(res.token);
      setProfile(p);
    } catch (e) {
      console.warn(e);
    }
    return res;
  };

  const registerUser = async (username, password, role = 'user') => {
    const res = await api.register(username, password, role);
    setToken(res.token);
    localStorage.setItem('cs_token', res.token);
    const u = { username: res.username, role: res.role };
    setUser(u);
    localStorage.setItem('cs_user', JSON.stringify(u));
    try {
      const p = await api.getProfile(res.token);
      setProfile(p);
    } catch (e) {
      console.warn(e);
    }
    return res;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setProfile(null);
    localStorage.removeItem('cs_token');
    localStorage.removeItem('cs_user');
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        profile,
        isAuthenticated: !!token,
        isPro: profile?.is_pro || user?.role === 'pro',
        login: loginUser,
        register: registerUser,
        logout,
        refreshProfile,
        loading
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
