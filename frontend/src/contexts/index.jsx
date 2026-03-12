// CineWorld Studio's - Context Providers
// Extracted from App.js for better maintainability

import React, { createContext, useState, useEffect, useContext } from 'react';
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

// Auth Provider with auto-login
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const tokenRef = React.useRef(localStorage.getItem('cineworld_token'));
  const [token, setTokenState] = useState(tokenRef.current);

  const setToken = (t) => {
    tokenRef.current = t;
    setTokenState(t);
  };

  const api = React.useMemo(() => {
    const instance = axios.create({
      baseURL: API,
      timeout: 30000
    });
    instance.interceptors.request.use(config => {
      const t = tokenRef.current;
      if (t) config.headers.Authorization = `Bearer ${t}`;
      return config;
    });
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

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    localStorage.setItem('cineworld_token', res.data.access_token);
    if (res.data.user?.language) {
      localStorage.setItem('cineworld_lang', res.data.user.language);
    }
    setToken(res.data.access_token);
    setUser(res.data.user);
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
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem('cineworld_token');
    setToken(null);
    setUser(null);
  };

  const updateFunds = (newFunds) => {
    setUser(prev => ({ ...prev, funds: newFunds }));
  };

  const refreshUser = async () => {
    const res = await api.get('/auth/me');
    setUser(res.data);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, token, api, updateFunds, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

// Language Provider
export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(localStorage.getItem('cineworld_lang') || 'en');
  const [translations, setTranslations] = useState({});

  // Listen for localStorage changes (from login/register)
  useEffect(() => {
    const handleStorageChange = () => {
      const storedLang = localStorage.getItem('cineworld_lang');
      if (storedLang && storedLang !== language) {
        setLanguage(storedLang);
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    // Also check periodically for same-tab changes
    const interval = setInterval(() => {
      const storedLang = localStorage.getItem('cineworld_lang');
      if (storedLang && storedLang !== language) {
        setLanguage(storedLang);
      }
    }, 500);
    
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      clearInterval(interval);
    };
  }, [language]);

  useEffect(() => {
    axios.get(`${API}/translations/${language}`)
      .then(res => setTranslations(res.data))
      .catch(() => {});
    localStorage.setItem('cineworld_lang', language);
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, translations }}>
      {children}
    </LanguageContext.Provider>
  );
};


// Player Popup Context - allows any component to open a player profile popup
export const PlayerPopupContext = React.createContext({ openPlayerPopup: () => {} });
export const usePlayerPopup = () => React.useContext(PlayerPopupContext);
