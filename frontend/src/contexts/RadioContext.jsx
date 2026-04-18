// CineWorld Studio's — Global Radio Context
// Manages audio playback, current station, volume, and promo banner state.

import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const RadioContext = createContext(null);
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const TOKEN_KEY = 'cineworld_token';

function authHeaders() {
  const t = localStorage.getItem(TOKEN_KEY);
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export function RadioProvider({ children }) {
  const [stations, setStations] = useState([]);
  const [currentStation, setCurrentStation] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [banner, setBanner] = useState({ should_show: false, discount_percent: 80, user_has_tv: false });
  // Track localStorage token changes so we can re-fetch after login
  const [tokenTick, setTokenTick] = useState(0);
  const audioRef = useRef(null);

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audio.preload = 'none';
    audio.volume = volume;
    audioRef.current = audio;

    const onPlaying = () => { setIsPlaying(true); setLoading(false); };
    const onPause = () => setIsPlaying(false);
    const onWaiting = () => setLoading(true);
    const onError = () => {
      setLoading(false);
      setIsPlaying(false);
      toast.error('Stream non disponibile, prova un\'altra radio');
    };
    audio.addEventListener('playing', onPlaying);
    audio.addEventListener('pause', onPause);
    audio.addEventListener('waiting', onWaiting);
    audio.addEventListener('error', onError);

    return () => {
      audio.pause();
      audio.src = '';
      audio.removeEventListener('playing', onPlaying);
      audio.removeEventListener('pause', onPause);
      audio.removeEventListener('waiting', onWaiting);
      audio.removeEventListener('error', onError);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Sync volume
  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
  }, [volume]);

  // Fetch stations/banner whenever token appears
  const loadStations = useCallback(async () => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) return;
    try {
      const res = await axios.get(`${API}/radio/stations`, { headers: authHeaders() });
      setStations(res.data.stations || []);
    } catch (e) {
      console.warn('Radio stations fetch failed', e?.response?.status);
    }
  }, []);

  const loadBanner = useCallback(async () => {
    const t = localStorage.getItem(TOKEN_KEY);
    if (!t) return;
    try {
      const res = await axios.get(`${API}/radio/banner`, { headers: authHeaders() });
      setBanner(res.data);
    } catch (e) {
      console.warn('Radio banner fetch failed', e?.response?.status);
    }
  }, []);

  // Re-fetch when token changes (storage event OR manual tick after login)
  useEffect(() => {
    loadStations();
    loadBanner();
    const onStorage = (e) => {
      if (e.key === TOKEN_KEY) setTokenTick(n => n + 1);
    };
    const onLogin = () => setTokenTick(n => n + 1);
    window.addEventListener('storage', onStorage);
    window.addEventListener('cineworld:login', onLogin);
    return () => {
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('cineworld:login', onLogin);
    };
  }, [loadStations, loadBanner, tokenTick]);

  // Retry fetch if either stations or banner are still empty
  useEffect(() => {
    const needsStations = stations.length === 0;
    const needsBanner = !banner?.status;
    if (!needsStations && !needsBanner) return;
    const interval = setInterval(() => {
      const t = localStorage.getItem(TOKEN_KEY);
      if (t) {
        if (needsStations) loadStations();
        if (needsBanner) loadBanner();
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [stations.length, banner?.status, loadStations, loadBanner]);

  const play = useCallback((station) => {
    if (!audioRef.current || !station?.url) return;
    setLoading(true);
    setCurrentStation(station);
    audioRef.current.src = station.url;
    audioRef.current.play().catch((err) => {
      setLoading(false);
      setIsPlaying(false);
      console.error('Play failed:', err);
      toast.error('Impossibile riprodurre questa radio');
    });
  }, []);

  const pause = useCallback(() => {
    if (audioRef.current) audioRef.current.pause();
  }, []);

  const resume = useCallback(() => {
    if (audioRef.current && audioRef.current.src) {
      setLoading(true);
      audioRef.current.play().catch(() => setLoading(false));
    }
  }, []);

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
    }
    setIsPlaying(false);
    setCurrentStation(null);
  }, []);

  const toggle = useCallback(() => {
    if (!currentStation && stations.length > 0) {
      play(stations[0]);
    } else if (isPlaying) {
      pause();
    } else {
      resume();
    }
  }, [currentStation, isPlaying, stations, play, pause, resume]);

  const next = useCallback(() => {
    if (!stations.length || !currentStation) return;
    const idx = stations.findIndex(s => s.id === currentStation.id);
    const nextSt = stations[(idx + 1) % stations.length];
    play(nextSt);
  }, [stations, currentStation, play]);

  const prev = useCallback(() => {
    if (!stations.length || !currentStation) return;
    const idx = stations.findIndex(s => s.id === currentStation.id);
    const prevSt = stations[(idx - 1 + stations.length) % stations.length];
    play(prevSt);
  }, [stations, currentStation, play]);

  const dismissBanner = useCallback(async () => {
    try {
      await axios.post(`${API}/radio/dismiss-banner`, {}, { headers: authHeaders() });
    } catch (e) {
      console.warn('Dismiss failed', e);
    }
    setBanner(b => ({ ...b, should_show: false, status: 'dismissed' }));
  }, []);

  const refreshBanner = useCallback(() => loadBanner(), [loadBanner]);

  return (
    <RadioContext.Provider value={{
      stations, currentStation, isPlaying, loading, volume,
      setVolume, play, pause, resume, stop, toggle, next, prev,
      banner, dismissBanner, refreshBanner,
    }}>
      {children}
    </RadioContext.Provider>
  );
}

export function useRadio() {
  const ctx = useContext(RadioContext);
  if (!ctx) throw new Error('useRadio must be used within RadioProvider');
  return ctx;
}
