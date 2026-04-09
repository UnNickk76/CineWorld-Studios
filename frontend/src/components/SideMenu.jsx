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
    { icon: "\uD83C\uDFAC", label: "Produci", action: goProduci, always: true },
    { icon: "\u270D\uFE0F", label: "Sceneggiature", action: () => go('/emerging-screenplays'), always: true },
    { icon: "\uD83C\uDFEA", label: "Mercato", action: () => go('/marketplace'), always: true },
    { icon: "\uD83D\uDCFA", label: "Le mie TV", action: () => go('/my-tv'), always: true },
    { icon: "\uD83C\uDFD7\uFE0F", label: "Infrastrutture", action: () => go('/infrastructure'), always: true },
    { icon: "\uD83C\uDFE2", label: "Strutture", action: () => go('/strutture'), always: false, visible: categories.has_strutture },
    { icon: "\uD83D\uDC64", label: "Agenzia", action: () => go('/agenzia'), always: false, visible: categories.has_agenzia },
    { icon: "\uD83D\uDEE1\uFE0F", label: "Strategico", action: () => go('/strategico'), always: false, visible: categories.has_strategico },
    { icon: "\uD83C\uDFAE", label: "Minigiochi", action: () => go('/minigiochi'), always: true },
    { icon: "\uD83C\uDFC6", label: "Contest", action: () => go('/games'), always: true },
    { icon: "\uD83C\uDFAF", label: "Arena", action: () => go('/pvp-arena'), always: true },
    { icon: "\uD83C\uDF9F\uFE0F", label: "Festival", action: () => go('/festivals'), always: true },
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
