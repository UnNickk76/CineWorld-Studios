/**
 * LiveActionTabs — header tab navigation per /create-live-action
 * Modalità: 'mine' | 'marketplace' | 'queue'
 */
import React from 'react';
import { Camera, Globe, Package } from 'lucide-react';

export default function LiveActionTabs({ active, onChange, queueCount = 0, marketCount = 0 }) {
  const tabs = [
    { id: 'mine', label: 'Mio', icon: Camera, color: 'pink' },
    { id: 'marketplace', label: 'Marketplace', icon: Globe, color: 'cyan', badge: marketCount },
    { id: 'queue', label: 'In coda', icon: Package, color: 'amber', badge: queueCount },
  ];
  return (
    <div className="flex gap-1 mb-4 sticky top-14 z-10 bg-black/95 py-2 -mx-4 px-4 backdrop-blur" data-testid="la-tabs">
      {tabs.map(t => {
        const Icon = t.icon;
        const isActive = active === t.id;
        return (
          <button
            key={t.id}
            onClick={() => onChange(t.id)}
            className={`flex-1 px-2 py-2 rounded-lg border text-[10px] font-bold flex items-center justify-center gap-1 transition-all relative ${
              isActive
                ? `bg-${t.color}-500/20 border-${t.color}-500/50 text-${t.color}-200`
                : 'bg-gray-900 border-gray-800 text-gray-400'
            }`}
            data-testid={`la-tab-${t.id}`}
          >
            <Icon className="w-3 h-3" />
            <span className="truncate">{t.label}</span>
            {t.badge > 0 && (
              <span className={`absolute -top-1 -right-1 min-w-[16px] h-4 px-1 rounded-full text-[8px] font-black flex items-center justify-center bg-red-500 text-white`}>
                {t.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
