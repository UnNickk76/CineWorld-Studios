// CineWorld Studio's - Context Providers
// Extracted from App.js for better maintainability

import React, { createContext, useState, useEffect, useContext, useCallback, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
export { API };

// Context declarations
export const AuthContext = createContext(null);
export const LanguageContext = createContext(null);

// Translations hook
export const useTranslations = () => {
  const { language, translations } = useContext(LanguageContext);
  return { t: (key) => translations[key] || key, language };
};

// Simple in-memory cache with TTL
const apiCache = new Map();
const CACHE_TTL = 60000; // 60 seconds

const getCached = (key) => {
  const entry = apiCache.get(key);
  if (!entry) return null;
  if (Date.now() - entry.ts > CACHE_TTL) {
    apiCache.delete(key);
    return null;
  }
  return entry.data;
};

const setCache = (key, data) => {
  apiCache.set(key, { data, ts: Date.now() });
};

export const clearApiCache = () => apiCache.clear();

// Auth Provider with auto-login
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const tokenRef = useRef(localStorage.getItem('cineworld_token'));
  const [token, setTokenState] = useState(tokenRef.current);
  const logoutRef = useRef(null);

  const setToken = (t) => {
    tokenRef.current = t;
    setTokenState(t);
  };

  const api = React.useMemo(() => {
    const instance = axios.create({
      baseURL: API,
      timeout: 30000
    });

    let consecutive401Count = 0;

    // Request interceptor - add token
    instance.interceptors.request.use(config => {
      const t = tokenRef.current;
      if (t) config.headers.Authorization = `Bearer ${t}`;
      return config;
    });

    // Response interceptor - handle 401 + retry on network error
    instance.interceptors.response.use(
      (response) => {
        // Reset 401 counter on any successful response
        consecutive401Count = 0;
        return response;
      },
      async (error) => {
        const config = error.config;

        // 401 = token expired/invalid → auto-logout (skip for login/register/me endpoints)
        if (error.response?.status === 401) {
          const url = config?.url || '';
          const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/me');
          if (!isAuthEndpoint) {
            consecutive401Count++;
            // Only logout after 2+ consecutive 401s to avoid transient issues
            if (consecutive401Count >= 2) {
              localStorage.removeItem('cineworld_token');
              tokenRef.current = null;
              clearApiCache();
              if (logoutRef.current) logoutRef.current();
            }
            return Promise.reject(error);
          }
        }

        // Retry once on network error or 5xx (not on 4xx)
        if (!config._retried && (!error.response || error.response.status >= 500)) {
          config._retried = true;
          await new Promise(r => setTimeout(r, 1000));
          return instance(config);
        }

        return Promise.reject(error);
      }
    );

    return instance;
  }, []);

  // Auto-login on app load
  useEffect(() => {
    if (token) {
      api.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('cineworld_token');
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token, api]);

  const login = async (email, password, remember_me = true) => {
    const res = await api.post('/auth/login', { email, password, remember_me });
    localStorage.setItem('cineworld_token', res.data.access_token);
    if (res.data.user?.language) {
      localStorage.setItem('cineworld_lang', res.data.user.language);
    }
    setToken(res.data.access_token);
    setUser(res.data.user);
    clearApiCache();
    return res.data;
  };

  const register = async (data) => {
    const res = await api.post('/auth/register', data);
    localStorage.setItem('cineworld_token', res.data.access_token);
    if (res.data.user?.language) {
      localStorage.setItem('cineworld_lang', res.data.user.language);
    }
    setToken(res.data.access_token);
    setUser(res.data.user);
    clearApiCache();
    return res.data;
  };

  const logout = useCallback(() => {
    localStorage.removeItem('cineworld_token');
    setToken(null);
    setUser(null);
    clearApiCache();
  }, []);

  // Keep logoutRef in sync for interceptor
  logoutRef.current = logout;

  const updateFunds = (newFunds) => {
    setUser(prev => ({ ...prev, funds: newFunds }));
  };

  const refreshUser = async () => {
    const res = await api.get('/auth/me');
    setUser(res.data);
  };

  // Cached GET - for read-only endpoints
  const cachedGet = useCallback(async (url) => {
    const cached = getCached(url);
    if (cached) return { data: cached };
    const res = await api.get(url);
    setCache(url, res.data);
    return res;
  }, [api]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, token, api, updateFunds, refreshUser, cachedGet }}>
      {children}
    </AuthContext.Provider>
  );
};

// Language Provider - Solo italiano (forced to Italian only)
export const LanguageProvider = ({ children }) => {
  const [language] = useState('it');
  const [translations, setTranslations] = useState({});

  // setLanguage is a no-op since language is forced to Italian
  const setLanguage = () => {};

  useEffect(() => {
    localStorage.setItem('cineworld_lang', 'it');
    axios.get(`${API}/translations/it`)
      .then(res => setTranslations(res.data))
      .catch(() => {});
  }, []);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, translations }}>
      {children}
    </LanguageContext.Provider>
  );
};


// Player Popup Context - allows any component to open a player profile popup
export const PlayerPopupContext = React.createContext({ openPlayerPopup: () => {} });
export const usePlayerPopup = () => React.useContext(PlayerPopupContext);
