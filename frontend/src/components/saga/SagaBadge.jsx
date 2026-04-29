// CineWorld Studio's — SagaBadge
// Badge visuale per identificare i film appartenenti a una saga
// nei feed (Dashboard, Prossimamente, Cinema, ecc.)

import React from 'react';
import { BookOpen, Sparkles } from 'lucide-react';

export const SagaBadge = ({ chapterNumber, totalChapters, cliffhanger, size = 'sm', position = 'top-right' }) => {
  if (!chapterNumber) return null;

  const sizeMap = {
    xs: 'text-[9px] px-1.5 py-0.5 gap-0.5',
    sm: 'text-[10px] px-2 py-1 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1',
  };
  const iconSize = size === 'xs' ? 'w-2.5 h-2.5' : size === 'md' ? 'w-3.5 h-3.5' : 'w-3 h-3';

  const positionClass = {
    'top-right': 'top-1.5 right-1.5',
    'top-left': 'top-1.5 left-1.5',
    'bottom-right': 'bottom-1.5 right-1.5',
    'bottom-left': 'bottom-1.5 left-1.5',
    'inline': '',
  }[position] || '';

  const labelChapter = totalChapters ? `${chapterNumber}/${totalChapters}` : `${chapterNumber}`;

  return (
    <div
      className={`
        ${position !== 'inline' ? `absolute ${positionClass}` : 'inline-flex'}
        flex items-center font-bold
        bg-gradient-to-br from-amber-500 via-amber-600 to-amber-700
        text-amber-50 rounded-md shadow-lg shadow-amber-900/40
        ring-1 ring-amber-300/30 backdrop-blur-sm
        ${sizeMap[size]}
        z-10 select-none
      `}
      data-testid="saga-badge"
      title={`Capitolo ${chapterNumber}${totalChapters ? ` di ${totalChapters}` : ''} di una saga${cliffhanger ? ' (cliffhanger)' : ''}`}
    >
      <BookOpen className={iconSize} />
      <span className="leading-none">Cap. {labelChapter}</span>
      {cliffhanger && <Sparkles className={`${iconSize} text-yellow-200 animate-pulse`} />}
    </div>
  );
};

export default SagaBadge;
