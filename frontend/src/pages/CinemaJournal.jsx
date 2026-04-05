// CineWorld Studio's - CinemaJournal ULTRA
// 3 tabs: LIVE | NEWS | PUBBLICO
// Riusa tutte le API esistenti, zero nuove API

import React, { useState, useEffect, useContext, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Badge } from '../components/ui/badge';
import { ScrollArea } from '../components/ui/scroll-area';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import {
  Film, Star, Flame, Heart, Newspaper, MessageCircle, TrendingUp,
  Eye, DollarSign, Sparkles, Zap, Crown, Trophy, Users, Clapperboard,
  ChevronRight, ArrowUp, ArrowDown, Activity
} from 'lucide-react';

// ── FASE 4: Template frasi riutilizzabili ──
const TEMPLATES = {
  it: {
    own_revenue_high:    (t) => `Il tuo film "${t}" sta incassando alla grande`,
    own_likes_growing:   (t) => `"${t}" sta ricevendo molto amore dal pubblico`,
    own_quality_top:     (t) => `"${t}" conquista la critica con recensioni eccellenti`,
    own_cinemas_many:    (t, n) => `"${t}" proiettato in ${n} sale in tutta la nazione`,
    own_in_theaters:     (t, d) => `"${t}" e al giorno ${d} in sala`,
    own_growing_fast:    (t) => `"${t}" sta crescendo rapidamente nelle classifiche`,
    own_audience_loves:  (t) => `Il pubblico non smette di parlare di "${t}"`,
    own_buzz:            (t) => `"${t}" genera un buzz incredibile sui social`,
    global_dominating:   (t) => `"${t}" domina il box office oggi`,
    global_trending:     (t) => `Cresce l'interesse per "${t}"`,
    global_popular:      (t) => `"${t}" e il film piu discusso del momento`,
    global_quality:      (t) => `"${t}" sorprende la critica con un punteggio altissimo`,
    global_revenue_rec:  (t, r) => `"${t}" supera $${r}M al box office`,
    global_likes_boom:   (t, n) => `"${t}" raggiunge +${n} reazioni dal pubblico`,
    la_prima_live:       (t) => `"${t}" e in anteprima esclusiva — La Prima LIVE`,
    hype_rising:         (t) => `Cresce l'hype per "${t}" — tutti ne parlano`,
    audience_positive:   (t) => `Il pubblico ama "${t}" — recensioni entusiastiche`,
    audience_mixed:      (t) => `Opinioni divise su "${t}" — il dibattito e aperto`,
    attendance_high:     (t, n) => `"${t}" ha attirato ${n} spettatori`,
  }
};

const getIcon = (type) => {
  const map = {
    own_revenue_high: DollarSign,
    own_likes_growing: Heart,
    own_quality_top: Star,
    own_cinemas_many: Film,
    own_in_theaters: Clapperboard,
    own_growing_fast: TrendingUp,
    own_audience_loves: Users,
    own_buzz: Sparkles,
    global_dominating: Crown,
    global_trending: TrendingUp,
    global_popular: Flame,
    global_quality: Trophy,
    global_revenue_rec: DollarSign,
    global_likes_boom: Heart,
    la_prima_live: Zap,
    hype_rising: Sparkles,
    audience_positive: Star,
    audience_mixed: Activity,
    attendance_high: Users,
  };
  return map[type] || Film;
};

const getColor = (type) => {
  if (type.startsWith('own_'))    return { bg: 'bg-yellow-500/10', border: 'border-yellow-500/25', text: 'text-yellow-400', icon: 'text-yellow-400' };
  if (type.startsWith('la_prima')) return { bg: 'bg-red-500/10', border: 'border-red-500/25', text: 'text-red-400', icon: 'text-red-400' };
  if (type.includes('likes') || type.includes('audience')) return { bg: 'bg-pink-500/8', border: 'border-pink-500/20', text: 'text-pink-400', icon: 'text-pink-400' };
  return { bg: 'bg-white/5', border: 'border-white/10', text: 'text-gray-300', icon: 'text-blue-400' };
};

