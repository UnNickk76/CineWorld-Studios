import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;

const STEPS = [
  { id: 'idea', label: 'IDEA' },
  { id: 'hype', label: 'HYPE' },
  { id: 'cast', label: 'CAST' },
  { id: 'prep', label: 'PREP' },
  { id: 'ciak', label: 'CIAK' },
  { id: 'finalcut', label: 'FINAL CUT' },
  { id: 'marketing', label: 'MARKETING' },
  { id: 'distribution', label: 'DISTRIBUZIONE' },
  { id: 'release_pending', label: 'USCITA' },
];

const GENRES = ['action', 'comedy', 'drama', 'horror', 'sci_fi', 'romance', 'thriller', 'animation', 'documentary', 'fantasy', 'adventure'];
const SUBGENRES = {
  action: ['militare', 'spy', 'vendetta', 'arti marziali'],
  comedy: ['demenziale', 'surreale', 'familiare', 'satirica'],
  drama: ['romantico', 'psicologico', 'sociale', 'familiare'],
  horror: ['slasher', 'soprannaturale', 'psicologico', 'zombie'],
  sci_fi: ['cyberpunk', 'distopia', 'alieni', 'mecha'],
  romance: ['tragico', 'proibito', 'teen romance', 'commedia romantica'],
  thriller: ['crime', 'mistero', 'suspense', 'paranoia'],
  animation: ['anime', 'CGI', '2D classico', 'stop motion'],
  documentary: ['true crime', 'storico', 'sociale', 'natura'],
  fantasy: ['epico', 'dark fantasy', 'urban fantasy', 'mitologico'],
  adventure: ['giungla', 'tesoro', 'survival', 'oceano'],
};
const RELEASE_OPTIONS = ['6 ore', '12 ore', 'Immediato', 'Tra 24 ore', '2 giorni', '3 giorni', '4 giorni', '5 giorni', '6 giorni'];
const MARKETING_PACKAGES = ['Teaser Digitale', 'Campagna Social Virale', 'Stampa e TV', 'Tour del Cast', 'Mega Campagna Globale'];

