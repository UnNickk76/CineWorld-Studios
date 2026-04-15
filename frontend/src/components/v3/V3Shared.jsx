import React, { useRef, useEffect } from 'react';
import { Check, Sparkles, TrendingUp, Users, Camera, Clapperboard, Scissors, Megaphone, Globe, Ticket } from 'lucide-react';

export const V3_STEPS = [
  { id: 'idea', label: 'IDEA', icon: Sparkles, color: 'amber' },
  { id: 'hype', label: 'HYPE', icon: TrendingUp, color: 'orange' },
  { id: 'cast', label: 'CAST', icon: Users, color: 'cyan' },
  { id: 'prep', label: 'PREP', icon: Camera, color: 'blue' },
  { id: 'ciak', label: 'CIAK', icon: Clapperboard, color: 'red' },
  { id: 'finalcut', label: 'FINAL CUT', icon: Scissors, color: 'purple' },
  { id: 'marketing', label: 'MARKETING', icon: Megaphone, color: 'green' },
  { id: 'distribution', label: 'DISTRIB.', icon: Globe, color: 'blue' },
  { id: 'release_pending', label: 'USCITA', icon: Ticket, color: 'emerald' },
];

export const STEP_STYLES = {
  amber:   { active: 'border-amber-500 bg-amber-500/15 text-amber-400', line: 'bg-amber-600', text: 'text-amber-400' },
  orange:  { active: 'border-orange-500 bg-orange-500/15 text-orange-400', line: 'bg-orange-600', text: 'text-orange-400' },
  cyan:    { active: 'border-cyan-500 bg-cyan-500/15 text-cyan-400', line: 'bg-cyan-600', text: 'text-cyan-400' },
  blue:    { active: 'border-blue-500 bg-blue-500/15 text-blue-400', line: 'bg-blue-600', text: 'text-blue-400' },
  red:     { active: 'border-red-500 bg-red-500/15 text-red-400', line: 'bg-red-600', text: 'text-red-400' },
  purple:  { active: 'border-purple-500 bg-purple-500/15 text-purple-400', line: 'bg-purple-600', text: 'text-purple-400' },
  green:   { active: 'border-green-500 bg-green-500/15 text-green-400', line: 'bg-green-600', text: 'text-green-400' },
  yellow:  { active: 'border-yellow-500 bg-yellow-500/15 text-yellow-400', line: 'bg-yellow-600', text: 'text-yellow-400' },
  emerald: { active: 'border-emerald-500 bg-emerald-500/15 text-emerald-400', line: 'bg-emerald-600', text: 'text-emerald-400' },
};

export const GENRES = ['action','comedy','drama','horror','sci_fi','romance','thriller','animation','documentary','fantasy','adventure','musical','western','biographical','mystery','war','crime','noir','historical'];
export const GENRE_LABELS = { action:'Azione', comedy:'Commedia', drama:'Dramma', horror:'Horror', sci_fi:'Fantascienza', romance:'Romantico', thriller:'Thriller', animation:'Animazione', documentary:'Documentario', fantasy:'Fantasy', adventure:'Avventura', musical:'Musical', western:'Western', biographical:'Biografico', mystery:'Giallo', war:'Guerra', crime:'Crime', noir:'Noir', historical:'Storico' };
export const SUBGENRE_MAP = {
  action:['militare','spy','vendetta','arti marziali','heist','survival'], comedy:['slapstick','romantica','nera','satirica','demenziale','teen','familiare'],
  drama:['romantico','psicologico','familiare','sociale','biografico','legale'], horror:['slasher','psicologico','soprannaturale','body horror','gotico','zombie'],
  sci_fi:['cyberpunk','space opera','distopia','alieni','mecha','viaggi nel tempo'], romance:['tragico','commedia romantica','teen romance','proibito','period'],
  thriller:['psicologico','crime','paranoia','politico','suspense','serial killer'], animation:['CGI','stop motion','2D classico','anime','mixed media'],
  documentary:['true crime','storico','sociale','natura','sportivo'], fantasy:['epico','dark fantasy','urban fantasy','mitologico','fiabesco'],
  adventure:['giungla','oceano','tesoro','survival','esplorazione'],
};