// ── Genera eventi LIVE dai dati esistenti ──
function generateLiveEvents(myFilms, allFilms, laPrimaEvents, userId) {
  const T = TEMPLATES.it;
  const events = [];
  const myIds = new Set(myFilms.map(f => f.id));

  // 1) PROPRI FILM — rotazione ciclica per massima varieta
  const ownTemplates = [
    { check: (f) => (f.total_revenue || 0) > 5000000, type: 'own_revenue_high', gen: (f, T) => T.own_revenue_high(f.title) },
    { check: (f) => (f.quality_score || 0) > 60, type: 'own_quality_top', gen: (f, T) => T.own_quality_top(f.title) },
    { check: (f) => ((f.virtual_likes || 0) + (f.likes_count || 0)) > 500, type: 'own_likes_growing', gen: (f, T) => T.own_likes_growing(f.title) },
    { check: (f) => (f.current_cinemas || 0) > 50, type: 'own_cinemas_many', gen: (f, T) => T.own_cinemas_many(f.title, f.current_cinemas) },
    { check: (f) => ((f.virtual_likes || 0) + (f.likes_count || 0)) > 1000, type: 'own_audience_loves', gen: (f, T) => T.own_audience_loves(f.title) },
    { check: (f) => (f.popularity_score || 0) > 50, type: 'own_growing_fast', gen: (f, T) => T.own_growing_fast(f.title) },
    { check: (f) => (f.total_revenue || 0) > 1000000, type: 'own_buzz', gen: (f, T) => T.own_buzz(f.title) },
  ];
  const usedTypes = new Set();
  for (let i = 0; i < Math.min(myFilms.length, 20); i++) {
    const f = myFilms[i];
    const day = f.day_in_theaters || 0;
    // Film nuovissimi (giorno 1-3) sempre in cima
    if (day > 0 && day <= 3) {
      events.push({ type: 'own_in_theaters', text: T.own_in_theaters(f.title, day), filmId: f.id, priority: 95, poster: f.poster_url });
      continue;
    }
    // Rotazione: scegli il primo template NON ancora usato che il film soddisfa
    let found = false;
    for (let j = 0; j < ownTemplates.length; j++) {
      const tmpl = ownTemplates[(i + j) % ownTemplates.length];
      if (tmpl.check(f) && !usedTypes.has(tmpl.type)) {
        events.push({ type: tmpl.type, text: tmpl.gen(f, T), filmId: f.id, priority: 85 - i * 2, poster: f.poster_url });
        usedTypes.add(tmpl.type);
        found = true;
        break;
      }
    }
    // Se tutti i tipi sono gia stati usati, resetta e riprova
    if (!found) {
      usedTypes.clear();
      for (let j = 0; j < ownTemplates.length; j++) {
        const tmpl = ownTemplates[(i + j) % ownTemplates.length];
        if (tmpl.check(f)) {
          events.push({ type: tmpl.type, text: tmpl.gen(f, T), filmId: f.id, priority: 60 - i, poster: f.poster_url });
          usedTypes.add(tmpl.type);
          break;
        }
      }
    }
  }

  // 2) LA PRIMA — eventi live
  for (const e of laPrimaEvents) {
    if (e.film_title) {
      events.push({ type: 'la_prima_live', text: T.la_prima_live(e.film_title), filmId: e.film_id, priority: 100, poster: e.poster_url });
    }
  }

  // 3) FILM GLOBALI — top per revenue, quality, likes
  const globalFilms = allFilms.filter(f => !myIds.has(f.id));
  const sortedByRev = [...globalFilms].sort((a, b) => (b.total_revenue || 0) - (a.total_revenue || 0));
  const sortedByPop = [...globalFilms].sort((a, b) => (b.popularity_score || 0) - (a.popularity_score || 0));
  const sortedByQ   = [...globalFilms].sort((a, b) => (b.quality_score || 0) - (a.quality_score || 0));

  if (sortedByRev[0]) {
    const f = sortedByRev[0];
    events.push({ type: 'global_dominating', text: T.global_dominating(f.title), filmId: f.id, priority: 75, poster: f.poster_url });
    const revM = ((f.total_revenue || 0) / 1000000).toFixed(1);
    events.push({ type: 'global_revenue_rec', text: T.global_revenue_rec(f.title, revM), filmId: f.id, priority: 60, poster: f.poster_url });
  }
  if (sortedByPop[0]) {
    const f = sortedByPop[0];
    events.push({ type: 'global_popular', text: T.global_popular(f.title), filmId: f.id, priority: 65, poster: f.poster_url });
  }
  if (sortedByQ[0]) {
    const f = sortedByQ[0];
    events.push({ type: 'global_quality', text: T.global_quality(f.title), filmId: f.id, priority: 55, poster: f.poster_url });
  }

  // Likes boom globali
  for (const f of globalFilms) {
    const likes = (f.virtual_likes || 0) + (f.likes_count || 0);
    if (likes > 3000) {
      events.push({ type: 'global_likes_boom', text: T.global_likes_boom(f.title, (likes / 1000).toFixed(1) + 'K'), filmId: f.id, priority: 50, poster: f.poster_url });
    }
  }

  // Deduplica per filmId (1 solo evento per film, il più prioritario), ordina
  const seen = new Set();
  return events
    .sort((a, b) => b.priority - a.priority)
    .filter(e => { if (seen.has(e.filmId)) return false; seen.add(e.filmId); return true; });
}

