import React, { useEffect, useState, useRef } from 'react';
import { X, FileText, Loader2, Download, Share2 } from 'lucide-react';

/**
 * Genera una card PNG "poster" del trailer testuale (stile locandina serif).
 * Ritorna un dataURL. Il client può salvarlo o condividerlo via Web Share API.
 */
async function buildTrailerCard({ textTrailer, contentTitle }) {
  const W = 1080, H = 1920;
  const canvas = document.createElement('canvas');
  canvas.width = W; canvas.height = H;
  const ctx = canvas.getContext('2d');
  // Background radiale
  const grad = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) / 1.2);
  grad.addColorStop(0, '#0b0b0c');
  grad.addColorStop(1, '#000');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);
  // Grana sottile
  ctx.globalAlpha = 0.04;
  for (let i = 0; i < 1200; i++) {
    ctx.fillStyle = '#fff';
    ctx.fillRect(Math.random() * W, Math.random() * H, 1, 1);
  }
  ctx.globalAlpha = 1;
  // Titolo serif
  ctx.textAlign = 'center';
  ctx.fillStyle = '#fbbf24';
  ctx.font = 'bold 56px Georgia, serif';
  const title = (contentTitle || 'Trailer').toUpperCase();
  ctx.fillText(title.slice(0, 40), W / 2, 220);
  // Sections
  const sections = textTrailer?.sections || [];
  let y = 420;
  ctx.fillStyle = '#f5f5f4';
  ctx.font = 'italic 42px Georgia, serif';
  const wrap = (txt, maxChars) => {
    const words = (txt || '').split(/\s+/);
    const lines = [];
    let cur = '';
    for (const w of words) {
      if ((cur + ' ' + w).trim().length > maxChars) { lines.push(cur.trim()); cur = w; }
      else cur = (cur + ' ' + w).trim();
    }
    if (cur) lines.push(cur);
    return lines;
  };
  for (let i = 0; i < sections.length && y < H - 300; i++) {
    const s = sections[i] || '';
    const isCS = /coming soon|prossimamente/i.test(s);
    if (isCS) {
      ctx.fillStyle = '#fbbf24';
      ctx.font = 'bold 76px Georgia, serif';
      ctx.fillText(s.toUpperCase().slice(0, 30), W / 2, y + 40);
      y += 120;
      ctx.fillStyle = '#f5f5f4';
      ctx.font = 'italic 42px Georgia, serif';
      continue;
    }
    const lines = wrap(s, 42);
    for (const ln of lines) {
      if (y > H - 240) break;
      ctx.fillText(ln, W / 2, y);
      y += 58;
    }
    y += 40;
  }
  // Footer
  ctx.fillStyle = '#71717a';
  ctx.font = '28px Georgia, serif';
  ctx.fillText('— CineWorld Studio\'s —', W / 2, H - 120);
  return canvas.toDataURL('image/png');
}

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
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={async (e) => {
                e.stopPropagation();
                try {
                  const dataUrl = await buildTrailerCard({ textTrailer, contentTitle });
                  // Prova Web Share con file image
                  try {
                    const blob = await (await fetch(dataUrl)).blob();
                    const file = new File([blob], `${(contentTitle || 'trailer').replace(/[^a-z0-9]/gi, '_')}_trailer.png`, { type: 'image/png' });
                    if (navigator.canShare && navigator.canShare({ files: [file] })) {
                      await navigator.share({ files: [file], title: contentTitle, text: 'Dal Trailer Testuale — CineWorld' });
                      return;
                    }
                  } catch (_) { /* fallthrough a download */ }
                  // Fallback: download diretto
                  const link = document.createElement('a');
                  link.href = dataUrl;
                  link.download = `${(contentTitle || 'trailer').replace(/[^a-z0-9]/gi, '_')}_trailer.png`;
                  document.body.appendChild(link); link.click(); link.remove();
                } catch (_) { /* silent */ }
              }}
              data-testid="trailer-text-share-btn"
              className="px-5 py-2.5 rounded-full bg-gradient-to-r from-amber-500 to-yellow-500 text-black text-xs font-black uppercase tracking-widest flex items-center gap-1.5 hover:scale-[1.03] transition-transform"
            >
              <Share2 className="w-3.5 h-3.5" /> Condividi
            </button>
            <button
              onClick={async (e) => {
                e.stopPropagation();
                try {
                  const dataUrl = await buildTrailerCard({ textTrailer, contentTitle });
                  const link = document.createElement('a');
                  link.href = dataUrl;
                  link.download = `${(contentTitle || 'trailer').replace(/[^a-z0-9]/gi, '_')}_trailer.png`;
                  document.body.appendChild(link); link.click(); link.remove();
                } catch (_) { /* silent */ }
              }}
              data-testid="trailer-text-download-btn"
              className="px-5 py-2.5 rounded-full bg-white/10 border border-white/20 text-white text-xs font-bold uppercase tracking-widest flex items-center gap-1.5 hover:bg-white/20"
            >
              <Download className="w-3.5 h-3.5" /> Salva
            </button>
            <button
              onClick={(e) => { e.stopPropagation(); onClose?.(); }}
              data-testid="trailer-text-end-btn"
              className="px-5 py-2.5 rounded-full bg-white/5 border border-white/10 text-zinc-300 text-xs font-bold uppercase tracking-widest hover:bg-white/10"
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