export const LOCATION_TAGS = ['Urban','Suburban','Rurale','Costiero','Montano','Deserto','Tropicale','Artico','Storico','Futuristico','Sotterraneo','Spaziale'];

export async function v3api(path, method = 'GET', body) {
  const API = process.env.REACT_APP_BACKEND_URL;
  const token = localStorage.getItem('cineworld_token');
  const res = await fetch(`${API}/api/pipeline-v3${path}`, {
    method, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || 'Errore API');
  return data;
}

/* ═══════ STEPPER ═══════ */
export const StepperBar = ({ current }) => {
  const ci = V3_STEPS.findIndex(s => s.id === current);
  const ref = useRef(null);
  useEffect(() => {
    if (ref.current) {
      const el = ref.current.querySelector(`[data-sid="${current}"]`);
      if (el) el.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
    }
  }, [current]);
  return (
    <div ref={ref} className="flex items-center gap-0 overflow-x-auto py-2 px-1 scrollbar-hide" data-testid="v3-stepper">
      {V3_STEPS.map((s, i) => {
        const Icon = s.icon;
        const style = STEP_STYLES[s.color];
        const done = i < ci; const active = i === ci;
        return (
          <React.Fragment key={s.id}>
            {i > 0 && <div className={`w-2 sm:w-4 h-0.5 shrink-0 ${done || active ? style.line : 'bg-gray-800'}`} />}
            <div className="flex flex-col items-center shrink-0 gap-0.5" data-sid={s.id}>
              <div className={`w-6 h-6 sm:w-7 sm:h-7 rounded-full flex items-center justify-center border-2 transition-all ${
                active ? `${style.active} shadow-lg scale-110` : done ? 'border-emerald-600 bg-emerald-500/10 text-emerald-400' : 'border-gray-800 bg-gray-900/50 text-gray-700 opacity-40'
              }`}>{done ? <Check className="w-2.5 h-2.5" /> : <Icon className="w-2.5 h-2.5" />}</div>
              <span className={`text-[5px] sm:text-[6px] font-bold uppercase tracking-wider whitespace-nowrap ${
                active ? style.text : done ? 'text-emerald-500/60' : 'text-gray-700'
              }`}>{s.label}</span>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
};

/* ═══════ PHASE WRAPPER ═══════ */
export const PhaseWrapper = ({ title, subtitle, icon: Icon, color, children }) => (
  <div className="p-3 space-y-3">
    <div className="flex items-center gap-2 mb-1">
      <div className={`w-7 h-7 rounded-lg bg-${color}-500/10 border border-${color}-500/20 flex items-center justify-center`}>
        <Icon className={`w-3.5 h-3.5 text-${color}-400`} />
      </div>
      <div>
        <h3 className="text-sm font-bold text-white">{title}</h3>
        {subtitle && <p className="text-[8px] text-gray-500">{subtitle}</p>}
      </div>
    </div>
    {children}
  </div>
);

/* ═══════ PROGRESS CIRCLE ═══════ */
export const ProgressCircle = ({ value, size = 48, color = '#00FFD0' }) => {
  const r = (size / 2) - 4; const circ = 2 * Math.PI * r;
  const offset = circ - (Math.min(100, Math.max(0, value)) / 100) * circ;
  return (
    <svg width={size} height={size} className="block">
      <circle cx={size/2} cy={size/2} r={r} stroke="#333" strokeWidth="3" fill="none" />
      <circle cx={size/2} cy={size/2} r={r} stroke={color} strokeWidth="3" fill="none"
        strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
        style={{ transition: 'stroke-dashoffset 0.5s ease', transform: 'rotate(-90deg)', transformOrigin: 'center' }} />
      <text x={size/2} y={size/2} textAnchor="middle" dominantBaseline="central"
        fill={color} fontSize={size * 0.22} fontWeight="bold">{Math.floor(value)}%</text>
    </svg>
  );
};
