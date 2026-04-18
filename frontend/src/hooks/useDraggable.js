// useDraggable — reusable drag hook for floating widgets.
// Works on touch + mouse, persists position per-key in localStorage,
// clamps to viewport, and distinguishes a drag from a click using a small
// movement threshold (so child buttons stay clickable).

import { useRef, useState, useCallback, useEffect } from 'react';

const PX_TO_CONSIDER_DRAG = 6;  // pointer movement before we call it a drag

export function useDraggable({ storageKey, defaultOffset = { x: 0, y: 0 }, size = 64, anchor = 'right' }) {
  const [offset, setOffset] = useState(() => {
    if (!storageKey) return defaultOffset;
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (typeof parsed?.x === 'number' && typeof parsed?.y === 'number') return parsed;
      }
    } catch {}
    return defaultOffset;
  });
  const [isDragging, setIsDragging] = useState(false);
  const startRef = useRef(null); // { pointerX, pointerY, offsetX, offsetY, suppressClick }

  const clamp = useCallback((x, y) => {
    const w = window.innerWidth || 375;
    const h = window.innerHeight || 812;
    const margin = 8;
    // Margine inferiore maggiorato: riserviamo ~80px sopra il bordo inferiore
    // in modo da non coprire mai la bottom-navbar.
    const bottomNavReserve = 80;
    // Horizontal bounds depend on anchor side
    let minX, maxX;
    if (anchor === 'left') {
      minX = 0;
      maxX = w - size - margin * 2;
    } else {
      minX = -(w - size - margin * 2);
      maxX = 0;
    }
    // Vertical: l'elemento è ancorato in basso; y negativo lo sposta verso l'alto.
    // Non si può andare più in basso di 0 (default position).
    const minY = -(h - size - margin * 2 - bottomNavReserve);
    const maxY = 0;
    return {
      x: Math.min(maxX, Math.max(minX, x)),
      y: Math.min(maxY, Math.max(minY, y)),
    };
  }, [size, anchor]);

  const onPointerDown = useCallback((e) => {
    // Don't start a drag if the user pressed on a button/input inside the widget
    if (e.target && e.target.closest && e.target.closest('[data-no-drag="true"]')) return;
    const pt = 'touches' in e && e.touches[0] ? e.touches[0] : e;
    startRef.current = {
      pointerX: pt.clientX,
      pointerY: pt.clientY,
      offsetX: offset.x,
      offsetY: offset.y,
      moved: 0,
    };
  }, [offset]);

  useEffect(() => {
    const onMove = (e) => {
      if (!startRef.current) return;
      const pt = 'touches' in e && e.touches[0] ? e.touches[0] : e;
      const dx = pt.clientX - startRef.current.pointerX;
      const dy = pt.clientY - startRef.current.pointerY;
      const moved = Math.hypot(dx, dy);
      startRef.current.moved = Math.max(startRef.current.moved, moved);
      if (moved > PX_TO_CONSIDER_DRAG) {
        if (!isDragging) setIsDragging(true);
        setOffset(clamp(startRef.current.offsetX + dx, startRef.current.offsetY + dy));
        if (e.cancelable && 'preventDefault' in e) e.preventDefault();
      }
    };
    const onUp = () => {
      if (startRef.current && startRef.current.moved > PX_TO_CONSIDER_DRAG) {
        // Persist final position
        if (storageKey) {
          try { localStorage.setItem(storageKey, JSON.stringify(offset)); } catch {}
        }
      }
      startRef.current = null;
      setIsDragging(false);
    };
    // Register pointer + mouse + touch for broad compat (Playwright only dispatches mouse/touch)
    window.addEventListener('pointermove', onMove, { passive: false });
    window.addEventListener('mousemove', onMove, { passive: false });
    window.addEventListener('touchmove', onMove, { passive: false });
    window.addEventListener('pointerup', onUp);
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchend', onUp);
    window.addEventListener('pointercancel', onUp);
    return () => {
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('touchmove', onMove);
      window.removeEventListener('pointerup', onUp);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchend', onUp);
      window.removeEventListener('pointercancel', onUp);
    };
  }, [isDragging, clamp, offset, storageKey]);

  // If the viewport is resized, re-clamp the stored offset
  useEffect(() => {
    const onResize = () => setOffset(o => clamp(o.x, o.y));
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, [clamp]);

  // Helper for children: prevent click-through right after a drag
  const wasDragged = () => startRef.current?.moved > PX_TO_CONSIDER_DRAG;

  return {
    offset,
    isDragging,
    wasDragged,
    // Spread these on the draggable wrapper
    dragProps: {
      onPointerDown,
      onMouseDown: onPointerDown,
      onTouchStart: onPointerDown,
      style: {
        transform: `translate3d(${offset.x}px, ${offset.y}px, 0)`,
        touchAction: 'none',
        cursor: isDragging ? 'grabbing' : 'grab',
      },
    },
  };
}