async function api(path, method = 'GET', body) {
  const token = localStorage.getItem('cineworld_token');
  const res = await fetch(`${API}/api/pipeline-v3${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || data.error || 'Errore API');
  return data;
}

function Stepper({ current }) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto py-3">
      {STEPS.map((s, i) => {
        const active = s.id === current;
        const done = STEPS.findIndex(x => x.id === current) > i;
        return (
          <div key={s.id} className="flex items-center gap-1 shrink-0">
            <div className={`w-9 h-9 rounded-full border text-[10px] flex items-center justify-center font-bold ${active ? 'border-emerald-400 text-emerald-400 bg-emerald-500/10' : done ? 'border-cyan-400 text-cyan-400 bg-cyan-500/10' : 'border-slate-700 text-slate-500 bg-slate-900'}`}>
              {done ? '✓' : i + 1}
            </div>
            <span className={`text-[10px] font-bold ${active ? 'text-emerald-300' : done ? 'text-cyan-300' : 'text-slate-500'}`}>{s.label}</span>
            {i < STEPS.length - 1 && <div className="w-4 h-[2px] bg-slate-800" />}
          </div>
        );
      })}
    </div>
  );
}

function ProgressOverlay({ value }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/95 flex flex-col items-center justify-center px-6">
      <div className="text-2xl font-bold text-emerald-300 mb-6">Rilascio in corso…</div>
      <div className="w-40 h-40 rounded-full border-[10px] border-slate-800 relative flex items-center justify-center">
        <div className="absolute inset-0 rounded-full" style={{ background: `conic-gradient(#23d3a6 ${value * 3.6}deg, #1e293b 0deg)` }} />
        <div className="absolute inset-[10px] rounded-full bg-black flex items-center justify-center text-4xl text-emerald-300 font-bold">{value}%</div>
      </div>
      <div className="text-slate-400 mt-6 text-sm">Nessun calcolo qualità. Solo chiusura del rilascio.</div>
    </div>
  );
}

export default function PipelineV3() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [balances, setBalances] = useState(null);
  const [progress, setProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);

  const [idea, setIdea] = useState({ title: '', genre: 'action', subgenre: '', preplot: '' });
  const [posterSource, setPosterSource] = useState('preplot');
  const [posterPrompt, setPosterPrompt] = useState('');
  const [screenplaySource, setScreenplaySource] = useState('preplot');
  const [screenplayPrompt, setScreenplayPrompt] = useState('');
  const [hypeNotes, setHypeNotes] = useState('');
  const [hypeBudget, setHypeBudget] = useState(0);
  const [castNotes, setCastNotes] = useState('');
  const [chemistryMode, setChemistryMode] = useState('auto');
  const [prepNotes, setPrepNotes] = useState('');
  const [finalcutNotes, setFinalcutNotes] = useState('');
  const [marketingPackages, setMarketingPackages] = useState([]);
  const [releaseType, setReleaseType] = useState('direct');
  const [releaseDate, setReleaseDate] = useState('Immediato');
  const [world, setWorld] = useState(true);

  const loadProjects = useCallback(async () => {
    const data = await api('/films');
    setProjects(data.items || []);
    if (!selected && data.items?.length) setSelected(data.items[0]);
    if (selected) {
      const fresh = (data.items || []).find(x => x.id === selected.id);
      if (fresh) setSelected(fresh);
    }
  }, [selected]);

  const refreshSelected = useCallback(async (id) => {
    if (!id && !selected?.id) return null;
    const data = await api(`/films/${id || selected.id}`);
    setSelected(data);
    setIdea({ title: data.title || '', genre: data.genre || 'action', subgenre: data.subgenre || '', preplot: data.preplot || '' });
    setHypeNotes(data.hype_notes || '');
    setHypeBudget(data.hype_budget || 0);
    setCastNotes(data.cast_notes || '');
    setChemistryMode(data.chemistry_mode || 'auto');
    setPrepNotes(data.prep_notes || '');
    setFinalcutNotes(data.finalcut_notes || '');
    setMarketingPackages(data.marketing_packages || []);
    setReleaseType(data.release_type || 'direct');
    setReleaseDate(data.release_date_label || 'Immediato');
    setWorld(data.distribution_world ?? true);
    setPosterSource(data.poster_source || 'preplot');
    setPosterPrompt(data.poster_source === 'custom_prompt' ? (data.poster_prompt || '') : '');
    setScreenplaySource(data.screenplay_source || 'preplot');
    setScreenplayPrompt(data.screenplay_source === 'custom_prompt' ? (data.screenplay_prompt || '') : '');
    return data;
  }, [selected]);

  useEffect(() => { loadProjects().catch(e => setError(e.message)); }, [loadProjects]);
  useEffect(() => { if (selected?.id) refreshSelected(selected.id).catch(() => {}); }, [selected?.id, refreshSelected]);

  const currentStep = selected?.pipeline_state || 'idea';
  const subgenreOptions = useMemo(() => SUBGENRES[idea.genre] || [], [idea.genre]);

  const run = async (fn) => {
    setError(''); setMessage(''); setLoading(true);
    try {
      await fn();
      await loadProjects();
    } catch (e) {
      setError(e.message || 'Errore');
    } finally {
      setLoading(false);
    }
  };

  const createProject = () => run(async () => {
    const res = await api('/films/create', 'POST', idea);
    setSelected(res.project);
    setMessage('Progetto V3 creato');
  });

  const saveIdea = () => run(async () => {
    const res = await api(`/films/${selected.id}/save-idea`, 'POST', idea);
    setSelected(res.project);
    setMessage('Idea salvata');
  });

  const generatePoster = () => run(async () => {
    const res = await api(`/films/${selected.id}/generate-poster`, 'POST', {
      source: posterSource,
      custom_prompt: posterPrompt,
    });
    setSelected(res.project);
    setMessage(res.note);
  });

  const generateScreenplay = () => run(async () => {
    const res = await api(`/films/${selected.id}/generate-screenplay`, 'POST', {
      source: screenplaySource,
      custom_prompt: screenplayPrompt,
    });
    setSelected(res.project);
    setMessage('Sceneggiatura aggiornata');
  });

  const saveHype = () => run(async () => {
    const res = await api(`/films/${selected.id}/save-hype`, 'POST', { hype_notes: hypeNotes, budget: Number(hypeBudget || 0) });
    setSelected(res.project); setBalances(res.balances || null); setMessage('Hype salvato');
  });

  const saveCast = () => run(async () => {
    const res = await api(`/films/${selected.id}/save-cast`, 'POST', { cast_notes: castNotes, chemistry_mode: chemistryMode });
    setSelected(res.project); setMessage('Cast salvato');
  });

  const savePrep = () => run(async () => {
    const res = await api(`/films/${selected.id}/save-prep`, 'POST', { prep_notes: prepNotes });
    setSelected(res.project); setMessage('Prep salvato');
  });

  const startCiak = () => run(async () => {
    const res = await api(`/films/${selected.id}/start-ciak`, 'POST');
    setSelected(res.project); setMessage('Ciak completato');
  });

  const saveFinalcut = () => run(async () => {
    const res = await api(`/films/${selected.id}/save-finalcut`, 'POST', { finalcut_notes: finalcutNotes });
    setSelected(res.project); setMessage('Final cut salvato');
  });

  const saveMarketing = () => run(async () => {
    const res = await api(`/films/${selected.id}/save-marketing`, 'POST', { packages: marketingPackages });
    setSelected(res.project); setBalances(res.balances || null); setMessage('Marketing salvato');
  });

  const saveReleaseType = () => run(async () => {
    const res = await api(`/films/${selected.id}/set-release-type`, 'POST', { release_type: releaseType });
    setSelected(res.project); setMessage('Tipo rilascio salvato');
  });

  const saveDistribution = () => run(async () => {
    const res = await api(`/films/${selected.id}/schedule-release`, 'POST', {
      release_date_label: releaseDate,
      world,
      zones: [],
    });
    setSelected(res.project); setBalances(res.balances || null); setMessage('Distribuzione salvata');
  });

  const speedup = (stage, percentage) => run(async () => {
    const res = await api(`/films/${selected.id}/speedup`, 'POST', { stage, percentage });
    setSelected(res.project); setBalances(res.balances || null); setMessage(`Accelerazione ${percentage}% applicata`);
  });

  const confirmRelease = async () => {
    if (loading || !selected?.id) return;
    setError(''); setMessage(''); setLoading(true);
    setShowProgress(true);
    setProgress(0);
    let current = 0;
    const timer = setInterval(() => {
      current += 5;
      setProgress(Math.min(current, 100));
      if (current >= 100) clearInterval(timer);
    }, 100);

    try {
      await new Promise(r => setTimeout(r, 2300));
      const res = await api(`/films/${selected.id}/confirm-release`, 'POST');
      setProgress(100);
      await new Promise(r => setTimeout(r, 700));
      setShowProgress(false);
      setMessage('Film rilasciato senza calcoli qualità. Reindirizzamento…');
      await loadProjects();
      setTimeout(() => navigate('/'), 900);
      return res;
    } catch (e) {
      setError(e.message || 'Errore rilascio');
      setShowProgress(false);
    } finally {
      setLoading(false);
    }
  };

  const discard = () => run(async () => {
    const res = await api(`/films/${selected.id}/discard`, 'POST');
    setSelected(res.project); setMessage('Film scartato e inviato al mercato');
  });

  return (
    <div className="min-h-screen bg-black text-white pb-28">
      {showProgress && <ProgressOverlay value={progress} />}
      <div className="px-4 pt-8">
        <div className="flex items-center gap-3 mb-4">
          <button onClick={() => navigate('/')} className="w-10 h-10 rounded-full bg-slate-900 border border-slate-800">←</button>
          <div>
            <div className="text-2xl font-black tracking-wide">PIPELINE V3</div>
            <div className="text-slate-400 text-sm">Nessun calcolo qualità. Nessun fattore bloccante.</div>
          </div>
        </div>

        {balances && <div className="mb-3 text-sm text-emerald-300">Saldo aggiornato → Fondi: ${balances.funds?.toLocaleString?.() ?? balances.funds} · CinePass: {balances.cinepass}</div>}
        {message && <div className="mb-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-emerald-300">{message}</div>}
        {error && <div className="mb-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-red-300">{error}</div>}

        <div className="grid grid-cols-1 lg:grid-cols-[320px,1fr] gap-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
            <div className="text-sm font-bold text-slate-300 mb-3">Progetti V3</div>
            <button onClick={createProject} disabled={loading || !idea.title.trim()} className="w-full mb-3 rounded-xl bg-emerald-500 py-3 font-bold text-black disabled:opacity-50">Crea nuovo progetto V3</button>
            <div className="space-y-2 max-h-[60vh] overflow-y-auto">
              {projects.map(p => (
                <button key={p.id} onClick={() => setSelected(p)} className={`w-full text-left rounded-xl border px-3 py-3 ${selected?.id === p.id ? 'border-emerald-500 bg-emerald-500/10' : 'border-slate-800 bg-slate-900'}`}>
                  <div className="font-bold truncate">{p.title || 'Senza titolo'}</div>
                  <div className="text-xs text-slate-400">{p.genre || '—'} · {p.pipeline_state || 'idea'}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4">
            {!selected ? (
              <div className="text-slate-400">Crea o seleziona un progetto V3.</div>
            ) : (
              <>
                <div className="flex items-center justify-between gap-4 mb-3">
                  <div>
                    <div className="text-2xl font-black">{selected.title || 'Nuovo film'}</div>
                    <div className="text-slate-400">{selected.genre || 'genere'} · qualità preview/finale: null</div>
                  </div>
                  <div className="text-right text-sm text-slate-400">
                    <div>stato: <span className="text-cyan-300 font-bold">{selected.pipeline_state}</span></div>
                    <div>rilascio: <span className="text-emerald-300 font-bold">{selected.release_type || '—'}</span></div>
                  </div>
                </div>

                <Stepper current={currentStep} />

                <div className="mt-4 space-y-5">
                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">IDEA — pretrama, prompt locandina e sceneggiatura</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                      <input value={idea.title} onChange={e => setIdea(v => ({ ...v, title: e.target.value }))} placeholder="Titolo" className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3" />
                      <select value={idea.genre} onChange={e => setIdea(v => ({ ...v, genre: e.target.value, subgenre: '' }))} className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-3">
                        {GENRES.map(g => <option key={g} value={g}>{g}</option>)}
                      </select>
                    </div>
                    <select value={idea.subgenre} onChange={e => setIdea(v => ({ ...v, subgenre: e.target.value }))} className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3">
                      <option value="">Sottogenere</option>
                      {subgenreOptions.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <textarea value={idea.preplot} onChange={e => setIdea(v => ({ ...v, preplot: e.target.value }))} rows={6} placeholder="Scrivi la pretrama utente" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3" />
                    <button onClick={saveIdea} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black disabled:opacity-50">Salva idea e vai avanti</button>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                      <div className="rounded-2xl border border-slate-800 p-4">
                        <div className="font-bold mb-2">Locandina</div>
                        <div className="text-xs text-slate-400 mb-2">“Da pretrama utente” usa la pretrama come prompt. “Da prompt utente” apre un prompt separato.</div>
                        <div className="flex gap-2 mb-2">
                          <button onClick={() => setPosterSource('preplot')} className={`flex-1 rounded-lg py-2 ${posterSource === 'preplot' ? 'bg-emerald-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>Da pretrama utente</button>
                          <button onClick={() => setPosterSource('custom_prompt')} className={`flex-1 rounded-lg py-2 ${posterSource === 'custom_prompt' ? 'bg-emerald-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>Da prompt utente</button>
                        </div>
                        {posterSource === 'custom_prompt' && (
                          <textarea value={posterPrompt} onChange={e => setPosterPrompt(e.target.value)} rows={4} placeholder="Prompt locandina personalizzato" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-2" />
                        )}
                        <button onClick={generatePoster} disabled={loading} className="w-full rounded-xl bg-slate-100 py-3 font-bold text-black disabled:opacity-50">Salva prompt locandina</button>
                        {selected.poster_prompt_note && <div className="text-xs text-emerald-300 mt-2">{selected.poster_prompt_note}</div>}
                      </div>

                      <div className="rounded-2xl border border-slate-800 p-4">
                        <div className="font-bold mb-2">Sceneggiatura</div>
                        <div className="text-xs text-slate-400 mb-2">“Da pretrama utente” usa davvero la pretrama. “Da prompt utente” usa un prompt personalizzato.</div>
                        <div className="flex gap-2 mb-2">
                          <button onClick={() => setScreenplaySource('preplot')} className={`flex-1 rounded-lg py-2 ${screenplaySource === 'preplot' ? 'bg-emerald-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>Da pretrama utente</button>
                          <button onClick={() => setScreenplaySource('custom_prompt')} className={`flex-1 rounded-lg py-2 ${screenplaySource === 'custom_prompt' ? 'bg-emerald-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>Da prompt utente</button>
                        </div>
                        {screenplaySource === 'custom_prompt' && (
                          <textarea value={screenplayPrompt} onChange={e => setScreenplayPrompt(e.target.value)} rows={4} placeholder="Prompt sceneggiatura personalizzato" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-2" />
                        )}
                        <button onClick={generateScreenplay} disabled={loading} className="w-full rounded-xl bg-slate-100 py-3 font-bold text-black disabled:opacity-50">Genera/scopri prompt sceneggiatura</button>
                        {!!selected.screenplay_text && <pre className="whitespace-pre-wrap text-xs text-slate-300 mt-2 max-h-40 overflow-y-auto">{selected.screenplay_text}</pre>}
                      </div>
                    </div>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">HYPE</div>
                    <textarea value={hypeNotes} onChange={e => setHypeNotes(e.target.value)} rows={3} placeholder="Note hype" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3" />
                    <input type="number" value={hypeBudget} onChange={e => setHypeBudget(e.target.value)} placeholder="Budget hype" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3" />
                    <div className="flex gap-2 flex-wrap mb-3">{[25,50,75,100].map(p => <button key={p} onClick={() => speedup('hype', p)} className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Accelera {p}%</button>)}</div>
                    <button onClick={saveHype} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black">Salva hype</button>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">CAST</div>
                    <textarea value={castNotes} onChange={e => setCastNotes(e.target.value)} rows={3} placeholder="Note cast" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3" />
                    <select value={chemistryMode} onChange={e => setChemistryMode(e.target.value)} className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3">
                      <option value="auto">Chimica auto</option>
                      <option value="manual">Chimica manuale</option>
                      <option value="off">Nessuna chimica</option>
                    </select>
                    <button onClick={saveCast} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black">Salva cast</button>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">PREP</div>
                    <textarea value={prepNotes} onChange={e => setPrepNotes(e.target.value)} rows={3} placeholder="Note prep" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3" />
                    <button onClick={savePrep} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black">Salva prep</button>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">CIAK</div>
                    <div className="text-sm text-slate-400 mb-3">Nessun fattore bloccante. Il ciak chiude e passa al final cut.</div>
                    <div className="flex gap-2 flex-wrap mb-3">{[25,50,75,100].map(p => <button key={p} onClick={() => speedup('ciak', p)} className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Accelera {p}%</button>)}</div>
                    <button onClick={startCiak} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black">Completa ciak</button>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">FINAL CUT</div>
                    <textarea value={finalcutNotes} onChange={e => setFinalcutNotes(e.target.value)} rows={3} placeholder="Note final cut" className="w-full rounded-xl border border-slate-800 bg-slate-950 px-3 py-3 mb-3" />
                    <div className="flex gap-2 flex-wrap mb-3">{[25,50,75,100].map(p => <button key={p} onClick={() => speedup('finalcut', p)} className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Accelera {p}%</button>)}</div>
                    <button onClick={saveFinalcut} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black">Salva final cut</button>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">MARKETING</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
                      {MARKETING_PACKAGES.map(name => (
                        <button key={name} onClick={() => setMarketingPackages(v => v.includes(name) ? v.filter(x => x !== name) : [...v, name])} className={`rounded-xl border px-3 py-3 text-left ${marketingPackages.includes(name) ? 'border-emerald-500 bg-emerald-500/10 text-emerald-300' : 'border-slate-800 bg-slate-950'}`}>{name}</button>
                      ))}
                    </div>
                    <div className="flex gap-2 mb-3">
                      <button onClick={() => setReleaseType('premiere')} className={`flex-1 rounded-xl py-3 ${releaseType === 'premiere' ? 'bg-yellow-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>La Prima</button>
                      <button onClick={() => setReleaseType('direct')} className={`flex-1 rounded-xl py-3 ${releaseType === 'direct' ? 'bg-emerald-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>Rilascio diretto</button>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-3">
                      <button onClick={saveMarketing} disabled={loading} className="rounded-xl bg-cyan-500 py-3 font-bold text-black">Salva marketing</button>
                      <button onClick={saveReleaseType} disabled={loading} className="rounded-xl bg-slate-100 py-3 font-bold text-black">Salva tipo rilascio</button>
                    </div>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">DISTRIBUZIONE</div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 mb-3">
                      {RELEASE_OPTIONS.map(label => (
                        <button key={label} onClick={() => setReleaseDate(label)} className={`rounded-xl py-3 ${releaseDate === label ? 'bg-emerald-500 text-black' : 'bg-slate-900 border border-slate-800'}`}>{label}</button>
                      ))}
                    </div>
                    <label className="flex items-center gap-2 mb-3 text-sm text-slate-300">
                      <input type="checkbox" checked={world} onChange={e => setWorld(e.target.checked)} /> Mondiale (scala subito fondi e cinepass)
                    </label>
                    <div className="flex gap-2 flex-wrap mb-3">{[25,50,75,100].map(p => <button key={p} onClick={() => speedup('premiere', p)} className="rounded-lg border border-slate-700 px-3 py-2 text-sm">Accelera premiere {p}%</button>)}</div>
                    <button onClick={saveDistribution} disabled={loading} className="w-full rounded-xl bg-cyan-500 py-3 font-bold text-black">Salva distribuzione</button>
                  </section>

                  <section className="rounded-2xl border border-slate-800 p-4 bg-black/30">
                    <div className="font-bold mb-3">USCITA</div>
                    <div className="text-slate-400 text-sm mb-3">Qualità preview/finale volutamente assente. Valore mostrato: null.</div>
                    <div className="rounded-xl border border-slate-800 p-4 mb-3 bg-slate-950">
                      <div className="text-sm text-slate-400">Titolo</div>
                      <div className="text-xl font-black">{selected.title}</div>
                      <div className="text-sm text-slate-400 mt-2">Genere: {selected.genre} · Rilascio: {releaseType} · Data: {releaseDate}</div>
                      <div className="text-sm text-slate-400 mt-2">Poster da: {posterSource === 'preplot' ? 'pretrama utente' : 'prompt utente'} · Sceneggiatura da: {screenplaySource === 'preplot' ? 'pretrama utente' : 'prompt utente'}</div>
                      <div className="text-sm text-slate-400 mt-2">Quality preview/finale: null</div>
                    </div>
                    <button onClick={confirmRelease} disabled={loading} className="w-full rounded-xl bg-emerald-500 py-4 text-lg font-black text-black disabled:opacity-50">CONFERMA USCITA</button>
                    <button onClick={discard} disabled={loading} className="w-full rounded-xl border border-red-500/30 bg-red-500/10 py-4 text-lg font-black text-red-300 mt-3 disabled:opacity-50">SCARTA FILM</button>
                  </section>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