// ── Componente Card Live ──
const LiveCard = ({ event, navigate }) => {
  const Icon = getIcon(event.type);
  const c = getColor(event.type);
  const isOwn = event.type.startsWith('own_');
  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-lg ${c.bg} border ${c.border} cursor-pointer hover:brightness-110 transition-all`}
      onClick={() => event.filmId && navigate(`/films/${event.filmId}`)}
      data-testid={`live-card-${event.type}`}
    >
      {event.poster ? (
        <img src={event.poster} alt="" className="w-10 h-14 rounded object-cover flex-shrink-0 border border-white/10" />
      ) : (
        <div className={`w-10 h-14 rounded ${c.bg} flex items-center justify-center flex-shrink-0`}>
          <Icon className={`w-5 h-5 ${c.icon}`} />
        </div>
      )}
      <div className="flex-1 min-w-0">
        {isOwn && <span className="text-[9px] font-bold uppercase tracking-wider text-yellow-500">Il tuo contenuto</span>}
        <p className={`text-sm leading-snug ${c.text}`}>{event.text}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
    </div>
  );
};

// ── Componente Card News ──
const NewsCard = ({ item, navigate }) => {
  const catColors = {
    trending: 'bg-red-500/20 text-red-400',
    star: 'bg-yellow-500/20 text-yellow-400',
    record: 'bg-green-500/20 text-green-400',
    default: 'bg-purple-500/20 text-purple-400',
  };
  const badge = catColors[item.category] || catColors[item.type] || catColors.default;
  return (
    <div
      className="flex items-start gap-3 p-3 rounded-lg bg-white/[0.03] border border-white/[0.06] cursor-pointer hover:bg-white/[0.06] transition-all"
      onClick={() => {
        const link = item.link || (item.film_id ? `/films/${item.film_id}` : null);
        if (link) navigate(link);
      }}
      data-testid="news-card"
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 mb-1">
          <Badge className={`${badge} text-[9px] h-4 px-1.5`}>{item.category || item.type || 'NEWS'}</Badge>
          {item.importance === 'high' && <Badge className="bg-red-500/20 text-red-400 text-[9px] h-4 px-1.5">HOT</Badge>}
        </div>
        <p className="text-sm font-medium text-gray-200 leading-snug">{item.title_localized || item.title}</p>
        <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{item.content_localized || item.content}</p>
      </div>
      <ChevronRight className="w-4 h-4 text-gray-600 flex-shrink-0 mt-1" />
    </div>
  );
};

// ── Componente Card Pubblico ──
const ReviewCard = ({ review, navigate }) => (
  <div
    className="flex items-start gap-3 p-3 rounded-lg bg-pink-500/[0.04] border border-pink-500/[0.1] cursor-pointer hover:bg-pink-500/[0.08] transition-all"
    onClick={() => review.film_id && navigate(`/films/${review.film_id}`)}
    data-testid="review-card"
  >
    <Avatar className="w-8 h-8 flex-shrink-0">
      <AvatarFallback className="bg-pink-500/20 text-pink-400 text-[10px]">{review.reviewer_name?.[0] || '?'}</AvatarFallback>
    </Avatar>
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-0.5">
        <span className="text-xs font-semibold text-gray-300">{review.reviewer_name}</span>
        <div className="flex items-center gap-0.5">
          {[1,2,3,4,5].map(s => (
            <Star key={s} className={`w-2.5 h-2.5 ${s <= review.rating ? 'fill-yellow-500 text-yellow-500' : 'text-gray-700'}`} />
          ))}
        </div>
      </div>
      <p className="text-xs text-gray-400 italic line-clamp-2">"{review.comment}"</p>
      <p className="text-[10px] text-pink-400/70 mt-0.5">{review.film_title}</p>
    </div>
  </div>
);

// ══════════════════════════════════════════
// ── MAIN COMPONENT ──
// ══════════════════════════════════════════
const CinemaJournal = () => {
  const { api, user } = useContext(AuthContext);
  const { t, language } = useTranslations();
  const navigate = useNavigate();

  const [tab, setTab] = useState('live');
  const [loading, setLoading] = useState(false);

  // Dati riusati dalle API esistenti
  const [myFilms, setMyFilms] = useState([]);
  const [allFilms, setAllFilms] = useState([]);
  const [laPrimaEvents, setLaPrimaEvents] = useState([]);
  const [news, setNews] = useState([]);
  const [otherNews, setOtherNews] = useState([]);
  const [virtualReviews, setVirtualReviews] = useState([]);

  useEffect(() => {
    // Carica ogni API indipendentemente — la UI si popola man mano
    api.get('/films/my').then(r => {
      const my = Array.isArray(r.data) ? r.data : r.data?.films || [];
      setMyFilms(my);
      setAllFilms(my);
    }).catch(() => {});

    api.get('/la-prima/active').then(r => {
      setLaPrimaEvents(r.data?.events || []);
    }).catch(() => {});

    api.get('/cinema-news').then(r => {
      setNews(r.data?.news || []);
    }).catch(() => {});

    api.get('/journal/other-news').then(r => {
      setOtherNews(r.data?.news || []);
    }).catch(() => {});

    api.get('/journal/virtual-reviews').then(r => {
      setVirtualReviews(r.data?.reviews || []);
    }).catch(() => {});
  }, [api]);

  // Genera eventi live (FASE 3 — personalizzazione)
  const liveEvents = useMemo(
    () => generateLiveEvents(myFilms, allFilms, laPrimaEvents, user?.id),
    [myFilms, allFilms, laPrimaEvents, user?.id]
  );

  // Merge news + other-news per tab NEWS
  const mergedNews = useMemo(() => {
    const all = [
      ...news.map(n => ({ ...n, _src: 'news' })),
      ...otherNews.map(n => ({ ...n, _src: 'other' })),
    ];
    return all;
  }, [news, otherNews]);

  const TABS = [
    { id: 'live',     label: 'LIVE',     icon: Zap,            color: 'text-yellow-400', count: liveEvents.length },
    { id: 'news',     label: 'NEWS',     icon: Newspaper,      color: 'text-blue-400',   count: mergedNews.length },
    { id: 'pubblico', label: 'PUBBLICO', icon: MessageCircle,  color: 'text-pink-400',   count: virtualReviews.length },
  ];

  return (
    <div className="pt-14 pb-16 px-3 max-w-lg mx-auto" data-testid="cinema-journal-page">
      {/* ── Header ── */}
      <div className="text-center mb-4">
        <h1 className="font-['Bebas_Neue'] text-3xl tracking-wider text-yellow-400">
          CINEMA JOURNAL
        </h1>
        <div className="flex items-center justify-center gap-2 mt-1">
          <div className="h-px w-10 bg-yellow-500/30" />
          <Newspaper className="w-3.5 h-3.5 text-yellow-500/50" />
          <div className="h-px w-10 bg-yellow-500/30" />
        </div>
      </div>

      {/* ── Tab Bar ── */}
      <div className="flex bg-white/[0.03] rounded-lg p-0.5 mb-4 border border-white/[0.06]" data-testid="journal-tabs">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 rounded-md text-xs font-bold tracking-wide transition-all ${
              tab === t.id
                ? `bg-white/10 ${t.color} shadow-sm`
                : 'text-gray-500 hover:text-gray-400'
            }`}
            data-testid={`journal-tab-${t.id}`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
            {t.count > 0 && (
              <span className={`text-[9px] px-1 py-px rounded-full ${tab === t.id ? 'bg-white/10' : 'bg-white/5'}`}>
                {t.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── TAB LIVE ── */}
      {tab === 'live' && (
        <div className="space-y-2" data-testid="journal-live-tab">
          {liveEvents.length === 0 && myFilms.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <Zap className="w-6 h-6 mx-auto mb-2 animate-pulse text-yellow-500/40" />
              <p className="text-xs">Caricamento eventi live...</p>
            </div>
          ) : liveEvents.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <Zap className="w-6 h-6 mx-auto mb-2 opacity-30" />
              <p className="text-sm">Nessun evento live al momento</p>
              <p className="text-xs text-gray-600 mt-1">Produci film per vedere aggiornamenti</p>
            </div>
          ) : (
            liveEvents.map((e, i) => <LiveCard key={i} event={e} navigate={navigate} />)
          )}
        </div>
      )}

      {/* ── TAB NEWS ── */}
      {tab === 'news' && (
        <div className="space-y-2" data-testid="journal-news-tab">
          {mergedNews.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <Newspaper className="w-6 h-6 mx-auto mb-2 animate-pulse text-blue-500/40" />
              <p className="text-xs">Caricamento news...</p>
            </div>
          ) : (
            mergedNews.map((n, i) => <NewsCard key={i} item={n} navigate={navigate} />)
          )}
        </div>
      )}

      {/* ── TAB PUBBLICO ── */}
      {tab === 'pubblico' && (
        <div className="space-y-2" data-testid="journal-pubblico-tab">
          {virtualReviews.length === 0 ? (
            <div className="text-center py-10 text-gray-500">
              <MessageCircle className="w-6 h-6 mx-auto mb-2 animate-pulse text-pink-500/40" />
              <p className="text-xs">Caricamento voci dal pubblico...</p>
            </div>
          ) : (
            virtualReviews.slice(0, 30).map((r, i) => <ReviewCard key={i} review={r} navigate={navigate} />)
          )}
        </div>
      )}
    </div>
  );
};

export default CinemaJournal;
