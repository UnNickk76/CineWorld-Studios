import React, { useState, useMemo, useRef } from 'react';
import { Sparkles, Film } from 'lucide-react';
import { PhaseWrapper, GENRES, GENRE_LABELS, SUBGENRE_MAP, LOCATION_TAGS, ProgressCircle, v3api } from './V3Shared';

export const IdeaPhase = ({ film, onRefresh, toast, onDirty }) => {
  const [title, setTitle] = useState(film.title || '');
  const [genre, setGenre] = useState(film.genre || 'action');
  const [preplot, setPreplot] = useState(film.preplot || '');
  const [subgenres, setSubgenres] = useState(film.subgenres || (film.subgenre ? [film.subgenre] : []));
  const [locations, setLocations] = useState(film.locations || []);
  const [posterPrompt, setPosterPrompt] = useState(film.poster_prompt || '');
  const [screenplaySource, setScreenplaySource] = useState('preplot');
  const [screenplayPrompt, setScreenplayPrompt] = useState('');
  const [loading, setLoading] = useState('');
  const [posterProgress, setPosterProgress] = useState(0);
  const [scriptProgress, setScriptProgress] = useState(0);
  const posterInt = useRef(null);
  const scriptInt = useRef(null);

  const subgenreOptions = useMemo(() => SUBGENRE_MAP[genre] || [], [genre]);
  const mark = () => onDirty?.();
  const hasPoster = !!film.poster_url;

  const saveIdea = async () => {
    setLoading('save');
    try {
      await v3api(`/films/${film.id}/save-idea`, 'POST', { title, genre, subgenre: subgenres.join(', '), preplot, subgenres });
      await onRefresh(); toast?.('Idea salvata!');
    } catch (e) { toast?.(e.message, 'error'); }
    setLoading('');
  };

  const generatePoster = async (mode) => {
    setLoading('poster'); setPosterProgress(5);
    posterInt.current = setInterval(() => setPosterProgress(p => p >= 90 ? p : p + Math.random() * 10), 800);
    try {
      await v3api(`/films/${film.id}/generate-poster`, 'POST', {
        source: mode === 'custom' ? 'custom_prompt' : 'preplot',
        custom_prompt: mode === 'custom' ? posterPrompt : '',
      });
      setPosterProgress(100); clearInterval(posterInt.current);
      await onRefresh(); toast?.('Locandina generata!');
    } catch (e) { clearInterval(posterInt.current); setPosterProgress(0); toast?.(e.message, 'error'); }
    setLoading('');
  };

  const generateScreenplay = async () => {
    setLoading('screenplay'); setScriptProgress(5);
    scriptInt.current = setInterval(() => setScriptProgress(p => p >= 90 ? p : p + Math.random() * 8), 1000);
    try {
      await v3api(`/films/${film.id}/generate-screenplay`, 'POST', {
        source: screenplaySource === 'custom' ? 'custom_prompt' : 'preplot',
        custom_prompt: screenplaySource === 'custom' ? screenplayPrompt : '',
      });
      setScriptProgress(100); clearInterval(scriptInt.current);
      await onRefresh(); toast?.('Sceneggiatura generata!');
    } catch (e) { clearInterval(scriptInt.current); setScriptProgress(0); toast?.(e.message, 'error'); }
    setLoading('');
  };

  const toggleLoc = (l) => { setLocations(v => v.includes(l) ? v.filter(x => x !== l) : [...v, l]); mark(); };

  const canAdvance = title.trim().length >= 2 && genre && preplot.trim().length >= 50;

  return (
    <PhaseWrapper title="L'Idea" subtitle="Dai forma al tuo progetto cinematografico" icon={Sparkles} color="amber">
      <div className="space-y-3">
        {/* Title */}
        <input value={title} onChange={e => { setTitle(e.target.value); mark(); }}
          placeholder="Titolo del film" className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-sm text-white placeholder-gray-600" data-testid="title-input" />

        {/* Genre + Subgenres */}
        <select value={genre} onChange={e => { setGenre(e.target.value); setSubgenres([]); mark(); }}
          className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px] text-white">
          {GENRES.map(g => <option key={g} value={g}>{GENRE_LABELS[g]}</option>)}
        </select>
        {subgenreOptions.length > 0 && (
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-[8px] text-gray-500 uppercase font-bold">Sottogeneri</span>
              <span className={`text-[8px] ${subgenres.length > 0 ? 'text-cyan-400' : 'text-gray-600'}`}>{subgenres.length}/3</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {subgenreOptions.map(s => (
                <button key={s} onClick={() => { setSubgenres(v => v.includes(s) ? v.filter(x => x !== s) : v.length < 3 ? [...v, s] : v); mark(); }}
                  className={`px-2 py-1 rounded-lg text-[8px] font-bold border transition-all ${
                    subgenres.includes(s) ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400' : 'border-gray-800 text-gray-500 hover:border-gray-600'
                  }`}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {/* Pretrama */}
        <div>
          <div className="flex justify-between mb-1">
            <span className="text-[8px] text-gray-500 uppercase font-bold">Pretrama</span>
            <span className={`text-[8px] ${preplot.length >= 50 ? 'text-emerald-400' : 'text-gray-600'}`}>{preplot.length}/50 min</span>
          </div>
          <textarea value={preplot} onChange={e => { setPreplot(e.target.value); mark(); }}
            rows={4} placeholder="Descrivi la trama del tuo film (min 50 caratteri)..."
            className="w-full rounded-xl border border-gray-800 bg-gray-950 px-3 py-2.5 text-[10px] text-white placeholder-gray-600" data-testid="preplot-input" />
        </div>

        {/* Locations */}
        <div>
          <span className="text-[8px] text-gray-500 uppercase font-bold">Ambientazione</span>
          <div className="flex flex-wrap gap-1.5 mt-1.5">
            {LOCATION_TAGS.map(l => (
              <button key={l} onClick={() => toggleLoc(l)}
                className={`px-2 py-1 rounded-lg text-[8px] font-bold border transition-all ${
                  locations.includes(l) ? 'bg-amber-500/10 border-amber-500/30 text-amber-400' : 'border-gray-800 text-gray-500 hover:border-gray-600'
                }`}>{l}</button>
            ))}
          </div>
        </div>

        {/* LOCANDINA AI */}
        <div className="p-3 rounded-xl bg-gray-800/20 border border-gray-700/30 space-y-2">
          <span className="text-[8px] text-gray-500 uppercase font-bold">Locandina AI</span>
          {hasPoster && <img src={film.poster_url} alt="" className="w-20 h-28 rounded-lg border border-gray-700 object-cover mx-auto" />}
          {posterProgress > 0 && posterProgress < 100 ? (
            <div className="flex justify-center py-2"><ProgressCircle value={posterProgress} size={56} color="#F59E0B" /></div>
          ) : (
            <div className="space-y-2">
              <div className="flex gap-1.5">
                <button onClick={() => generatePoster('auto')} disabled={!!loading || preplot.length < 10}
                  className="flex-1 text-[8px] py-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 disabled:opacity-30 font-bold" data-testid="poster-ai-auto">AI Auto</button>
                <button onClick={() => generatePoster('custom')} disabled={!!loading || !posterPrompt.trim()}
                  className="flex-1 text-[8px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-400 hover:bg-purple-500/20 disabled:opacity-30 font-bold" data-testid="poster-ai-custom">AI Custom</button>
              </div>
              <input value={posterPrompt} onChange={e => setPosterPrompt(e.target.value)}
                placeholder="Prompt personalizzato locandina..." className="w-full rounded-lg border border-gray-800 bg-gray-950 px-2.5 py-1.5 text-[8px] text-white placeholder-gray-600" />
            </div>
          )}
        </div>

        {/* SCENEGGIATURA */}
        <div className="p-3 rounded-xl bg-gray-800/20 border border-gray-700/30 space-y-2">
          <span className="text-[8px] text-gray-500 uppercase font-bold">Sceneggiatura</span>
          {scriptProgress > 0 && scriptProgress < 100 ? (
            <div className="flex justify-center py-2"><ProgressCircle value={scriptProgress} size={56} color="#A855F7" /></div>
          ) : (
            <div className="space-y-2">
              <div className="flex gap-1.5">
                {['preplot','custom'].map(m => (
                  <button key={m} onClick={() => setScreenplaySource(m)}
                    className={`flex-1 text-[7px] py-1.5 rounded-lg border font-bold ${screenplaySource === m ? 'bg-purple-500/10 border-purple-500/30 text-purple-400' : 'border-gray-800 text-gray-500'}`}>
                    {m === 'preplot' ? 'Da pretrama' : 'Prompt custom'}
                  </button>
                ))}
              </div>
              {screenplaySource === 'custom' && (
                <textarea value={screenplayPrompt} onChange={e => setScreenplayPrompt(e.target.value)}
                  rows={2} placeholder="Prompt sceneggiatura..." className="w-full rounded-lg border border-gray-800 bg-gray-950 px-2.5 py-1.5 text-[8px] text-white placeholder-gray-600" />
              )}
              <button onClick={generateScreenplay} disabled={!!loading}
                className="w-full text-[8px] py-2 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-400 hover:bg-purple-500/20 disabled:opacity-30 font-bold" data-testid="gen-screenplay-btn">Genera Sceneggiatura</button>
            </div>
          )}
          {film.screenplay_text && <pre className="whitespace-pre-wrap text-[7px] text-gray-400 mt-1 max-h-28 overflow-y-auto bg-gray-900/50 p-2 rounded-lg">{film.screenplay_text}</pre>}
        </div>

        {/* Save */}
        <button onClick={saveIdea} disabled={!canAdvance || !!loading}
          className="w-full text-[10px] py-2.5 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400 hover:bg-amber-500/25 disabled:opacity-30 font-bold" data-testid="save-idea-btn">
          {loading === 'save' ? '...' : 'Salva Bozza Idea'}
        </button>
      </div>
    </PhaseWrapper>
  );
};
