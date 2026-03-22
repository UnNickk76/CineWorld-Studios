import React from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Zap, Clock, TrendingUp, Star, Shield, AlertTriangle, ChevronRight } from 'lucide-react';

export function ReleaseModeSelector({ selected, onSelect, onContinue }) {
  const modes = [
    {
      id: 'immediate',
      icon: Zap,
      color: 'yellow',
      title: 'Rilascio Immediato',
      pros: ['Uscita subito', 'Velocizzabile con crediti', 'Guadagni immediati'],
      cons: ['Nessun hype'],
      tag: 'Gameplay veloce',
    },
    {
      id: 'coming_soon',
      icon: Clock,
      color: 'cyan',
      title: 'Coming Soon',
      pros: ['Genera hype pre-lancio', 'Più potenziale incasso', 'Sezione "Prossimamente"'],
      cons: ['Non velocizzabile', 'Più rischio'],
      tag: 'Cinematografico',
    },
  ];

  const colorMap = {
    yellow: { border: 'border-yellow-500', bg: 'bg-yellow-500/10', text: 'text-yellow-400', badge: 'bg-yellow-500/20 text-yellow-400', glow: 'shadow-yellow-500/20' },
    cyan: { border: 'border-cyan-500', bg: 'bg-cyan-500/10', text: 'text-cyan-400', badge: 'bg-cyan-500/20 text-cyan-400', glow: 'shadow-cyan-500/20' },
  };

  return (
    <div className="space-y-3" data-testid="release-mode-selector">
      <div className="text-center mb-2">
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Modalità di rilascio</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {modes.map(m => {
          const c = colorMap[m.color];
          const isActive = selected === m.id;
          const Icon = m.icon;
          return (
            <Card
              key={m.id}
              className={`cursor-pointer transition-all duration-200 ${
                isActive ? `${c.border} ${c.bg} shadow-lg ${c.glow}` : 'border-gray-800 bg-[#111113] hover:border-gray-600'
              }`}
              onClick={() => onSelect(m.id)}
              data-testid={`release-mode-${m.id}`}
            >
              <CardContent className="p-4 space-y-3">
                <div className="flex items-center gap-2.5">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isActive ? c.bg : 'bg-white/5'}`}>
                    <Icon className={`w-5 h-5 ${isActive ? c.text : 'text-gray-500'}`} />
                  </div>
                  <div className="flex-1">
                    <h3 className={`text-sm font-bold ${isActive ? 'text-white' : 'text-gray-300'}`}>{m.title}</h3>
                    <Badge className={`text-[8px] h-4 mt-0.5 ${isActive ? c.badge : 'bg-gray-800 text-gray-500'}`}>{m.tag}</Badge>
                  </div>
                  {isActive && (
                    <div className={`w-5 h-5 rounded-full ${c.bg} ${c.border} border-2 flex items-center justify-center`}>
                      <div className={`w-2 h-2 rounded-full ${c.text.replace('text-', 'bg-')}`} />
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  {m.pros.map((p, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-[10px]">
                      <Star className="w-2.5 h-2.5 text-emerald-400 flex-shrink-0" />
                      <span className="text-gray-300">{p}</span>
                    </div>
                  ))}
                  {m.cons.map((c2, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-[10px]">
                      <AlertTriangle className="w-2.5 h-2.5 text-orange-400 flex-shrink-0" />
                      <span className="text-gray-500">{c2}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Button
        className="w-full bg-white/10 hover:bg-white/15 text-white text-xs font-semibold h-9"
        onClick={onContinue}
        disabled={!selected}
        data-testid="release-mode-continue-btn"
      >
        Continua <ChevronRight className="w-3.5 h-3.5 ml-1" />
      </Button>
    </div>
  );
}
