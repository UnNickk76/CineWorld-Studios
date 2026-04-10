// CineWorld Studio's - Release Notes Page (FROZEN)
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Lock, Cpu } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';

const ReleaseNotes = () => {
  const navigate = useNavigate();

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="release-notes-page">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-400 opacity-50" />
            NOTE DI RILASCIO
          </h1>
        </div>
      </div>

      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-8 text-center">
          <Lock className="w-12 h-12 mx-auto mb-4 text-amber-500/60" />
          <Badge className="bg-amber-500/20 text-amber-400 border border-amber-500/30 mb-4" data-testid="frozen-badge">
            In aggiornamento
          </Badge>
          <p className="text-gray-300 text-sm mb-2">
            Questa sezione è temporaneamente in aggiornamento e verrà riattivata in una versione successiva.
          </p>
        </CardContent>
      </Card>

      <Card className="bg-[#0D0D0D] border-white/5 mt-3">
        <CardContent className="p-4 text-center">
          <div className="flex items-center justify-center gap-2 text-gray-500 text-xs">
            <Cpu className="w-3.5 h-3.5" />
            <span>Il sistema futuro permetterà aggiornamento intelligente tramite AI e gestione da Admin Panel.</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ReleaseNotes;
