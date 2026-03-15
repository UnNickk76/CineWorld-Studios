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
      timeout: 120000
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

  const login = async (email, password, remember_me = true) => {
    const res = await api.post('/auth/login', { email, password, remember_me });
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
