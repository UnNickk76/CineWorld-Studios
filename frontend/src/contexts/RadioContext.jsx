// CineWorld Studio's — Global Radio Context
// Manages audio playback, current station, volume, and promo banner state.

import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const RadioContext = createContext(null);
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export function RadioProvider({ children }) {
  const [stations, setStations] = useState([]);
  const [currentStation, setCurrentStation] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [volume, setVolume] = useState(0.7);
  const [loading, setLoading] = useState(false);
  const [banner, setBanner] = useState({ should_show: false, discount_percent: 80 });
  const audioRef = useRef(null);

  // Initialize audio element
  useEffect(() => {
    const audio = new Audio();
    audio.crossOrigin = 'anonymous';
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
  }, []);

  // Sync volume
  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = volume;
  }, [volume]);

  // Fetch stations on mount (only if user is logged in — check via localStorage token)
  const loadStations = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await axios.get(`${API}/radio/stations`, { headers: { Authorization: `Bearer ${token}` } });
      setStations(res.data.stations || []);
    } catch (e) {
      console.warn('Radio stations fetch failed', e);
    }
  }, []);

  const loadBanner = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;
      const res = await axios.get(`${API}/radio/banner`, { headers: { Authorization: `Bearer ${token}` } });
      setBanner(res.data);
    } catch (e) {
      console.warn('Radio banner fetch failed', e);
    }
  }, []);

  useEffect(() => {
    loadStations();
    loadBanner();
  }, [loadStations, loadBanner]);

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
      const token = localStorage.getItem('token');
      await axios.post(`${API}/radio/dismiss-banner`, {}, { headers: { Authorization: `Bearer ${token}` } });
      setBanner(b => ({ ...b, should_show: false, status: 'dismissed' }));
    } catch (e) {
      console.warn('Dismiss failed', e);
      setBanner(b => ({ ...b, should_show: false }));
    }
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
