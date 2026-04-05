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
const CACHE_TTL = 120000; // 2 minutes
const inflightRequests = new Map(); // deduplication

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

export const clearApiCache = () => { apiCache.clear(); inflightRequests.clear(); };

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
      timeout: 12000
    });

    let logoutScheduled = false;
    let logoutTimer = null;

    // Request interceptor - add token
    instance.interceptors.request.use(config => {
      const t = tokenRef.current;
      if (t) config.headers.Authorization = `Bearer ${t}`;
      return config;
    });

    // Response interceptor - handle 401 + retry on network error
    instance.interceptors.response.use(
      (response) => {
        // Any successful response cancels pending logout
        if (logoutTimer) {
          clearTimeout(logoutTimer);
          logoutTimer = null;
          logoutScheduled = false;
        }
        return response;
      },
      async (error) => {
        const config = error.config;

        // 401 = token expired/invalid → schedule logout with debounce
        // Skip auth endpoints to avoid logout loop during login
        if (error.response?.status === 401) {
          const url = config?.url || '';
          const isAuthEndpoint = url.includes('/auth/login') || url.includes('/auth/register') || url.includes('/auth/me');
          if (!isAuthEndpoint && !logoutScheduled) {
            // Debounced logout: wait 3 seconds for a successful response to cancel it
            // This handles parallel requests where some fail but others succeed
            logoutScheduled = true;
            logoutTimer = setTimeout(() => {
              // Double-check that token is still present (user didn't already logout)
              if (tokenRef.current) {
                // Verify token is truly invalid with a dedicated check
                instance.get('/auth/me').then(() => {
                  // Token is actually valid - cancel logout
                  logoutScheduled = false;
                }).catch((verifyErr) => {
                  if (verifyErr.response?.status === 401) {
                    // Confirmed: token is invalid
                    localStorage.removeItem('cineworld_token');
                    tokenRef.current = null;
                    clearApiCache();
                    if (logoutRef.current) logoutRef.current();
                  }
                  logoutScheduled = false;
                });
              } else {
                logoutScheduled = false;
              }
            }, 3000);
          }
          return Promise.reject(error);
        }

        // Retry once on network error or 5xx (not on 4xx)
        if (!config._retried && (!error.response || error.response.status >= 500)) {
          config._retried = true;
          await new Promise(r => setTimeout(r, 800));
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
        .catch((err) => {
          // Only clear token on definitive auth failures (401)
          // Network errors, timeouts, 5xx should NOT log the user out
          if (err.response?.status === 401) {
            localStorage.removeItem('cineworld_token');
            setToken(null);
            setUser(null);
          }
          // For other errors, keep token and user null - they can retry
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

  const guestLogin = async () => {
    const res = await api.post('/auth/guest');
    localStorage.setItem('cineworld_token', res.data.access_token);
    localStorage.setItem('cineworld_guest_start', Date.now().toString());
    setToken(res.data.access_token);
    setUser(res.data.user);
    clearApiCache();
    return res.data;
  };

  const convertGuest = async (data) => {
    const res = await api.post('/auth/convert', data);
    localStorage.removeItem('cineworld_guest_start');
    if (res.data.access_token) {
      localStorage.setItem('cineworld_token', res.data.access_token);
      setToken(res.data.access_token);
    }
    setUser(res.data.user);
    clearApiCache();
    return res.data;
  };

  const logout = useCallback(async () => {
    // If guest, call backend to delete guest data before clearing local state
    if (user?.is_guest) {
      try { await api.post('/auth/guest-logout'); } catch {}
    }
    localStorage.removeItem('cineworld_token');
    localStorage.removeItem('cw_guest_reg_tooltip');
    setToken(null);
    setUser(null);
    clearApiCache();
  }, [user?.is_guest]);

  // Keep logoutRef in sync for interceptor
  logoutRef.current = logout;

  const updateFunds = (newFunds) => {
    setUser(prev => ({ ...prev, funds: newFunds }));
  };

  const updateUser = (updates) => {
    setUser(prev => prev ? { ...prev, ...updates } : prev);
  };

  const refreshUser = async () => {
    const res = await api.get('/auth/me');
    setUser(res.data);
  };

  // Cached GET with deduplication - for read-only endpoints
  const cachedGet = useCallback(async (url) => {
    const cached = getCached(url);
    if (cached) return { data: cached };
    // Deduplicate in-flight requests
    if (inflightRequests.has(url)) return inflightRequests.get(url);
    const promise = api.get(url).then(res => {
      setCache(url, res.data);
      inflightRequests.delete(url);
      return res;
    }).catch(err => {
      inflightRequests.delete(url);
      throw err;
    });
    inflightRequests.set(url, promise);
    return promise;
  }, [api]);

  // Preload key pages data in background after login
  const preloadPages = useCallback(() => {
    if (!tokenRef.current) return;
    const endpoints = [
      '/film-pipeline/all',
      '/films/my',
      '/player/level-info',
      '/dashboard/batch',
      '/films/my/featured?limit=9',
    ];
    endpoints.forEach(url => {
      if (!getCached(url)) {
        api.get(url).then(res => setCache(url, res.data)).catch(() => {});
      }
    });
  }, [api]);

  // Trigger preload after user is loaded
  useEffect(() => {
    if (user && tokenRef.current) {
      preloadPages();
    }
  }, [user, preloadPages]);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, guestLogin, convertGuest, logout, token, api, updateFunds, updateUser, refreshUser, cachedGet }}>
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


// Production Menu Context - allows any component to open the production menu
export const ProductionMenuContext = React.createContext({ isOpen: false, setIsOpen: () => {} });
export const useProductionMenu = () => React.useContext(ProductionMenuContext);
