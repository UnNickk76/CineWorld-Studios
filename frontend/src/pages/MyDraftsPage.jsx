import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock } from 'lucide-react';
import MyDraftsWidget from '../components/MyDraftsWidget';
import { Button } from '../components/ui/button';

export default function MyDraftsPage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-[#0A0A0B] p-3 pb-24" data-testid="my-drafts-page">
      <div className="max-w-[1200px] mx-auto space-y-3">
        <div className="flex items-center gap-2 mb-2">
          <Button size="sm" variant="ghost" className="text-gray-300 hover:text-white" onClick={() => navigate(-1)} data-testid="back-btn">
            <ArrowLeft className="w-4 h-4 mr-1" /> Indietro
          </Button>
          <div className="flex items-center gap-2 ml-auto">
            <Clock className="w-4 h-4 text-amber-400" />
            <h1 className="font-['Bebas_Neue'] text-base text-white tracking-widest">Le Mie Bozze</h1>
          </div>
        </div>
        <p className="text-[10px] text-gray-500 px-1">
          Tutti i tuoi progetti in lavorazione (film, serie, anime, sceneggiature) salvati automaticamente.
          Clicca su una voce per riprendere a lavorarci.
        </p>
        <MyDraftsWidget />
      </div>
    </div>
  );
}
