import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Plus, X as XIcon } from 'lucide-react';
import {
  Pen, Tv, Building, Target, Coins, BookOpen, Star, User,
  Film, Trophy, Sparkles, Globe, BarChart3, Medal, Heart,
  Newspaper, Store, RadioTower, Gamepad2, Zap, Home, Award,
  Gift, Palette, Camera, Video, Music, Crown, Flame, Rocket,
  Briefcase, Users, Calendar, MapPin, Eye, Settings,
} from 'lucide-react';

/**
 * Full catalog of all commands users can place in their 8 custom slots.
 * key must be unique. Each entry: { key, icon, label, path }
 */
export const QUICK_COMMAND_CATALOG = [
  { key: 'screenplays', icon: Pen, label: 'Sceneggiature', path: '/emerging-screenplays' },
  { key: 'my-tv', icon: Tv, label: 'Le mie TV', path: '/my-tv' },
  { key: 'infrastructure', icon: Building, label: 'Infrastrutture', path: '/infrastructure' },
  { key: 'arena', icon: Target, label: 'Arena', path: '/pvp-arena' },
  { key: 'contest', icon: Coins, label: 'Contest', path: '/games' },
  { key: 'sagas', icon: BookOpen, label: 'Saghe', path: '/sagas' },
  { key: 'stars', icon: Star, label: 'Stelle', path: '/stars' },
  { key: 'profile', icon: User, label: 'Profilo', path: '/profile' },
  { key: 'my-films', icon: Film, label: 'I miei Film', path: '/films' },
  { key: 'leaderboard', icon: BarChart3, label: 'Classifiche', path: '/leaderboard' },
  { key: 'festivals', icon: Medal, label: 'Festival', path: '/festivals' },
  { key: 'cineboard', icon: Globe, label: 'CineBoard', path: '/social' },
  { key: 'journal', icon: Newspaper, label: 'CineJournal', path: '/journal' },
  { key: 'marketplace', icon: Store, label: 'Mercato', path: '/marketplace' },
  { key: 'minigames', icon: Gamepad2, label: 'Minigiochi', path: '/minigiochi' },
  { key: 'events', icon: Sparkles, label: 'Eventi', path: '/event-history' },
  { key: 'la-prima', icon: Trophy, label: 'La Prima', path: '/events/la-prima' },
  { key: 'home', icon: Home, label: 'Home', path: '/dashboard' },
  { key: 'produce', icon: Video, label: 'Produci', path: '/produce' },
  { key: 'studio', icon: Camera, label: 'Studio', path: '/studio' },
  { key: 'major', icon: Crown, label: 'Major', path: '/major' },
  { key: 'awards', icon: Award, label: 'Awards', path: '/awards' },
  { key: 'rewards', icon: Gift, label: 'Ricompense', path: '/rewards' },
  { key: 'directors', icon: Briefcase, label: 'Registi', path: '/directors' },
  { key: 'actors', icon: Users, label: 'Attori', path: '/actors' },
  { key: 'crew', icon: Users, label: 'Troupe', path: '/crew' },
  { key: 'calendar', icon: Calendar, label: 'Calendario', path: '/calendar' },
  { key: 'locations', icon: MapPin, label: 'Location', path: '/locations' },
  { key: 'soundtrack', icon: Music, label: 'Colonna Son.', path: '/soundtrack' },
  { key: 'art-dept', icon: Palette, label: 'Arte', path: '/art' },
  { key: 'radio', icon: RadioTower, label: 'Radio', path: '/radio' },
  { key: 'donate', icon: Heart, label: 'Dona', path: 'https://www.paypal.me/UnNickk', external: true },
  { key: 'chart', icon: Flame, label: 'Trending', path: '/trending' },
  { key: 'missions', icon: Rocket, label: 'Missioni', path: '/missions' },
  { key: 'watchlist', icon: Eye, label: 'Watchlist', path: '/watchlist' },
  { key: 'settings', icon: Settings, label: 'Impostazioni', path: '/settings' },
];

const DEFAULT_SLOTS = [
  'screenplays', 'my-tv', 'infrastructure', 'arena',
  'contest', 'sagas', 'stars', 'profile',
];

// Preset profiles users can apply with one tap in edit mode
export const QUICK_COMMAND_PRESETS = [
  {
    key: 'producer',
    label: 'Producer',
    emoji: '🎬',
    slots: ['produce', 'my-films', 'screenplays', 'my-tv', 'infrastructure', 'sagas', 'stars', 'profile'],
  },
  {
    key: 'networker',
    label: 'Networker',
    emoji: '🤝',
    slots: ['cineboard', 'journal', 'events', 'la-prima', 'leaderboard', 'marketplace', 'festivals', 'profile'],
  },
  {
    key: 'fighter',
    label: 'Arena',
    emoji: '⚔️',
    slots: ['arena', 'contest', 'minigames', 'leaderboard', 'missions', 'rewards', 'stars', 'profile'],
  },
  {
    key: 'star',
    label: 'Star',
    emoji: '⭐',
    slots: ['stars', 'awards', 'festivals', 'la-prima', 'leaderboard', 'my-films', 'trending', 'profile'],
  },
];

