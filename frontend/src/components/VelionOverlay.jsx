import React, { useState, useEffect, useContext, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { AuthContext } from '../contexts';
import { useLocation } from 'react-router-dom';
import { useDraggable } from '../hooks/useDraggable';

const VELION_SIZE = 72;
const LS_KEY = 'velion_visible';
const POLL_INTERVAL = 600000; // 10 minutes — re-check stato giocatore
const BUBBLE_COOLDOWN = 1800000; // 30 minutes between bubbles — meno invasivo
const HIGH_PRIORITY_TYPES = new Set([
  'stuck_film', 'countdown_imminent', 'countdown', 'low_hype', 'high_hype',
  'quota_full', 'live_action_ready', 'live_action_close',
]);

export const VelionOverlay = ({ onClick, onDismiss, onBubbleClick, onHelpClick, mode }) => {
  const { api, user } = useContext(AuthContext);
  const location = useLocation();
  const [hovered, setHovered] = useState(false);
  const [visible, setVisible] = useState(() => {
    const saved = localStorage.getItem(LS_KEY);
    return saved === null ? true : saved === 'true';
  });
  const [bubble, setBubble] = useState(null);
  const [hasAlert, setHasAlert] = useState(false);
  const [lastBubbleType, setLastBubbleType] = useState(null);
  const lastActivityRef = React.useRef(Date.now());
  const idleMinutesRef = React.useRef(0);
  const isOff = mode === 'off';
  // Drag hook — shared position between recall & full states
  const { dragProps, wasDragged } = useDraggable({
    storageKey: 'cw_velion_pos',
    size: VELION_SIZE,
  });

  // Track user activity
  useEffect(() => {
    const resetActivity = () => { lastActivityRef.current = Date.now(); idleMinutesRef.current = 0; };
    const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];
    events.forEach(e => window.addEventListener(e, resetActivity, { passive: true }));
    const idleCheck = setInterval(() => {
      idleMinutesRef.current = Math.floor((Date.now() - lastActivityRef.current) / 60000);
    }, 30000);
    return () => {
      events.forEach(e => window.removeEventListener(e, resetActivity));
      clearInterval(idleCheck);
    };
  }, []);

  useEffect(() => {
    localStorage.setItem(LS_KEY, String(visible));
  }, [visible]);

  const handleDismiss = (e) => {
    e.stopPropagation();
    setVisible(false);
    onDismiss?.();
  };

  useEffect(() => {
    const handler = () => setVisible(true);
    window.addEventListener('velion-show', handler);
    return () => window.removeEventListener('velion-show', handler);
  }, []);

  // Poll player status (only when ON)
  const lastBubbleTime = React.useRef(0);
  const recentBubbleTypes = React.useRef(new Set());
  const fetchTriggers = useCallback(async (forceImportant = false) => {
    if (!api || !user || isOff) return;
    // Don't show new bubble within cooldown period — UNLESS forceImportant (es. cambio pagina con quota piena)
    if (!forceImportant && Date.now() - lastBubbleTime.current < BUBBLE_COOLDOWN) return;
    try {
      const currentPage = location.pathname;
      const idle = idleMinutesRef.current;
      const res = await api.get(`/velion/player-status?page=${encodeURIComponent(currentPage)}&idle_minutes=${idle}`);
      const advisor = res.data?.advisor;

      // Only show high-priority, non-duplicate advisors
      if (advisor && HIGH_PRIORITY_TYPES.has(advisor.type) && !recentBubbleTypes.current.has(advisor.type)) {
        lastBubbleTime.current = Date.now();
        recentBubbleTypes.current.add(advisor.type);
        // Clear recent types after 30 min to allow re-showing
        setTimeout(() => recentBubbleTypes.current.delete(advisor.type), 1800000);
        setBubble(advisor);
        setHasAlert(advisor.priority === 'high');
        setLastBubbleType(advisor.type);
        setTimeout(() => setBubble(null), 10000);
      } else {
        setHasAlert(false);
      }
    } catch {
      // silent
    }
  }, [api, user, location.pathname, isOff]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!user || !api || isOff) return;
    const initTimer = setTimeout(fetchTriggers, 3000);
    const interval = setInterval(fetchTriggers, POLL_INTERVAL);
    return () => { clearTimeout(initTimer); clearInterval(interval); };
  }, [user, api, fetchTriggers, isOff]);

  // Login greeting (only when ON)
  useEffect(() => {
    if (!user || !api || isOff) return;
    const sessionKey = `velion_greeted_${user.id}`;
    if (sessionStorage.getItem(sessionKey)) return;
    sessionStorage.setItem(sessionKey, 'true');
    const greetTimer = setTimeout(async () => {
      try {
        const res = await api.get('/velion/login-greeting');
        const msg = res.data?.message;
        if (msg) {
          setBubble({ type: 'login_greeting', message: msg, priority: 'high', action: null });
          setHasAlert(true);
          setTimeout(() => setBubble(null), 12000);
        }
      } catch {}
    }, 4000);
    return () => clearTimeout(greetTimer);
  }, [user, api, isOff]);

  // Clear bubble on page change + immediately re-check for critical context (es. quota piena)
  useEffect(() => {
    if (!user || !api || isOff) return;
    setBubble(null);
    // Re-check al cambio pagina ma SOLO se entriamo in una pagina di creazione/produzione,
    // dove serve avvisare immediatamente di blocchi (quota satura, requisiti live action mancanti)
    const path = (location.pathname || '').toLowerCase();
    const isProductionPage = ['/pipeline-v3', '/create-film', '/create-series', '/create-anime',
                              '/create-sequel', '/create-live-action'].some(p => path.startsWith(p));
    if (isProductionPage) {
      const t = setTimeout(() => fetchTriggers(true), 1500);
      return () => clearTimeout(t);
    }
  }, [location.pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  // Clear bubble when switching to OFF
  useEffect(() => {
    if (isOff) { setBubble(null); setHasAlert(false); }
  }, [isOff]);

  const handleBubbleClick = () => {
    const action = bubble?.action;
    setBubble(null);
    setHasAlert(false);
    if (action === 'open-studio') {
      window.dispatchEvent(new Event('velion-open-studio'));
    } else if (onBubbleClick && action) {
      onBubbleClick(action);
    } else {
      onClick?.();
    }
  };

  // Listen for frontend-triggered revenue notification
  useEffect(() => {
    const handler = (e) => {
      if (isOff) return;
      const msg = e.detail?.message || 'Hai incassi da riscuotere! Apri lo studio.';
      setBubble({ type: 'revenue_alert', message: msg, priority: 'high', action: 'open-studio' });
      setHasAlert(true);
      setTimeout(() => setBubble(null), 10000);
    };
    window.addEventListener('velion-revenue-notify', handler);
    return () => window.removeEventListener('velion-revenue-notify', handler);
  }, [isOff]);

  if (!visible) return (
    <motion.button
      onClick={() => setVisible(true)}
      className="fixed bottom-20 right-2 z-50 sm:bottom-6 sm:right-5 w-10 h-10 rounded-full bg-[#0d1117]/90 border border-cyan-500/30 flex items-center justify-center hover:border-cyan-400/60 hover:bg-[#0d1117] transition-colors"
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 0.7 }}
      whileHover={{ scale: 1.1, opacity: 1 }}
      whileTap={{ scale: 0.9 }}
      data-testid="velion-recall"
      title="Richiama Velion"
    >
      <img src="/velion.png" alt="" className="w-7 h-7 object-contain rounded-full opacity-50" style={{ filter: 'brightness(0.8) saturate(0.4)' }} />
    </motion.button>
  );

  return (
    <>
      {/* Bubble notification - swipeable */}
      <AnimatePresence>
        {bubble && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1, x: 0 }}
            exit={{ opacity: 0, x: 200, scale: 0.9 }}
            transition={{ type: 'spring', damping: 22 }}
            drag="x"
            dragConstraints={{ left: 0, right: 0 }}
            dragElastic={0.3}
            onDragEnd={(e, info) => {
              if (info.offset.x > 80) {
                setBubble(null);
                setHasAlert(false);
              }
            }}
            className="fixed bottom-[180px] right-2 z-[52] sm:bottom-[96px] sm:right-5 max-w-[220px] sm:max-w-[240px] cursor-pointer touch-pan-y"
            onClick={handleBubbleClick}
            data-testid="velion-bubble"
          >
            <div className={`backdrop-blur-md rounded-xl px-3 py-2.5 shadow-lg ${
              bubble.priority === 'high'
                ? 'bg-[#0d0d10]/95 border border-cyan-400/40 shadow-cyan-500/10'
                : bubble.priority === 'low'
                ? 'bg-[#0d0d10]/90 border border-white/10 shadow-white/5'
                : 'bg-[#0d0d10]/95 border border-cyan-500/30 shadow-cyan-500/5'
            }`}>
              <p className="text-[11px] sm:text-[12px] text-gray-200 leading-snug">{bubble.message}</p>
              <div className="mt-1 flex items-center justify-between">
                <span className="text-[8px] text-gray-600">Swipe per eliminare</span>
                <span className={`text-[9px] ${bubble.priority === 'low' ? 'text-gray-500' : 'text-cyan-400/60'}`}>
                  {bubble.action ? 'Tocca per andare' : 'Tocca per dettagli'}
                </span>
              </div>
            </div>
            {/* Arrow pointing to Velion */}
            <div className={`absolute -bottom-1.5 right-6 w-3 h-3 rotate-45 ${
              bubble.priority === 'high'
                ? 'bg-[#0d0d10]/95 border-r border-b border-cyan-400/40'
                : bubble.priority === 'low'
                ? 'bg-[#0d0d10]/90 border-r border-b border-white/10'
                : 'bg-[#0d0d10]/95 border-r border-b border-cyan-500/30'
            }`} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Velion character (wrapped in drag handle) */}
      <div
        {...dragProps}
        className="fixed bottom-20 right-2 z-50 sm:bottom-6 sm:right-5"
        style={{ width: VELION_SIZE, height: VELION_SIZE, ...dragProps.style }}
      >
      <motion.div
        style={{ width: '100%', height: '100%', position: 'relative' }}
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0, opacity: 0 }}
        transition={{ type: 'spring', stiffness: 260, damping: 20, delay: 1 }}
      >
        {/* Dismiss X */}
        <button
          onClick={handleDismiss}
          data-no-drag="true"
          className="absolute -top-2 -left-2 z-30 w-5 h-5 rounded-full bg-gray-800 border border-gray-600 flex items-center justify-center hover:bg-red-600 hover:border-red-500 transition-colors"
          data-testid="velion-dismiss"
        >
          <X className="w-3 h-3 text-gray-300" />
        </button>

        {/* Help ? */}
        {onHelpClick && (
          <button
            onClick={(e) => { e.stopPropagation(); onHelpClick(); }}
            data-no-drag="true"
            className="absolute -top-2 -right-2 z-30 w-5 h-5 rounded-full bg-gray-800 border border-yellow-500/40 flex items-center justify-center hover:bg-yellow-500/20 hover:border-yellow-500/60 transition-colors"
            data-testid="velion-help-btn"
          >
            <span className="text-[9px] font-bold text-yellow-400">?</span>
          </button>
        )}

        {/* Clickable area */}
        <motion.button
          onClick={(e) => { if (wasDragged()) { e.preventDefault(); return; } onClick?.(); }}
          data-no-drag="true"
          onMouseEnter={() => setHovered(true)}
          onMouseLeave={() => setHovered(false)}
          className="w-full h-full cursor-pointer relative"
          whileHover={{ scale: 1.12 }}
          whileTap={{ scale: 0.9 }}
          data-testid="velion-overlay"
          title="Velion (trascinami)"
        >
          <div
            className="absolute inset-0 rounded-full"
            style={{ background: 'radial-gradient(circle, rgba(0,30,60,0.9) 40%, rgba(0,20,50,0.5) 70%, transparent 100%)' }}
          />
          {/* Glow ring */}
          <motion.div
            className="absolute inset-[-3px] rounded-full"
            style={{
              background: hasAlert
                ? 'conic-gradient(from 0deg, rgba(0,255,200,0.6), rgba(0,180,255,0.2), rgba(0,255,200,0.6))'
                : isOff
                ? 'conic-gradient(from 0deg, rgba(100,100,120,0.3), rgba(60,60,80,0.1), rgba(100,100,120,0.3))'
                : 'conic-gradient(from 0deg, rgba(0,180,255,0.4), rgba(0,100,255,0.1), rgba(0,180,255,0.4))',
              filter: hasAlert ? 'blur(4px)' : 'blur(3px)'
            }}
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: hasAlert ? 3 : 6, ease: 'linear' }}
          />
          {/* Breathing animation */}
          <motion.div
            className="absolute inset-0 rounded-full"
            animate={{ scale: isOff ? 1 : [1, 1.04, 1] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
          >
            <img
              src="/velion.png"
              alt=""
              loading="eager"
              onError={(e) => { e.target.style.display = 'none'; }}
              className="w-full h-full object-contain rounded-full relative z-10 pointer-events-none"
              style={{
                mixBlendMode: 'screen',
                filter: isOff
                  ? 'brightness(1.0) contrast(1.1) saturate(0.5)'
                  : 'brightness(1.4) contrast(1.3) saturate(1.2)'
              }}
            />
          </motion.div>
          {/* Notification dot (only when ON and has alert) */}
          <AnimatePresence>
            {!isOff && (hasAlert || !hovered) && (
              <motion.div
                className="absolute -top-0.5 -right-0.5 w-3 h-3 rounded-full z-20 border-2 border-[#0a0a0b]"
                style={{ background: hasAlert ? 'linear-gradient(135deg, #00ffcc, #00ddff)' : 'linear-gradient(135deg, #00ddff, #0088ff)' }}
                animate={{ scale: [1, 1.25, 1] }}
                transition={{ repeat: Infinity, duration: hasAlert ? 1 : 2 }}
                exit={{ scale: 0, opacity: 0 }}
              />
            )}
          </AnimatePresence>
          {/* Hover tooltip */}
          <AnimatePresence>
            {hovered && (
              <motion.div
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 8 }}
                className="absolute right-full mr-2 top-1/2 -translate-y-1/2 whitespace-nowrap bg-[#0d1117]/95 border border-cyan-500/40 text-cyan-300 text-[11px] px-2.5 py-1.5 rounded-lg font-['Bebas_Neue'] tracking-widest"
              >
                {isOff ? 'Velion (OFF)' : 'Chiedi a Velion'}
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </motion.div>
      </div>
    </>
  );
};
