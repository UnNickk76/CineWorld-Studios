// CineWorld — Pull to Refresh for PWA
// Wrap your app content with this component for native-like pull-to-refresh

import React, { useState, useRef, useCallback } from 'react';

export function PullToRefresh({ children, onRefresh }) {
  const [pulling, setPulling] = useState(false);
  const [pullDistance, setPullDistance] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const startY = useRef(0);
  const isDragging = useRef(false);
  const THRESHOLD = 80;

  const handleTouchStart = useCallback((e) => {
    if (window.scrollY === 0) {
      startY.current = e.touches[0].clientY;
      isDragging.current = true;
    }
  }, []);

  const handleTouchMove = useCallback((e) => {
    if (!isDragging.current || refreshing) return;
    const diff = e.touches[0].clientY - startY.current;
    if (diff > 0 && window.scrollY === 0) {
      const dampened = Math.min(120, diff * 0.4);
      setPullDistance(dampened);
      setPulling(dampened > 10);
    }
  }, [refreshing]);

  const handleTouchEnd = useCallback(async () => {
    isDragging.current = false;
    if (pullDistance >= THRESHOLD && !refreshing) {
      setRefreshing(true);
      setPullDistance(50);
      try {
        if (onRefresh) await onRefresh();
        else window.location.reload();
      } catch { /* */ }
      setRefreshing(false);
    }
    setPullDistance(0);
    setPulling(false);
  }, [pullDistance, refreshing, onRefresh]);

  const progress = Math.min(1, pullDistance / THRESHOLD);
  const rotation = progress * 360;

  return (
    <div onTouchStart={handleTouchStart} onTouchMove={handleTouchMove} onTouchEnd={handleTouchEnd} style={{ position: 'relative' }}>
      {/* Pull indicator */}
      {(pulling || refreshing) && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, zIndex: 99998,
          display: 'flex', justifyContent: 'center', paddingTop: Math.max(8, pullDistance - 20),
          transition: refreshing ? 'padding-top 0.2s' : 'none',
          pointerEvents: 'none',
        }} data-testid="pull-to-refresh-indicator">
          <div style={{
            width: 32, height: 32, borderRadius: '50%',
            background: 'rgba(20,20,22,0.95)', border: '2px solid rgba(255,255,255,0.1)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
            transform: `rotate(${refreshing ? 0 : rotation}deg)`,
            transition: refreshing ? 'none' : 'transform 0.05s',
          }}>
            {refreshing ? (
              <svg width="16" height="16" viewBox="0 0 16 16" style={{ animation: 'ptr-spin 0.8s linear infinite' }}>
                <circle cx="8" cy="8" r="6" fill="none" stroke="#4ade80" strokeWidth="2" strokeDasharray="25 12" />
              </svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={progress >= 1 ? '#4ade80' : '#6b7280'} strokeWidth="2.5">
                <path d="M12 5v14M5 12l7 7 7-7" />
              </svg>
            )}
          </div>
        </div>
      )}
      <style>{`@keyframes ptr-spin { to { transform: rotate(360deg); } }`}</style>
      {children}
    </div>
  );
}
