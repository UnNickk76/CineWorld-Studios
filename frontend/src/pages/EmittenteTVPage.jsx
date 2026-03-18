import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, LanguageContext } from '../contexts';
import { Radio, Lock, ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

export default function EmittenteTVPage() {
  const { api } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [unlocked, setUnlocked] = useState(false);
  const [requirements, setRequirements] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await api.get('/production-studios/unlock-status');
        setUnlocked(res.data.has_emittente_tv);
        setRequirements(res.data.requirements?.emittente_tv);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    check();
  }, [api]);

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-emerald-400" />
    </div>
  );

  if (!unlocked) return (
    <div className="min-h-screen bg-[#0a0a0b] p-4 flex flex-col items-center justify-center text-center" data-testid="tv-locked">
      <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-8 max-w-sm">
        <Lock className="w-16 h-16 text-emerald-400/50 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-emerald-300 mb-2">Emittente TV</h2>
        <p className="text-sm text-gray-400 mb-4">
          {language === 'it' ? 'Acquista l\'Emittente TV dallo Studio di Produzione per sbloccare!' : 'Purchase the TV Broadcaster from the Production Studio to unlock!'}
        </p>
        {requirements && (
          <div className="space-y-1 text-xs text-gray-500 mb-4">
            <p>Livello richiesto: <span className="text-emerald-300">{requirements.level}</span></p>
            <p>Fama richiesta: <span className="text-emerald-300">{requirements.fame}</span></p>
            <p>Costo: <span className="text-emerald-300">${requirements.cost?.toLocaleString()}</span></p>
          </div>
        )}
        <Button onClick={() => navigate('/infrastructure')} className="bg-emerald-600 hover:bg-emerald-700">
          <ArrowLeft className="w-4 h-4 mr-1" /> Vai alle Infrastrutture
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0b] p-4 pb-20" data-testid="emittente-tv">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white"><ArrowLeft className="w-5 h-5" /></button>
          <Radio className="w-6 h-6 text-emerald-400" />
          <h1 className="text-xl font-bold text-emerald-300">La tua TV</h1>
        </div>
        <div className="bg-emerald-500/5 border border-emerald-500/20 rounded-xl p-6 text-center">
          <Radio className="w-12 h-12 text-emerald-400/40 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-emerald-200 mb-2">Prossimamente!</h3>
          <p className="text-sm text-gray-400">
            La tua Emittente TV con palinsesto, fasce orarie (Prime Time, Daytime, Late Night), ascolti in tempo reale e entrate pubblicitarie arriva presto.
          </p>
        </div>
      </div>
    </div>
  );
}
