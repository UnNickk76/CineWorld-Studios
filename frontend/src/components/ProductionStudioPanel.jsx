import React, { useState, useEffect, useRef } from 'react';
import { Clapperboard, Wand2, Users, Sparkles, Star, ArrowUpCircle, Loader2, Check, Crown, Pen, Trash2, Plus, GraduationCap, UserPlus } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { toast } from 'sonner';

const GENRE_OPTIONS = [
  { value: 'action', label: 'Action' },
  { value: 'comedy', label: 'Comedy' },
  { value: 'drama', label: 'Drama' },
  { value: 'horror', label: 'Horror' },
  { value: 'sci_fi', label: 'Sci-Fi' },
  { value: 'romance', label: 'Romance' },
  { value: 'thriller', label: 'Thriller' },
  { value: 'animation', label: 'Animation' },
  { value: 'documentary', label: 'Documentary' },
  { value: 'fantasy', label: 'Fantasy' },
  { value: 'musical', label: 'Musical' },
  { value: 'western', label: 'Western' },
];

const ProductionStudioPanel = ({ api, user, infraDetail, upgradeInfo, upgrading, handleUpgrade, refreshUser, language }) => {
  const [activeTab, setActiveTab] = useState(null);
  const [studioData, setStudioData] = useState(null);
  const [castingData, setCastingData] = useState(null);
  const [drafts, setDrafts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(null);
  const [draftGenre, setDraftGenre] = useState('action');
  const [draftTitle, setDraftTitle] = useState('');
  const [generatingDraft, setGeneratingDraft] = useState(false);
  const [selectedRecruit, setSelectedRecruit] = useState(null);
  const [hiringAction, setHiringAction] = useState(null);
  const panelRef = useRef(null);

  useEffect(() => {
    api.get('/production-studio/status').then(r => setStudioData(r.data)).catch(() => {});
    api.get('/production-studio/drafts').then(r => setDrafts(r.data.drafts || [])).catch(() => {});
  }, [api]);

  const loadCasting = async () => {
    setLoading(true);
    try {
      const res = await api.get('/production-studio/casting');
      setCastingData(res.data);
    } catch {} finally { setLoading(false); }
  };

  const applyPreProduction = async (filmId, bonusType) => {
    setActionLoading(`${filmId}-${bonusType}`);
    try {
      const res = await api.post(`/production-studio/pre-production/${filmId}`, { bonus_type: bonusType });
      toast.success(res.data.message);
      refreshUser().catch(() => {});
      const updated = await api.get('/production-studio/status');
      setStudioData(updated.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setActionLoading(null); }
  };

  const applyRemaster = async (filmId) => {
    setActionLoading(`remaster-${filmId}`);
    try {
      const res = await api.post(`/production-studio/remaster/${filmId}`);
      toast.success(res.data.message);
      refreshUser().catch(() => {});
      const updated = await api.get('/production-studio/status');
      setStudioData(updated.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setActionLoading(null); }
  };

  const generateDraft = async () => {
    setGeneratingDraft(true);
    try {
      const res = await api.post('/production-studio/generate-draft', { genre: draftGenre, title_hint: draftTitle });
      toast.success(res.data.message);
      setDrafts(prev => [res.data.draft, ...prev]);
      setDraftTitle('');
      refreshUser().catch(() => {});
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore generazione bozza');
    } finally { setGeneratingDraft(false); }
  };

  const deleteDraft = async (draftId) => {
    try {
      await api.delete(`/production-studio/drafts/${draftId}`);
      setDrafts(prev => prev.filter(d => d.id !== draftId));
      toast.success('Bozza eliminata');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    }
  };

  const hireRecruit = async (recruit, action) => {
    setHiringAction(action);
    try {
      const res = await api.post('/production-studio/casting/hire', { recruit_id: recruit.id, action });
      toast.success(res.data.message);
      setSelectedRecruit(null);
      // Reload casting data to update UI
      loadCasting();
      refreshUser().catch(() => {});
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally { setHiringAction(null); }
  };

  const tabs = [
    { id: 'pre', icon: Clapperboard, label: 'Pre-Produzione', color: 'from-blue-500/20 to-indigo-500/10 border-blue-500/30', accent: 'text-blue-400' },
    { id: 'post', icon: Wand2, label: 'Post-Produzione', color: 'from-purple-500/20 to-pink-500/10 border-purple-500/30', accent: 'text-purple-400' },
  ];

  return (
    <div className="space-y-4" data-testid="production-studio-panel">
      {/* Studio Info */}
      <div className="grid grid-cols-3 gap-2">
        <div className="p-2.5 bg-yellow-500/10 rounded border border-yellow-500/20 text-center">
          <p className="text-[10px] text-gray-400">Livello</p>
          <p className="text-lg font-bold text-yellow-400">{studioData?.level || 1}</p>
        </div>
        <div className="p-2.5 bg-cyan-500/10 rounded border border-cyan-500/20 text-center">
          <p className="text-[10px] text-gray-400">Film in Attesa</p>
          <p className="text-lg font-bold text-cyan-400">{studioData?.pending_films?.length || 0}</p>
        </div>
        <div className="p-2.5 bg-green-500/10 rounded border border-green-500/20 text-center">
          <p className="text-[10px] text-gray-400">Sconto Casting</p>
          <p className="text-lg font-bold text-green-400">{studioData?.casting_agency?.discount_percent || 0}%</p>
        </div>
      </div>

      {/* 3 Panels */}
      <div className="grid grid-cols-3 gap-2">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <div
              key={tab.id}
              className={`p-3 rounded-lg border cursor-pointer transition-all bg-gradient-to-br ${tab.color} ${isActive ? 'ring-2 ring-white/20 scale-[1.02]' : 'opacity-80 hover:opacity-100'}`}
              onClick={() => { 
                const newTab = isActive ? null : tab.id;
                setActiveTab(newTab); 
                if (tab.id === 'casting' && !castingData) loadCasting(); 
                if (newTab) setTimeout(() => panelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }), 100);
              }}
              data-testid={`studio-tab-${tab.id}`}
            >
              <Icon className={`w-5 h-5 mb-1 ${tab.accent}`} />
              <p className="text-xs font-semibold">{tab.label}</p>
            </div>
          );
        })}
      </div>

      {/* Panel Content Area */}
      <div ref={panelRef}>
      {/* Pre-Production Panel */}
      {activeTab === 'pre' && studioData && (
        <div className="space-y-2" data-testid="pre-production-panel">
          <h4 className="text-sm font-semibold text-blue-400 flex items-center gap-1">
            <Clapperboard className="w-4 h-4" /> Pre-Produzione
          </h4>
          <p className="text-[10px] text-gray-500">Migliora i tuoi film prima del rilascio. Costo: ${studioData.pre_production.cost?.toLocaleString()}</p>
          
          {studioData.pending_films?.length === 0 ? (
            <p className="text-center text-gray-500 text-xs py-4">Nessun film in attesa di rilascio</p>
          ) : (
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {studioData.pending_films?.map(film => {
                const applied = film.pre_production_bonuses || [];
                return (
                  <div key={film.id} className="p-2 bg-black/30 rounded border border-white/5">
                    <div className="flex items-center gap-2 mb-2">
                      <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=60'} alt="" className="w-8 h-10 rounded object-cover" />
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold truncate">{film.title}</p>
                        <p className="text-[10px] text-gray-500">Qualità: {(film.quality_score || 0).toFixed(0)}%</p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {[
                        { type: 'storyboard', label: 'Storyboard', desc: `+${studioData.pre_production.storyboard_bonus}% qualità` },
                        { type: 'casting_interno', label: 'Casting', desc: `-${studioData.pre_production.casting_discount}% attori` },
                        { type: 'scouting', label: 'Scouting', desc: `-${studioData.pre_production.scouting_discount}% location` }
                      ].map(b => (
                        <Button
                          key={b.type}
                          size="sm"
                          disabled={applied.includes(b.type) || actionLoading === `${film.id}-${b.type}`}
                          onClick={() => applyPreProduction(film.id, b.type)}
                          className={`flex-1 h-7 text-[9px] ${applied.includes(b.type) ? 'bg-green-500/20 text-green-400' : 'bg-blue-500/20 text-blue-300 hover:bg-blue-500/30'}`}
                          data-testid={`pre-prod-${b.type}-${film.id}`}
                        >
                          {applied.includes(b.type) ? <Check className="w-3 h-3" /> : actionLoading === `${film.id}-${b.type}` ? <Loader2 className="w-3 h-3 animate-spin" /> : b.label}
                        </Button>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Draft Generation Section */}
          <div className="mt-3 pt-3 border-t border-white/10">
            <h5 className="text-xs font-semibold text-cyan-400 flex items-center gap-1 mb-2">
              <Pen className="w-3.5 h-3.5" /> Genera Bozza Sceneggiatura
            </h5>
            <p className="text-[10px] text-gray-500 mb-2">
              Crea una bozza AI da usare nel Film Wizard. CinePass gratis + qualità bonus +{studioData.pre_production.storyboard_bonus}%
            </p>
            <div className="flex gap-1.5 mb-2">
              <Select value={draftGenre} onValueChange={setDraftGenre}>
                <SelectTrigger className="h-7 text-xs bg-black/30 border-white/10 flex-1" data-testid="draft-genre-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {GENRE_OPTIONS.map(g => (
                    <SelectItem key={g.value} value={g.value}>{g.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Input
                value={draftTitle}
                onChange={e => setDraftTitle(e.target.value)}
                placeholder="Titolo (opzionale)"
                className="h-7 text-xs bg-black/30 border-white/10 flex-1"
                data-testid="draft-title-input"
              />
            </div>
            <Button
              size="sm"
              onClick={generateDraft}
              disabled={generatingDraft}
              className="w-full h-7 text-xs bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30"
              data-testid="generate-draft-btn"
            >
              {generatingDraft ? <><Loader2 className="w-3 h-3 animate-spin mr-1" /> Generando...</> : <><Plus className="w-3 h-3 mr-1" /> Genera Bozza (${studioData.pre_production.cost?.toLocaleString()})</>}
            </Button>

            {/* Existing Drafts */}
            {drafts.length > 0 && (
              <div className="mt-2 space-y-1.5">
                <p className="text-[10px] text-gray-400 font-medium">Bozze disponibili ({drafts.length}):</p>
                {drafts.map(d => (
                  <div key={d.id} className="flex items-center gap-2 p-1.5 bg-cyan-500/5 rounded border border-cyan-500/15" data-testid={`draft-${d.id}`}>
                    <div className="flex-1 min-w-0">
                      <p className="text-[11px] font-semibold truncate">{d.title}</p>
                      <p className="text-[9px] text-gray-500">{d.genre_name} | +{d.quality_bonus}% qualità</p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteDraft(d.id)}
                      className="h-6 w-6 p-0 text-red-400 hover:text-red-300 hover:bg-red-500/10"
                      data-testid={`delete-draft-${d.id}`}
                    >
                      <Trash2 className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      {activeTab === 'post' && studioData && (
        <div className="space-y-2" data-testid="post-production-panel">
          <h4 className="text-sm font-semibold text-purple-400 flex items-center gap-1">
            <Wand2 className="w-4 h-4" /> Post-Produzione / Remaster
          </h4>
          <p className="text-[10px] text-gray-500">
            Film pronti al rilascio. +{studioData.post_production.remaster_quality_bonus} qualita | 
            Costo: ${studioData.post_production.remaster_cost?.toLocaleString()} + {studioData.post_production.remaster_cinepass} CP
          </p>
          
          {studioData.released_films?.length === 0 ? (
            <p className="text-center text-gray-500 text-xs py-4">Nessun film pronto per il rilascio</p>
          ) : (
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {studioData.released_films?.map(film => (
                <div key={film.id} className="flex items-center gap-2 p-2 bg-black/30 rounded border border-white/5">
                  <img src={film.poster_url || 'https://images.unsplash.com/photo-1575823857138-d80155581d8c?w=60'} alt="" className="w-8 h-10 rounded object-cover" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold truncate">{film.title}</p>
                    <p className="text-[10px] text-gray-500">Pre-IMDb: {(film.pre_imdb_score || 0).toFixed(1)} | {film.genre}</p>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => applyRemaster(film.id)}
                    disabled={actionLoading === `remaster-${film.id}`}
                    className="h-7 text-[10px] bg-purple-500/20 text-purple-300 hover:bg-purple-500/30"
                    data-testid={`remaster-${film.id}`}
                  >
                    {actionLoading === `remaster-${film.id}` ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Remaster'}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      </div>
      {/* Pre/Post tabs remain active */}
    </div>
  );
};

export { ProductionStudioPanel };

