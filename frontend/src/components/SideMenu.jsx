// CineWorld - Side Menu (Slide-in from left)
import React, { useEffect, useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useProductionMenu, AuthContext } from '../contexts';

const SideMenu = ({ open, setOpen }) => {
  const navigate = useNavigate();
  const { setIsOpen: openProductionMenu } = useProductionMenu();
  const { api } = useContext(AuthContext);
  const [categories, setCategories] = useState({ has_strutture: false, has_agenzia: false, has_strategico: false });

  useEffect(() => {
    if (open && api) {
      api.get('/infrastructure/owned-categories').then(r => setCategories(r.data)).catch(() => {});
    }
  }, [open, api]);

  const go = (path) => { setOpen(false); navigate(path); };
  const goProduci = () => { setOpen(false); openProductionMenu(true); };

  const menuItems = [
    // — Produzione —
    { icon: "\uD83C\uDFAC", label: "Produci", action: goProduci, always: true },
    { icon: "\u270D\uFE0F", label: "Sceneggiature", action: () => go('/emerging-screenplays'), always: true },
    { icon: "\uD83C\uDFA5", label: "I Miei Film", action: () => go('/films?tab=film'), always: true },
    { icon: "\uD83D\uDCD6", label: "Saghe", action: () => go('/sagas'), always: true },

    // — Mia rete —
    { icon: "\uD83D\uDCFA", label: "Le mie TV", action: () => go('/my-tv'), always: true },
    { icon: "\uD83C\uDFEA", label: "Mercato", action: () => go('/marketplace'), always: true },
    { icon: "\uD83C\uDFD7\uFE0F", label: "Infrastrutture", action: () => go('/infrastructure'), always: true },
    { icon: "\uD83C\uDFE2", label: "Strutture", action: () => go('/strutture'), always: false, visible: categories.has_strutture },
    { icon: "\uD83D\uDC64", label: "Agenzia", action: () => go('/agenzia'), always: false, visible: categories.has_agenzia },
    { icon: "\uD83D\uDEE1\uFE0F", label: "Strategico", action: () => go('/strategico'), always: false, visible: categories.has_strategico },

    // — Stars & Casting —
    { icon: "\u2B50", label: "Stelle", action: () => go('/stars'), always: true },
    { icon: "\uD83C\uDFAD", label: "Casting", action: () => go('/casting-agency'), always: true },

    // — Competizioni —
    { icon: "\uD83C\uDFAF", label: "Arena", action: () => go('/pvp-arena'), always: true },
    { icon: "\uD83C\uDFC6", label: "Contest", action: () => go('/games'), always: true },
    { icon: "\uD83C\uDF9F\uFE0F", label: "Festival", action: () => go('/festivals'), always: true },
    { icon: "\uD83D\uDC51", label: "Major", action: () => go('/major'), always: true },
    { icon: "\uD83D\uDCCA", label: "Classifiche", action: () => go('/leaderboard'), always: true },

    // — Social / Info —
    { icon: "\uD83C\uDF10", label: "CineBoard", action: () => go('/social'), always: true },
    { icon: "\uD83D\uDCF0", label: "CineJournal", action: () => go('/journal'), always: true },
    { icon: "\u2728", label: "Eventi", action: () => go('/event-history'), always: true },
    { icon: "\uD83D\uDCAC", label: "Chat", action: () => go('/chat'), always: true },
    { icon: "\uD83D\uDD14", label: "Notifiche", action: () => go('/notifications'), always: true },

    // — Svago —
    { icon: "\uD83C\uDFAE", label: "Minigiochi", action: () => go('/minigiochi'), always: true },
    { icon: "\uD83C\uDFDE\uFE0F", label: "Parco 3D", action: () => go('/parco-studio'), always: true },

    // — Account —
    { icon: "\uD83D\uDC64", label: "Profilo", action: () => go('/profile'), always: true },
  ];

  const visibleItems = menuItems.filter(item => item.always || item.visible);

  return (
    <>
      <div
        className={`fixed inset-0 bg-black/40 z-40 transition-opacity duration-300 ${open ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"}`}
        onClick={() => setOpen(false)}
        data-testid="side-menu-overlay"
      />
      <div
        className={`fixed top-0 left-0 h-full w-[25%] min-w-[80px] max-w-[120px] bg-black/90 backdrop-blur-sm z-50 transform transition-transform duration-300 ${open ? "translate-x-0" : "-translate-x-full"}`}
        data-testid="side-menu"
      >
        {/* Close X button */}
        <button
          className="absolute top-3 right-2 w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-gray-400 hover:bg-white/20 hover:text-white transition-colors z-10"
          onClick={() => setOpen(false)}
          data-testid="side-menu-close"
        >
          <span className="text-xs leading-none">&times;</span>
        </button>
        <div className="flex flex-col h-full pt-12 px-1.5 gap-1.5 pb-20 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
          {visibleItems.map(item => (
            <button
              key={item.label}
              className={`flex flex-col items-center justify-center min-h-[60px] rounded-lg border text-white text-[10px] active:scale-95 transition-all hover:bg-white/5 ${
                !item.always ? 'border-white/15 bg-white/3 hover:border-white/25' : 'border-white/10 hover:border-white/20'
              }`}
              onClick={item.action}
              data-testid={`side-menu-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
            >
              <span className="text-base leading-none mb-1">{item.icon}</span>
              <span className="text-center leading-tight px-0.5">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
};

export default SideMenu;
