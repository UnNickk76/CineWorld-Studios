// CineWorld Studio's - Shared Components
// Small reusable components used across multiple pages

import React from 'react';
import { usePlayerPopup } from '../contexts';

// Clickable Nickname - opens player popup on click
export const ClickableNickname = ({ userId, nickname, className = '' }) => {
  const { openPlayerPopup } = usePlayerPopup();
  if (!userId || !nickname) return <span className={className}>{nickname || '?'}</span>;
  return (
    <span 
      className={`cursor-pointer hover:text-cyan-400 hover:underline transition-colors ${className}`}
      onClick={(e) => { e.stopPropagation(); openPlayerPopup(userId); }}
      data-testid={`clickable-nickname-${userId}`}
    >
      {nickname}
    </span>
  );
};
