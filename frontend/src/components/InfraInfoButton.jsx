import React, { useState, useContext } from 'react';
import { Info, X, Check, Clock, Zap, Trophy } from 'lucide-react';
import { AuthContext } from '../App';
import { Dialog, DialogContent } from './ui/dialog';

/**
 * InfraInfoButton — piccola "i" cliccabile su una card infrastruttura.
 * Al click apre un modal con: descrizione, funzioni, sblocchi per livello, ROI.
 */
export function InfraInfoButton({ infraType, variant = 'default' }) {
  const { api } = useContext(AuthContext);
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleClick = async (e) => {
    e.stopPropagation();
    if (!info) {
      setLoading(true);
      try {
        const res = await api.get(`/infrastructure/info/${infraType}`);
        setInfo(res.data || null);
      } catch (err) {
        setInfo({ title: infraType, short: 'Informazioni non disponibili.', what_it_does: [], unlocks_by_level: [], roi: '' });
      } finally {
        setLoading(false);
      }
    }
    setOpen(true);
  };

  const btnCls = variant === 'corner'
    ? 'absolute top-1 right-1 z-20 w-5 h-5 rounded-full bg-black/50 hover:bg-black/80 flex items-center justify-center transition-all'
    : 'w-5 h-5 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-all';

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        className={btnCls}
        data-testid={`infra-info-btn-${infraType}`}
        aria-label="Info infrastruttura"
        title="Informazioni"
      >
        <Info className="w-3 h-3 text-cyan-300" />
      </button>

      <Dialog open={open} onOpenChange={(v) => !v && setOpen(false)}>
        <DialogContent className="bg-gradient-to-b from-[#14110d] to-[#0a0805] border border-cyan-500/20 max-w-md max-h-[85vh] overflow-y-auto" data-testid={`infra-info-modal-${infraType}`}>
          {loading && (
            <div className="p-6 text-center text-cyan-300/70 text-sm">Caricamento…</div>
          )}
          {info && !loading && (
            <div className="p-1">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="text-[9px] uppercase tracking-wider text-cyan-400/70 font-semibold">Infrastruttura</div>
                  <h3 className="text-lg font-bold text-cyan-100 font-['Bebas_Neue']">{info.title}</h3>
                </div>
                <button onClick={() => setOpen(false)} className="text-cyan-300/60 hover:text-cyan-200 p-1"><X className="w-4 h-4" /></button>
              </div>

              {info.short && (
                <p className="text-xs text-slate-300 mb-4 italic border-l-2 border-cyan-500/50 pl-3">{info.short}</p>
              )}

              {info.what_it_does?.length > 0 && (
                <div className="mb-4">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    <h4 className="text-[10px] uppercase tracking-wider text-amber-300 font-semibold">A cosa serve</h4>
                  </div>
                  <ul className="space-y-1.5">
                    {info.what_it_does.map((item, i) => (
                      <li key={i} className="flex items-start gap-2 text-[11px] text-slate-200">
                        <Check className="w-3 h-3 text-emerald-400 flex-shrink-0 mt-0.5" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {info.unlocks_by_level?.length > 0 && (
                <div className="mb-4">
                  <div className="flex items-center gap-1.5 mb-2">
                    <Clock className="w-3.5 h-3.5 text-violet-400" />
                    <h4 className="text-[10px] uppercase tracking-wider text-violet-300 font-semibold">Sblocchi per livello</h4>
                  </div>
                  <div className="space-y-1.5">
                    {info.unlocks_by_level.map((u, i) => (
                      <div key={i} className="flex items-start gap-2 p-2 rounded-md bg-violet-500/5 border border-violet-500/10">
                        <span className="inline-flex items-center justify-center w-7 h-5 rounded bg-violet-500/20 text-violet-200 text-[9px] font-bold flex-shrink-0">
                          Lv.{u.level}
                        </span>
                        <span className="text-[10px] text-slate-300 leading-tight">{u.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {info.roi && (
                <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                  <div className="flex items-center gap-1.5 mb-1">
                    <Trophy className="w-3.5 h-3.5 text-emerald-400" />
                    <h4 className="text-[10px] uppercase tracking-wider text-emerald-300 font-semibold">Perché acquistarla</h4>
                  </div>
                  <p className="text-[11px] text-emerald-100/90 leading-snug">{info.roi}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}

export default InfraInfoButton;
