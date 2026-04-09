import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
import { useNotifications } from './NotificationProvider';

export function NotificationBell() {
  const navigate = useNavigate();
  const { unreadCount } = useNotifications();

  return (
    <button
      className="relative p-2 rounded-lg hover:bg-white/5 transition-colors"
      onClick={() => navigate('/notifications')}
      data-testid="notification-bell"
      aria-label="Notifiche"
    >
      <Bell className="w-5 h-5 text-gray-400" />
      {unreadCount > 0 && (
        <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] flex items-center justify-center rounded-full bg-red-500 text-white text-[9px] font-bold px-1 animate-in zoom-in" data-testid="notification-badge">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  );
}
