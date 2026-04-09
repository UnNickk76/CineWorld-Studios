import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';
import { AuthContext } from '../contexts';

const NotifContext = createContext(null);

export function useNotifications() {
  return useContext(NotifContext);
}

const POLL_INTERVAL = 30000; // 30s poll for count
const POPUP_COOLDOWN = 30000; // 30s between popups
const POPUP_POLL_INTERVAL = 15000; // check popups every 15s

const CATEGORY_LABELS = {
  production: 'Produzione',
  tv_episodes: 'TV / Episodi',
  events: 'Eventi',
  economy: 'Economia',
  social: 'Social',
  infrastructure: 'Infrastrutture',
  arena: 'Arena / Major',
  minigames: 'Minigiochi',
};

const CATEGORY_ICONS = {
  production: 'film',
  tv_episodes: 'tv',
  events: 'calendar',
  economy: 'dollar-sign',
  social: 'heart',
  infrastructure: 'building',
  arena: 'swords',
  minigames: 'gamepad-2',
};

export function NotificationProvider({ children }) {
  const { api, user } = useContext(AuthContext);
  const [unreadCount, setUnreadCount] = useState(0);
  const [categoryStats, setCategoryStats] = useState({});
  const lastPopupRef = useRef(0);
  const isOnlineRef = useRef(true);
  const loginSuppressRef = useRef(true); // suppress popups on login

  // Track online status
  useEffect(() => {
    const handleOnline = () => { isOnlineRef.current = true; };
    const handleOffline = () => { isOnlineRef.current = false; };
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // After login, suppress popups for 5 seconds then enable
  useEffect(() => {
    if (!user) return;
    loginSuppressRef.current = true;
    const t = setTimeout(() => { loginSuppressRef.current = false; }, 5000);
    return () => clearTimeout(t);
  }, [user]);

  // Poll unread count
  const fetchCount = useCallback(async () => {
    if (!api || !user) return;
    try {
      const res = await api.get('/notifications/count');
      setUnreadCount(res.data.unread_count || 0);
    } catch {}
  }, [api, user]);

  // Poll category stats
  const fetchStats = useCallback(async () => {
    if (!api || !user) return;
    try {
      const res = await api.get('/notifications/stats');
      setCategoryStats(res.data.stats || {});
    } catch {}
  }, [api, user]);

  // Poll for popup notifications (only when online, not suppressed, and after cooldown)
  const checkPopups = useCallback(async () => {
    if (!api || !user || !isOnlineRef.current || loginSuppressRef.current) return;
    const now = Date.now();
    if (now - lastPopupRef.current < POPUP_COOLDOWN) return;

    try {
      const res = await api.get('/notifications/popup');
      const notifs = res.data.notifications || [];
      if (notifs.length === 0) return;

      lastPopupRef.current = Date.now();
      for (const n of notifs) {
        if (n.priority === 'high') {
          toast(n.title, {
            description: n.message,
            duration: 6000,
            className: 'bg-[#1A1A1C] border border-yellow-500/30 text-white',
          });
        } else if (n.priority === 'medium') {
          toast(n.title, {
            description: n.message,
            duration: 3500,
          });
        }
      }
      // Refresh count after showing popups
      fetchCount();
    } catch {}
  }, [api, user, fetchCount]);

  // Set up polling intervals
  useEffect(() => {
    if (!user) return;
    fetchCount();
    fetchStats();
    const countInterval = setInterval(fetchCount, POLL_INTERVAL);
    const popupInterval = setInterval(checkPopups, POPUP_POLL_INTERVAL);
    return () => {
      clearInterval(countInterval);
      clearInterval(popupInterval);
    };
  }, [user, fetchCount, fetchStats, checkPopups]);

  const refreshNotifications = useCallback(() => {
    fetchCount();
    fetchStats();
  }, [fetchCount, fetchStats]);

  return (
    <NotifContext.Provider value={{
      unreadCount,
      categoryStats,
      categoryLabels: CATEGORY_LABELS,
      categoryIcons: CATEGORY_ICONS,
      refreshNotifications,
    }}>
      {children}
    </NotifContext.Provider>
  );
}
