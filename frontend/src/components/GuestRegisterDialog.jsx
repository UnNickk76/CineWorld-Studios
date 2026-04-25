import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../contexts';
import { Dialog, DialogContent } from './ui/dialog';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { X, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

/**
 * GuestRegisterDialog — listens for the global `open-guest-convert` event
 * and shows a registration form that CALLS convertGuest() to preserve
 * all guest progress (films, studio stats, CW$, cinepass, etc.).
 * Self-contained: no props needed. Mount once at the root.
 */
export default function GuestRegisterDialog() {
  const { user, convertGuest } = useContext(AuthContext);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', nickname: '', production_house_name: '' });

  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener('open-guest-convert', handler);
    return () => window.removeEventListener('open-guest-convert', handler);
  }, []);

  // Prefill nickname from guest user once mounted
  useEffect(() => {
    if (user?.nickname && !form.nickname) {
      setForm(f => ({ ...f, nickname: user.nickname, production_house_name: user.production_house_name || user.studio_name || '' }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.nickname]);

  if (!user?.is_guest) return null;

  const submit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password || !form.nickname) {
      toast.error('Compila email, password e nickname');
      return;
    }
    if (form.password.length < 6) {
      toast.error('La password deve essere di almeno 6 caratteri');
      return;
    }
    setLoading(true);
    try {
      await convertGuest({
        email: form.email.trim().toLowerCase(),
        password: form.password,
        nickname: form.nickname.trim(),
        production_house_name: form.production_house_name.trim() || undefined,
      });
      toast.success('Registrazione completata! Progressi salvati.');
      setOpen(false);
      // Soft reload to refresh all data as registered user
      setTimeout(() => window.location.reload(), 600);
    } catch (err) {
      const msg = err?.response?.data?.detail || err?.message || 'Errore durante la registrazione';
      toast.error(typeof msg === 'string' ? msg : 'Errore durante la registrazione');
    } finally {
      setLoading(false);
    }
  };

  // Quick stats (visible as motivation to register)
  const films = user.total_films_created ?? user.films_count ?? 0;
  const money = user.funds ?? 0;
  const fmtMoney = (n) => n >= 1_000_000 ? `$${(n / 1_000_000).toFixed(1)}M` : n >= 1_000 ? `$${(n / 1_000).toFixed(1)}K` : `$${n}`;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent
        className="bg-[#0f0f10] border border-red-500/40 max-w-sm p-0 overflow-hidden"
        data-testid="guest-register-dialog"
      >
        {/* Header */}
        <div className="bg-gradient-to-br from-red-600/90 via-red-700/80 to-red-900/80 p-4 relative">
          <button
            onClick={() => setOpen(false)}
            className="absolute top-2 right-2 text-white/80 hover:text-white p-1"
            data-testid="guest-register-close" aria-label="Chiudi">
            <X className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
            <span className="text-[10px] font-black uppercase tracking-widest text-white">REC · SALVA PROGRESSI</span>
          </div>
          <h2 className="text-xl font-black text-white leading-tight">Non perdere il tuo studio!</h2>
          <p className="text-[11px] text-white/90 mt-1 leading-snug">
            Registrati ora. Tutti i tuoi progressi (film, soldi, infrastrutture, stelle) rimarranno intatti.
          </p>
        </div>

        {/* Quick stats */}
        <div className="flex items-center justify-around py-2 px-4 bg-white/5 border-b border-white/10 text-center">
          <div>
            <p className="text-[9px] text-gray-500 uppercase">Film</p>
            <p className="text-sm font-black text-yellow-400">{films}</p>
          </div>
          <div>
            <p className="text-[9px] text-gray-500 uppercase">Soldi</p>
            <p className="text-sm font-black text-green-400">{fmtMoney(money)}</p>
          </div>
          <div>
            <p className="text-[9px] text-gray-500 uppercase">CinePass</p>
            <p className="text-sm font-black text-cyan-400">{user.cinepass ?? 0}</p>
          </div>
        </div>

        {/* Form */}
        <form onSubmit={submit} className="p-4 space-y-2" data-testid="guest-register-form">
          <div>
            <label className="text-[9px] text-gray-400 uppercase font-bold mb-0.5 block">Email</label>
            <Input
              type="email" value={form.email}
              onChange={e => setForm({ ...form, email: e.target.value })}
              placeholder="tu@email.com" autoComplete="email" required
              data-testid="guest-register-email"
              className="bg-black/40 border-white/15 text-white text-sm h-9"
            />
          </div>
          <div>
            <label className="text-[9px] text-gray-400 uppercase font-bold mb-0.5 block">Password (min 6)</label>
            <Input
              type="password" value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="••••••" autoComplete="new-password" required minLength={6}
              data-testid="guest-register-password"
              className="bg-black/40 border-white/15 text-white text-sm h-9"
            />
          </div>
          <div>
            <label className="text-[9px] text-gray-400 uppercase font-bold mb-0.5 block">Nickname</label>
            <Input
              type="text" value={form.nickname}
              onChange={e => setForm({ ...form, nickname: e.target.value })}
              placeholder="Il tuo nickname" required
              data-testid="guest-register-nickname"
              className="bg-black/40 border-white/15 text-white text-sm h-9"
            />
          </div>
          <div>
            <label className="text-[9px] text-gray-400 uppercase font-bold mb-0.5 block">Casa di produzione (opz.)</label>
            <Input
              type="text" value={form.production_house_name}
              onChange={e => setForm({ ...form, production_house_name: e.target.value })}
              placeholder="Studio …"
              data-testid="guest-register-studio"
              className="bg-black/40 border-white/15 text-white text-sm h-9"
            />
          </div>
          <Button
            type="submit" disabled={loading}
            className="w-full bg-gradient-to-r from-red-600 to-red-500 hover:from-red-500 hover:to-red-400 text-white font-black text-sm h-10 mt-2"
            data-testid="guest-register-submit"
          >
            {loading
              ? <><Loader2 className="w-4 h-4 mr-1 animate-spin" /> Salvataggio...</>
              : <><Save className="w-4 h-4 mr-1" /> Salva e Registra</>}
          </Button>
          <p className="text-[9px] text-gray-500 text-center mt-1">
            Non verrà perso nessun progresso, promesso.
          </p>
        </form>
      </DialogContent>
    </Dialog>
  );
}
