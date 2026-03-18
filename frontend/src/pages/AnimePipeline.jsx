import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, LanguageContext } from '../contexts';
import { Sparkles, Lock, ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

export default function AnimePipeline() {
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
        setUnlocked(res.data.has_studio_anime);
        setRequirements(res.data.requirements?.studio_anime);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    check();
  }, [api]);

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-orange-400" />
    </div>
  );

  if (!unlocked) return (
    <div className="min-h-screen bg-[#0a0a0b] p-4 flex flex-col items-center justify-center text-center" data-testid="anime-locked">
      <div className="bg-orange-500/10 border border-orange-500/30 rounded-2xl p-8 max-w-sm">
        <Lock className="w-16 h-16 text-orange-400/50 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-orange-300 mb-2">Studio Anime</h2>
        <p className="text-sm text-gray-400 mb-4">
          {language === 'it' ? 'Acquista lo Studio Anime dallo Studio di Produzione per sbloccare!' : 'Purchase the Anime Studio from the Production Studio to unlock!'}
        </p>
        {requirements && (
          <div className="space-y-1 text-xs text-gray-500 mb-4">
            <p>Livello richiesto: <span className="text-orange-300">{requirements.level}</span></p>
            <p>Fama richiesta: <span className="text-orange-300">{requirements.fame}</span></p>
            <p>Costo: <span className="text-orange-300">${requirements.cost?.toLocaleString()}</span></p>
          </div>
        )}
        <Button onClick={() => navigate('/infrastructure')} className="bg-orange-600 hover:bg-orange-700">
          <ArrowLeft className="w-4 h-4 mr-1" /> Vai alle Infrastrutture
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0b] p-4 pb-20" data-testid="anime-pipeline">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white"><ArrowLeft className="w-5 h-5" /></button>
          <Sparkles className="w-6 h-6 text-orange-400" />
          <h1 className="text-xl font-bold text-orange-300">Produci Anime</h1>
        </div>
        <div className="bg-orange-500/5 border border-orange-500/20 rounded-xl p-6 text-center">
          <Sparkles className="w-12 h-12 text-orange-400/40 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-orange-200 mb-2">Prossimamente!</h3>
          <p className="text-sm text-gray-400">
            La produzione Anime con stili unici (Shonen, Seinen, Shojo, Mecha, Isekai), pipeline completa e episodi giornalieri arriva presto.
          </p>
        </div>
      </div>
    </div>
  );
}
