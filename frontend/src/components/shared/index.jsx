// CineWorld Studio's - Shared Components
// Small reusable components extracted from App.js

import React, { useContext } from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { SKILL_TRANSLATIONS } from '../constants';
import { LanguageContext } from '../contexts';

// Skill Badge Component
export const SkillBadge = ({ name, value, change, language = 'it' }) => {
  const getBgColor = () => {
    if (change > 0) return 'bg-green-500/20 border-green-500/30';
    if (change < 0) return 'bg-red-500/20 border-red-500/30';
    return 'bg-white/5 border-white/10';
  };
  
  // Translate skill name
  const translatedName = SKILL_TRANSLATIONS[name]?.[language] || SKILL_TRANSLATIONS[name]?.['en'] || name;

  return (
    <div className={`flex items-center justify-between px-1.5 py-0.5 rounded border ${getBgColor()}`}>
      <span className="text-xs truncate mr-1">{translatedName}</span>
      <div className="flex items-center gap-0.5">
        <span className={`font-bold text-xs ${change > 0 ? 'text-green-500' : change < 0 ? 'text-red-500' : ''}`}>
          {value}
        </span>
        {change > 0 && <TrendingUp className="w-2.5 h-2.5 text-green-500" />}
        {change < 0 && <TrendingDown className="w-2.5 h-2.5 text-red-500" />}
      </div>
    </div>
  );
};

// Film Quality Indicator
export const QualityIndicator = ({ score }) => {
  const getColor = () => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    if (score >= 40) return 'text-orange-500';
    return 'text-red-500';
  };

  return (
    <span className={`font-bold ${getColor()}`}>{score?.toFixed(0) || 0}%</span>
  );
};

// Revenue Display
export const RevenueDisplay = ({ amount, size = 'normal' }) => {
  const formatted = amount >= 1000000 
    ? `$${(amount / 1000000).toFixed(2)}M`
    : `$${amount?.toLocaleString() || 0}`;
  
  return (
    <span className={`text-green-500 font-bold ${size === 'large' ? 'text-xl' : ''}`}>
      {formatted}
    </span>
  );
};

// Film Status Badge
export const FilmStatusBadge = ({ status }) => {
  const getStyles = () => {
    switch (status) {
      case 'released':
        return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'in_theaters':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'completed':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'production':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  return (
    <span className={`px-2 py-0.5 text-xs rounded border ${getStyles()}`}>
      {status?.toUpperCase()}
    </span>
  );
};

// Sequel Badge
export const SequelBadge = ({ sequelNumber }) => {
  if (!sequelNumber || sequelNumber <= 0) return null;
  
  return (
    <span className="bg-purple-500/20 text-purple-400 border border-purple-500/30 px-1.5 py-0.5 text-[10px] font-bold rounded">
      SEQUEL #{sequelNumber}
    </span>
  );
};

// Tier Badge
export const TierBadge = ({ tier }) => {
  const getTierStyles = () => {
    switch (tier) {
      case 'S':
        return 'bg-gradient-to-r from-yellow-500 to-amber-500 text-black';
      case 'A':
        return 'bg-gradient-to-r from-purple-500 to-pink-500 text-white';
      case 'B':
        return 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white';
      case 'C':
        return 'bg-gradient-to-r from-green-500 to-emerald-500 text-white';
      case 'D':
        return 'bg-gradient-to-r from-orange-500 to-red-500 text-white';
      default:
        return 'bg-gray-500 text-white';
    }
  };

  return (
    <span className={`px-2 py-1 text-xs font-bold rounded ${getTierStyles()}`}>
      TIER {tier}
    </span>
  );
};

// Loading Spinner
export const LoadingSpinner = ({ size = 'md' }) => {
  const sizeClass = size === 'lg' ? 'w-8 h-8' : size === 'sm' ? 'w-4 h-4' : 'w-6 h-6';
  return (
    <div className={`animate-spin rounded-full border-2 border-yellow-500 border-t-transparent ${sizeClass}`} />
  );
};

// Empty State
export const EmptyState = ({ icon: Icon, title, description }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {Icon && <Icon className="w-12 h-12 text-gray-500 mb-4" />}
      <h3 className="text-lg font-semibold text-gray-300 mb-2">{title}</h3>
      {description && <p className="text-sm text-gray-500">{description}</p>}
    </div>
  );
};
