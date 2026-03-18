import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, LanguageContext } from '../contexts';
import { Tv, Lock, ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function SeriesTVPipeline() {
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
        setUnlocked(res.data.has_studio_serie_tv);
        setRequirements(res.data.requirements?.studio_serie_tv);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    check();
  }, [api]);

  if (loading) return (
    <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
    </div>
  );

  if (!unlocked) return (
    <div className="min-h-screen bg-[#0a0a0b] p-4 flex flex-col items-center justify-center text-center" data-testid="series-locked">
      <div className="bg-blue-500/10 border border-blue-500/30 rounded-2xl p-8 max-w-sm">
        <Lock className="w-16 h-16 text-blue-400/50 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-blue-300 mb-2">Studio Serie TV</h2>
        <p className="text-sm text-gray-400 mb-4">
          {language === 'it' ? 'Acquista lo Studio Serie TV dallo Studio di Produzione per sbloccare questa funzione!' : 'Purchase the TV Series Studio from the Production Studio to unlock!'}
        </p>
        {requirements && (
          <div className="space-y-1 text-xs text-gray-500 mb-4">
            <p>Livello richiesto: <span className="text-blue-300">{requirements.level}</span></p>
            <p>Fama richiesta: <span className="text-blue-300">{requirements.fame}</span></p>
            <p>Costo: <span className="text-blue-300">${requirements.cost?.toLocaleString()}</span></p>
          </div>
        )}
        <Button onClick={() => navigate('/infrastructure')} className="bg-blue-600 hover:bg-blue-700">
          <ArrowLeft className="w-4 h-4 mr-1" /> Vai alle Infrastrutture
        </Button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0a0a0b] p-4 pb-20" data-testid="series-pipeline">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-white"><ArrowLeft className="w-5 h-5" /></button>
          <Tv className="w-6 h-6 text-blue-400" />
          <h1 className="text-xl font-bold text-blue-300">Produci Serie TV</h1>
        </div>
        <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-6 text-center">
          <Tv className="w-12 h-12 text-blue-400/40 mx-auto mb-3" />
          <h3 className="text-lg font-semibold text-blue-200 mb-2">Prossimamente!</h3>
          <p className="text-sm text-gray-400">
            La produzione di Serie TV con pipeline completa, casting, sceneggiatura per stagione e episodi giornalieri con mini-trame AI arriva presto.
          </p>
        </div>
      </div>
    </div>
  );
}
