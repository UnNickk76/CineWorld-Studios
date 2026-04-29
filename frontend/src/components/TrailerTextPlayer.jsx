import React, { useEffect, useState, useRef } from 'react';
import { X, FileText, Loader2 } from 'lucide-react';

/**
 * TrailerTextPlayer — modale full-screen con effetto typewriter cinematografico.
 * Stile: nero profondo + serif elegante + sezioni cadenzate.
 */
export default function TrailerTextPlayer({ textTrailer, contentTitle, onClose }) {
  const [revealedChars, setRevealedChars] = useState(0);
  const [done, setDone] = useState(false);
  const fullText = (textTrailer?.sections || []).join('\n\n');
  const totalChars = fullText.length;
  const tickRef = useRef(null);

  useEffect(() => {
    if (!fullText) return;
    setRevealedChars(0);
    setDone(false);
    const charsPerSec = Math.max(35, Math.min(70, totalChars / Math.max(15, textTrailer.duration_seconds || 25)));
    const intervalMs = 1000 / charsPerSec;
    let cur = 0;
    tickRef.current = setInterval(() => {
      cur += 1;
      if (cur >= totalChars) {
        setRevealedChars(totalChars);
        setDone(true);
        clearInterval(tickRef.current);
      } else {
        setRevealedChars(cur);
      }
    }, intervalMs);
    return () => clearInterval(tickRef.current);
  }, [fullText, totalChars, textTrailer?.duration_seconds]);

  const skip = () => {
    if (tickRef.current) clearInterval(tickRef.current);
    setRevealedChars(totalChars);
    setDone(true);
  };

  const display = fullText.slice(0, revealedChars);
  const sections = display.split('\n\n');
  const isRecap = !!textTrailer?.is_recap;

  return (
    <div
      className="fixed inset-0 z-[300] bg-black flex items-center justify-center p-4"
      onClick={skip}
      data-testid="trailer-text-player"
      style={{ background: 'radial-gradient(ellipse at center, #050505 0%, #000 100%)' }}
    >
      <button
        onClick={(e) => { e.stopPropagation(); onClose?.(); }}
        className="absolute top-3 right-3 w-9 h-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-zinc-400 hover:text-white hover:bg-white/10"
        data-testid="trailer-text-close"
      >
        <X className="w-4 h-4" />
      </button>

      {/* Subtle vignette + grain */}
      <div className="pointer-events-none absolute inset-0" style={{
        background: 'radial-gradient(ellipse at center, transparent 60%, rgba(0,0,0,0.95) 100%)',
      }} />

      <div className="relative max-w-2xl w-full text-center" style={{ fontFamily: 'Georgia, "Times New Roman", serif' }}>
        {isRecap && revealedChars > 0 && (
          <p className="text-amber-300/60 uppercase tracking-[0.3em] text-[9px] mb-6 animate-pulse">
            Previously on «{textTrailer.prev_title}»
          </p>
        )}
        <div className="space-y-8 text-white">
          {sections.map((section, i) => {
            const isLast = i === sections.length - 1;
            const isCommingSoon = section.toLowerCase().includes('coming soon') || section.toLowerCase().includes('prossimamente');
            return (
              <p
                key={i}
                className={`leading-relaxed ${isCommingSoon ? 'text-amber-300 text-2xl sm:text-3xl font-bold tracking-widest uppercase mt-12' : isLast ? 'text-amber-200/90 text-lg sm:text-xl italic' : 'text-zinc-100 text-base sm:text-lg italic'}`}
                style={{ textShadow: isCommingSoon ? '0 0 24px rgba(251,191,36,0.5)' : '0 0 8px rgba(255,255,255,0.15)' }}
              >
                {section}
                {!done && i === sections.length - 1 && <span className="inline-block w-0.5 h-5 bg-white/70 ml-1 animate-pulse" />}
              </p>
            );
          })}
        </div>

        {done && (
          <div className="mt-10 flex items-center justify-center gap-4">
            <button
              onClick={(e) => { e.stopPropagation(); onClose?.(); }}
              data-testid="trailer-text-end-btn"
              className="px-6 py-2.5 rounded-full bg-white/10 border border-white/20 text-white text-xs font-bold uppercase tracking-widest hover:bg-white/20"
            >
              Chiudi
            </button>
          </div>
        )}

        {!done && (
          <p className="mt-12 text-zinc-600 text-[10px] uppercase tracking-widest">tap per saltare</p>
        )}
      </div>
    </div>
  );
}

/** Bottone "Crea Trailer Testuale" — gratuito, sempre disponibile */
export function TextTrailerCard({ contentId, contentTitle, api, onGenerated, existing = null }) {
  const [busy, setBusy] = useState(false);
  const [text, setText] = useState(existing);
  const [showPlayer, setShowPlayer] = useState(false);

  useEffect(() => { setText(existing); }, [existing]);

  const generate = async () => {
    setBusy(true);
    try {
      const r = await api.post(`/trailers/${contentId}/generate-text`);
      setText(r.data.text_trailer);
      setShowPlayer(true);
      onGenerated?.(r.data.text_trailer);
    } catch (e) {
      const detail = e?.response?.data?.detail || 'Errore generazione trailer testuale';
      // eslint-disable-next-line no-alert
      alert(detail);
    } finally { setBusy(false); }
  };

  return (
    <>
      <div className="rounded-2xl border border-amber-500/30 bg-gradient-to-br from-amber-950/30 via-zinc-900/50 to-black p-3.5 mb-2.5" data-testid="trailer-text-card">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-yellow-500 flex items-center justify-center">
            <FileText className="w-4 h-4 text-black" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5">
              <p className="text-[12px] font-bold text-amber-300 uppercase tracking-wider">Trailer Testuale</p>
              <span className="px-1.5 py-0.5 rounded bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-[8px] font-black uppercase">GRATIS</span>
            </div>
            <p className="text-[8px] text-amber-200/60">Voice-over cinematografico anti-spoiler · stile movie title-card</p>
          </div>
        </div>

        {text ? (
          <div className="flex gap-1.5">
            <button
              onClick={() => setShowPlayer(true)}
              data-testid="trailer-text-play-btn"
              className="flex-1 py-2 rounded-lg bg-gradient-to-r from-amber-500 to-yellow-500 text-black font-black text-xs flex items-center justify-center gap-1.5 hover:scale-[1.02] transition-transform"
            >
              <FileText className="w-3.5 h-3.5" /> Guarda Trailer
            </button>
            <button
              onClick={generate}
              disabled={busy}
              data-testid="trailer-text-regen-btn"
              className="px-3 py-2 rounded-lg bg-zinc-800 border border-zinc-700 text-zinc-300 text-[10px] font-bold hover:bg-zinc-700 disabled:opacity-50"
            >
              {busy ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Rigenera'}
            </button>
          </div>
        ) : (
          <button
            onClick={generate}
            disabled={busy}
            data-testid="trailer-text-generate-btn"
            className="w-full py-2.5 rounded-lg bg-gradient-to-r from-amber-500 to-yellow-500 text-black font-black text-xs flex items-center justify-center gap-1.5 hover:scale-[1.02] transition-transform disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
            {busy ? 'Generazione…' : 'Genera Trailer Testuale (Gratis)'}
          </button>
        )}
      </div>

      {showPlayer && text && (
        <TrailerTextPlayer textTrailer={text} contentTitle={contentTitle} onClose={() => setShowPlayer(false)} />
      )}
    </>
  );
}
