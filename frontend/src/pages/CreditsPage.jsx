// CineWorld Studio's - Credits Page
// Extracted from App.js

import React, { useContext, useState, useEffect } from 'react';
import { Clapperboard, Award } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { AuthContext } from '../contexts';

const CreditsPage = () => {
  const { api } = useContext(AuthContext);
  const [credits, setCredits] = useState(null);

  useEffect(() => {
    api.get('/game/credits').then(r => setCredits(r.data)).catch(console.error);
  }, [api]);

  if (!credits) return <div className="pt-20 text-center">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="credits-page">
      <div className="text-center mb-8">
        <Clapperboard className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
        <h1 className="font-['Bebas_Neue'] text-4xl">{credits.game_title}</h1>
        <p className="text-gray-400">Versione {credits.version}</p>
      </div>
      
      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-2xl mb-4 text-yellow-500">Credits</h2>
          <div className="space-y-4">
            {credits.credits.map((credit, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-white/5 rounded-lg border border-white/10">
                <Award className="w-10 h-10 text-yellow-500 flex-shrink-0" />
                <div>
                  <p className="font-bold text-lg">{credit.name}</p>
                  <p className="text-sm text-yellow-400 font-semibold">{credit.role}</p>
                  <p className="text-xs text-gray-400 mt-1">{credit.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      
      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-xl mb-3">Tecnologie Utilizzate</h2>
          <div className="flex flex-wrap gap-2">
            {credits.technologies.map((tech, i) => (
              <Badge key={i} className="bg-white/10 text-sm py-1">{tech}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Legal Section */}
      {credits.legal && (
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h2 className="font-['Bebas_Neue'] text-xl mb-4 text-gray-300">Note Legali</h2>
            <div className="space-y-4 text-sm text-gray-400">
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <p className="text-yellow-400 font-semibold">{credits.legal.trademark}</p>
              </div>
              <p className="italic">{credits.legal.disclaimer}</p>
              <div className="border-t border-white/10 pt-3">
                <p className="font-semibold text-gray-300 mb-2">Diritti Riservati:</p>
                <ul className="list-disc list-inside space-y-1">
                  {credits.legal.rights.map((right, i) => (
                    <li key={i}>{right}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Special Thanks */}
      {credits.special_thanks && (
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h2 className="font-['Bebas_Neue'] text-xl mb-3">Ringraziamenti Speciali</h2>
            <div className="flex flex-wrap gap-2">
              {credits.special_thanks.map((thanks, i) => (
                <Badge key={i} variant="outline" className="border-yellow-500/30 text-yellow-400">{thanks}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      <div className="text-center space-y-2 mt-8 pt-6 border-t border-white/10">
        <p className="text-yellow-500 font-semibold">{credits.copyright}</p>
        {credits.legal && (
          <p className="text-gray-500 text-xs">Proprietario: {credits.legal.owner}</p>
        )}
      </div>
    </div>
  );
};

export default CreditsPage;