const STORAGE_KEY = 'cw_quick_commands_v1';

function loadSlots() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr) && arr.length === 8) return arr;
    }
  } catch {}
  return [...DEFAULT_SLOTS];
}

function saveSlots(slots) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(slots)); } catch {}
}

/**
 * QuickCommandsPanel — replaces the hardcoded "COMANDI RAPIDI" block.
 * - 8 user-customizable slots + central hamburger (side menu)
 * - Long-press (500ms) activates edit mode → small X badges on each slot
 *   - Tap X → opens picker with full command catalog (or removes)
 * - Empty slot (null) shows a "+" circle placeholder
 * - Persists in localStorage
 */
export default function QuickCommandsPanel({ onClose }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [slots, setSlots] = useState(loadSlots);
  const [editMode, setEditMode] = useState(false);
  const [pickerIdx, setPickerIdx] = useState(null); // which slot is being edited
  const longPressTimer = useRef(null);

  useEffect(() => { saveSlots(slots); }, [slots]);

  const catalogByKey = useMemo(() => {
    const m = {};
    for (const c of QUICK_COMMAND_CATALOG) m[c.key] = c;
    return m;
  }, []);

  const startLongPress = () => {
    if (longPressTimer.current) clearTimeout(longPressTimer.current);
    longPressTimer.current = setTimeout(() => {
      setEditMode(true);
      if (typeof navigator !== 'undefined' && navigator.vibrate) {
        try { navigator.vibrate(30); } catch {}
      }
    }, 500);
  };
  const cancelLongPress = () => {
    if (longPressTimer.current) { clearTimeout(longPressTimer.current); longPressTimer.current = null; }
  };

  const handleSlotClick = (idx) => {
    if (editMode) return; // in edit mode, clicks on slot body are ignored; only X does something
    const key = slots[idx];
    if (!key) {
      setPickerIdx(idx);
      return;
    }
    const entry = catalogByKey[key];
    if (!entry) return;
    if (entry.external) {
      window.open(entry.path, '_blank');
    } else {
      navigate(entry.path);
    }
    onClose?.();
  };

  const handleSlotRemoveOrPick = (idx) => {
    if (slots[idx]) {
      // Remove
      const next = [...slots]; next[idx] = null; setSlots(next);
    } else {
      // Pick
      setPickerIdx(idx);
    }
  };

  const pickFor = (idx, key) => {
    const next = [...slots];
    // Avoid duplicates: if key already present elsewhere, swap
    const existingIdx = next.indexOf(key);
    if (existingIdx !== -1 && existingIdx !== idx) {
      next[existingIdx] = next[idx] || null;
    }
    next[idx] = key;
    setSlots(next);
    setPickerIdx(null);
  };

  const openHamburger = () => {
    onClose?.();
    // Opens Titoli di Coda (credits-style full menu with all pages)
    window.dispatchEvent(new Event('open-titoli-di-coda'));
    if (typeof navigator !== 'undefined' && navigator.vibrate) try { navigator.vibrate(15); } catch {}
  };

  // Positions: 4 slots per row × 2 rows. Slot indices 0-3 (top), 4-7 (bottom).
  // Central hamburger spans the middle between top row slot 1,2 and bottom slot 5,6.
  return (
    <div
      className="bg-[#111113] border border-white/10 rounded-xl p-2 shadow-2xl relative"
      onPointerLeave={cancelLongPress}
      onPointerCancel={cancelLongPress}
      data-testid="quick-commands-panel-v2"
    >
      <div className="flex items-center justify-between px-2 mb-1.5">
        <p className="text-[9px] text-yellow-500/60 uppercase tracking-widest font-semibold">
          Comandi Rapidi {editMode && '· edita'}
        </p>
        {editMode && (
          <button
            onClick={() => setEditMode(false)}
            data-testid="qc-edit-done"
            className="text-[9px] text-emerald-400 font-bold uppercase px-2 py-0.5 rounded-full border border-emerald-500/40 hover:bg-emerald-500/10"
          >
            Fatto
          </button>
        )}
      </div>

      {/* Preset profiles (only visible in edit mode) */}
      {editMode && (
        <div className="flex gap-1 mb-2 px-1 overflow-x-auto pb-1" data-testid="qc-presets">
          <span className="text-[8px] text-gray-500 uppercase shrink-0 self-center mr-1">Preset:</span>
          {QUICK_COMMAND_PRESETS.map(p => (
            <button
              key={p.key}
              type="button"
              onClick={() => setSlots([...p.slots])}
              data-testid={`qc-preset-${p.key}`}
              aria-label={`Applica preset ${p.label}`}
              className="shrink-0 flex items-center gap-0.5 px-2 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/30 text-yellow-300 text-[9px] font-bold hover:bg-yellow-500/20 active:scale-95 transition"
            >
              <span>{p.emoji}</span>
              <span>{p.label}</span>
            </button>
          ))}
          <button
            type="button"
            onClick={() => setSlots([...DEFAULT_SLOTS])}
            data-testid="qc-preset-default"
            className="shrink-0 flex items-center gap-0.5 px-2 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400 text-[9px] font-bold hover:bg-white/10 active:scale-95 transition"
          >
            ↺ Default
          </button>
        </div>
      )}

      <div className="grid grid-cols-4 gap-1">
        {slots.map((key, idx) => {
          const entry = key ? catalogByKey[key] : null;
          const isActive = entry && location.pathname === entry.path;
          const Icon = entry?.icon;
          return (
            <div
              key={`slot-${idx}`}
              className="relative"
              onPointerDown={startLongPress}
              onPointerUp={cancelLongPress}
            >
              <button
                type="button"
                className={`flex flex-col items-center gap-0.5 py-2 w-full rounded-lg transition-all ${
                  isActive ? 'bg-yellow-500/15 text-yellow-400'
                  : entry ? 'text-gray-400 hover:bg-white/5'
                  : 'text-gray-600 border border-dashed border-white/10 hover:border-white/20'
                }`}
                onClick={() => handleSlotClick(idx)}
                data-testid={`qc-slot-${idx}`}
                aria-label={entry ? entry.label : `Slot ${idx+1} vuoto`}
              >
                {entry ? (
                  <>
                    <Icon className="w-4 h-4" />
                    <span className="text-[7px] leading-tight truncate max-w-full px-0.5">{entry.label}</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    <span className="text-[7px] leading-tight">Aggiungi</span>
                  </>
                )}
              </button>

              {editMode && entry && (
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); handleSlotRemoveOrPick(idx); }}
                  data-testid={`qc-slot-remove-${idx}`}
                  aria-label="Rimuovi comando"
                  className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-red-600 text-white flex items-center justify-center shadow-lg z-10 active:scale-90"
                  style={{ animation: 'qc-wiggle 0.4s ease-in-out infinite alternate' }}
                >
                  <XIcon className="w-2.5 h-2.5" strokeWidth={3} />
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Central hamburger — opens SideMenu */}
      <button
        onClick={openHamburger}
        data-testid="qc-hamburger-center"
        title="Apri Menu"
        aria-label="Apri Menu (hamburger)"
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 translate-y-[7px] w-11 h-11 rounded-full
                   bg-gradient-to-br from-blue-500 via-blue-600 to-blue-700
                   hover:brightness-110 border-2 border-white/30
                   shadow-xl shadow-blue-900/60
                   flex items-center justify-center
                   active:scale-90 transition
                   animate-[sideMenuPulse_2.4s_ease-in-out_infinite]"
      >
        <Menu className="w-5 h-5 text-white" strokeWidth={2.5} />
      </button>

      <style>{`
        @keyframes sideMenuPulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.7), 0 8px 20px rgba(30,64,175,0.5); }
          50% { box-shadow: 0 0 0 8px rgba(59,130,246,0), 0 8px 20px rgba(30,64,175,0.5); }
        }
        @keyframes qc-wiggle {
          0% { transform: rotate(-6deg) scale(1); }
          100% { transform: rotate(6deg) scale(1.05); }
        }
      `}</style>

      {/* Picker dialog */}
      {pickerIdx !== null && (
        <div
          className="fixed inset-0 bg-black/70 z-[70] flex items-end sm:items-center justify-center p-3"
          onClick={() => setPickerIdx(null)}
          data-testid="qc-picker-overlay"
        >
          <div
            className="bg-[#0f0f10] border border-yellow-500/25 rounded-xl w-full max-w-md max-h-[70vh] overflow-hidden flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between p-3 border-b border-white/10 shrink-0">
              <p className="text-[11px] font-bold text-yellow-400 uppercase tracking-wider">
                Scegli un comando · Slot {pickerIdx + 1}
              </p>
              <button
                type="button"
                onClick={() => setPickerIdx(null)}
                data-testid="qc-picker-close"
                className="text-gray-400 hover:text-white p-1"
                aria-label="Chiudi selettore"
              >
                <XIcon className="w-4 h-4" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 grid grid-cols-4 gap-1" data-testid="qc-picker-grid">
              {QUICK_COMMAND_CATALOG.map(c => {
                const Ic = c.icon;
                const picked = slots.includes(c.key);
                return (
                  <button
                    key={c.key}
                    type="button"
                    onClick={() => pickFor(pickerIdx, c.key)}
                    data-testid={`qc-picker-${c.key}`}
                    aria-label={c.label}
                    className={`flex flex-col items-center gap-1 py-2.5 rounded-lg transition ${
                      picked ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/40'
                             : 'text-gray-400 hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <Ic className="w-4 h-4" />
                    <span className="text-[8px] leading-tight text-center px-0.5">{c.label}</span>
                    {picked && <span className="text-[6px] text-yellow-500 font-black">GIÀ USATO</span>}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
