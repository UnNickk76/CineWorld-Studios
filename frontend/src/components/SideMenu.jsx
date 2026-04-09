// CineWorld - Side Menu (Slide-in from left)
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useProductionMenu } from '../contexts';

const SideMenu = ({ open, setOpen }) => {
  const navigate = useNavigate();
  const { setIsOpen: openProductionMenu } = useProductionMenu();

  const go = (path) => { setOpen(false); navigate(path); };
  const goProduci = () => { setOpen(false); openProductionMenu(true); };

  const menuItems = [
    { icon: "\uD83C\uDFAC", label: "Produci", action: goProduci },
    { icon: "\u270D\uFE0F", label: "Sceneggiature", action: () => go('/emerging-screenplays') },
    { icon: "\uD83C\uDFEA", label: "Mercato", action: () => go('/marketplace') },
    { icon: "\uD83D\uDCFA", label: "Le mie TV", action: () => go('/my-tv') },
    { icon: "\uD83C\uDFD7\uFE0F", label: "Infrastrutture", action: () => go('/infrastructure') },
    { icon: "\uD83C\uDFAE", label: "Minigiochi + Sfide", action: () => go('/minigiochi') },
    { icon: "\uD83C\uDFC6", label: "Contest", action: () => go('/games') },
    { icon: "\uD83C\uDFAF", label: "Arena", action: () => go('/pvp-arena') },
    { icon: "\uD83C\uDF9F\uFE0F", label: "Festival", action: () => go('/festivals') },
  ];

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
        <div className="flex flex-col h-full pt-16 px-1.5 gap-1.5 pb-20 overflow-y-auto" style={{ scrollbarWidth: 'none' }}>
          {menuItems.map(item => (
            <button
              key={item.label}
              className="flex flex-col items-center justify-center min-h-[60px] rounded-lg border border-white/10 text-white text-[10px] active:scale-95 transition-all hover:bg-white/5 hover:border-white/20"
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
