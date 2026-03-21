// CineWorld - Emittente TV Page (Redirect to new TV Station system)
import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Radio, Loader2 } from 'lucide-react';

export default function EmittenteTVPage() {
  const { api } = useContext(AuthContext);
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/tv-stations/my').then(res => {
      const stations = res.data.stations || [];
      if (stations.length > 0) {
        navigate(`/tv-station/${stations[0].id}`, { replace: true });
      } else {
        setLoading(false);
      }
    }).catch(() => setLoading(false));
  }, [api, navigate]);

  if (loading) return (
    <div className="min-h-screen bg-[#0A0A0B] flex items-center justify-center pt-16">
      <Loader2 className="w-8 h-8 text-red-400 animate-spin" />
    </div>
  );

  return (
    <div className="min-h-screen bg-[#0A0A0B] text-white flex items-center justify-center pt-16 pb-20">
      <div className="text-center">
        <Radio className="w-12 h-12 text-gray-700 mx-auto mb-3" />
        <p className="text-gray-400 text-sm mb-2">Nessuna emittente TV trovata</p>
        <p className="text-gray-600 text-xs">Acquista un'infrastruttura Emittente TV per iniziare!</p>
        <Button className="mt-4 bg-red-500 hover:bg-red-600" onClick={() => navigate('/infrastructure')}>
          Vai alle Infrastrutture
        </Button>
      </div>
    </div>
  );
}
