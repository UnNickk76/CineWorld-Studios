// CineWorld - Global Game Store with SWR (Stale-While-Revalidate)
// Provides instant navigation by keeping data in memory and revalidating in background

import React, { createContext, useContext, useCallback, useRef, useState, useEffect } from 'react';
import { AuthContext } from './index';

const GameStoreContext = createContext(null);

// SWR Cache - persists across navigations
const swrCache = new Map();
const SWR_STALE_MS = 30_000;  // 30s - show cached instantly, revalidate after this
const SWR_MAX_MS = 300_000;   // 5min - force refetch after this
const subscribers = new Map(); // key -> Set<callback>
const inflightSwr = new Map();

function getSwr(key) {
  return swrCache.get(key) || null;
}

function setSwr(key, data) {
  const entry = { data, ts: Date.now() };
  swrCache.set(key, entry);
  // Notify subscribers
  const subs = subscribers.get(key);
  if (subs) subs.forEach(cb => cb(data));
}

function subscribe(key, cb) {
  if (!subscribers.has(key)) subscribers.set(key, new Set());
  subscribers.get(key).add(cb);
  return () => subscribers.get(key)?.delete(cb);
}

function isStale(key) {
  const entry = swrCache.get(key);
  if (!entry) return true;
  return Date.now() - entry.ts > SWR_STALE_MS;
}

function isExpired(key) {
  const entry = swrCache.get(key);
  if (!entry) return true;
  return Date.now() - entry.ts > SWR_MAX_MS;
}

export function GameStoreProvider({ children }) {
  const { api, user } = useContext(AuthContext);
  const prefetchedRef = useRef(false);

  // SWR fetch: returns cached data instantly + revalidates in background
  const swrGet = useCallback(async (url, opts = {}) => {
    const { force = false, background = false } = opts;
    const cached = getSwr(url);

    // If we have cached data and it's not forced, return it immediately
    if (cached && !force && !isExpired(url)) {
      // Revalidate in background if stale
      if (isStale(url) && !inflightSwr.has(url)) {
        const bgPromise = api.get(url).then(res => {
          setSwr(url, res.data);
          inflightSwr.delete(url);
        }).catch(() => inflightSwr.delete(url));
        inflightSwr.set(url, bgPromise);
      }
      return cached.data;
    }

    // No cache or forced - fetch fresh
    if (inflightSwr.has(url) && !force) {
      await inflightSwr.get(url);
      const refreshed = getSwr(url);
      return refreshed?.data || null;
    }

    const promise = api.get(url).then(res => {
      setSwr(url, res.data);
      inflightSwr.delete(url);
      return res.data;
    }).catch(err => {
      inflightSwr.delete(url);
      // Return stale data on error
      if (cached) return cached.data;
      throw err;
    });

    if (!background) inflightSwr.set(url, promise);
    return promise;
  }, [api]);

  // Batch prefetch - fire and forget
  const prefetch = useCallback((urls) => {
    urls.forEach(url => {
      if (!getSwr(url) || isStale(url)) {
        if (!inflightSwr.has(url)) {
          const p = api.get(url).then(res => {
            setSwr(url, res.data);
            inflightSwr.delete(url);
          }).catch(() => inflightSwr.delete(url));
          inflightSwr.set(url, p);
        }
      }
    });
  }, [api]);

  // Invalidate specific keys (after mutations)
  const invalidate = useCallback((urls) => {
    const keys = Array.isArray(urls) ? urls : [urls];
    keys.forEach(k => {
      swrCache.delete(k);
      // Trigger background refetch
      if (!inflightSwr.has(k)) {
        const p = api.get(k).then(res => {
          setSwr(k, res.data);
          inflightSwr.delete(k);
        }).catch(() => inflightSwr.delete(k));
        inflightSwr.set(k, p);
      }
    });
  }, [api]);

  // Prefetch key game data after login
  useEffect(() => {
    if (!user || prefetchedRef.current) return;
    prefetchedRef.current = true;

    // Stagger prefetches to avoid burst
    const wave1 = ['/dashboard/batch', '/films/my/featured?limit=9', '/film-pipeline/all'];
    const wave2 = ['/films/my', '/pvp-cinema/arena', '/pvp-cinema/stats'];
    const wave3 = ['/player/level-info', '/genres', '/locations', '/film-pipeline/badges'];

    prefetch(wave1);
    setTimeout(() => prefetch(wave2), 1500);
    setTimeout(() => prefetch(wave3), 3000);
  }, [user, prefetch]);

  // Reset on logout
  useEffect(() => {
    if (!user) {
      swrCache.clear();
      inflightSwr.clear();
      prefetchedRef.current = false;
    }
  }, [user]);

  return (
    <GameStoreContext.Provider value={{ swrGet, prefetch, invalidate, subscribe: subscribe, getSwr }}>
      {children}
    </GameStoreContext.Provider>
  );
}

// Hook: use SWR data with auto-subscription
export function useSWR(url, opts = {}) {
  const { swrGet, subscribe: sub, getSwr: getEntry } = useContext(GameStoreContext);
  const { skip = false, deps = [] } = opts;
  const cached = url ? getSwr(url) : null;
  const [data, setData] = useState(cached?.data || null);
  const [loading, setLoading] = useState(!cached?.data);
  const mountedRef = useRef(true);

  useEffect(() => { mountedRef.current = true; return () => { mountedRef.current = false; }; }, []);

  // Subscribe to updates
  useEffect(() => {
    if (!url) return;
    return sub(url, (newData) => {
      if (mountedRef.current) setData(newData);
    });
  }, [url, sub]);

  // Fetch
  useEffect(() => {
    if (!url || skip) return;
    let cancelled = false;

    const fetchData = async () => {
      try {
        const result = await swrGet(url);
        if (!cancelled && mountedRef.current) {
          setData(result);
          setLoading(false);
        }
      } catch {
        if (!cancelled && mountedRef.current) setLoading(false);
      }
    };

    // If we have cached data, show it immediately (no loading state)
    const entry = getEntry(url);
    if (entry?.data) {
      setData(entry.data);
      setLoading(false);
      // Still revalidate in background
      swrGet(url).then(r => { if (!cancelled && mountedRef.current) setData(r); }).catch(() => {});
    } else {
      setLoading(true);
      fetchData();
    }

    return () => { cancelled = true; };
  }, [url, skip, swrGet, getEntry, ...deps]);

  const mutate = useCallback(async () => {
    if (!url) return;
    setLoading(true);
    try {
      const result = await swrGet(url, { force: true });
      if (mountedRef.current) { setData(result); setLoading(false); }
    } catch {
      if (mountedRef.current) setLoading(false);
    }
  }, [url, swrGet]);

  return { data, loading, mutate };
}

// Hook: prefetch on hover/focus for navigation links
export function usePrefetchOnHover(urls) {
  const { prefetch } = useContext(GameStoreContext);
  return useCallback(() => prefetch(Array.isArray(urls) ? urls : [urls]), [prefetch, urls]);
}

export function useGameStore() {
  return useContext(GameStoreContext);
}
