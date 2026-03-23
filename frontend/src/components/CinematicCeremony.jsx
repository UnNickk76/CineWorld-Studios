// CinematicCeremony.jsx — Fullscreen animated festival ceremony
// 9 phases: intro, presentation, category, nomination, suspense, reveal, prize, transition, finale

import React, { useState, useEffect, useRef, useCallback, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { AuthContext } from '../contexts';
import { X, Trophy, Award, Star, Send, MessageSquare, Film, Users } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';

// ═══════════════════════════════════════
// PARTICLES (CSS-only gold dust)
// ═══════════════════════════════════════
const Particles = ({ count = 30, color = 'gold' }) => (
  <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
    {Array.from({ length: count }).map((_, i) => {
      const size = Math.random() * 4 + 1;
      const x = Math.random() * 100;
      const delay = Math.random() * 5;
      const duration = 4 + Math.random() * 6;
      const c = color === 'gold' ? `rgba(255,${180 + Math.floor(Math.random()*60)},50,${0.3 + Math.random()*0.5})` : `rgba(255,255,255,${0.2 + Math.random()*0.3})`;
      return (
        <div key={i} className="absolute rounded-full" style={{
          width: size, height: size, left: `${x}%`, bottom: '-5%',
          background: c, boxShadow: `0 0 ${size*2}px ${c}`,
          animation: `particleFloat ${duration}s ${delay}s linear infinite`
        }} />
      );
    })}
  </div>
);

// ═══════════════════════════════════════
// HEARTBEAT VISUAL PULSE
// ═══════════════════════════════════════
const HeartbeatPulse = () => (
  <div className="absolute inset-0 pointer-events-none z-0">
    <div className="absolute inset-0 animate-pulse" style={{
      background: 'radial-gradient(circle at 50% 50%, rgba(255,200,50,0.08) 0%, transparent 60%)',
      animationDuration: '1.2s'
    }} />
    <div className="absolute inset-0" style={{
      background: 'radial-gradient(circle at 50% 50%, rgba(255,200,50,0.04) 0%, transparent 40%)',
      animation: 'heartbeat 1.2s ease-in-out infinite'
    }} />
  </div>
);

// ═══════════════════════════════════════
// PHASE COMPONENTS
// ═══════════════════════════════════════

const PhaseIntro = ({ festivalName, onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 5000); return () => clearTimeout(t); }, [onComplete]);
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 1.5 }}>
      <Particles count={40} color="gold" />
      <motion.div initial={{ scale: 0.5, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, duration: 1.5, type: 'spring', damping: 15 }} className="relative z-10 text-center">
        <Award className="w-16 h-16 sm:w-24 sm:h-24 text-yellow-400 mx-auto mb-4 sm:mb-6 drop-shadow-[0_0_30px_rgba(255,200,50,0.6)]" />
        <h1 className="font-['Bebas_Neue'] text-3xl sm:text-5xl lg:text-7xl text-yellow-400 tracking-widest drop-shadow-[0_0_20px_rgba(255,200,50,0.4)]">
          {festivalName}
        </h1>
      </motion.div>
      <motion.p className="mt-6 sm:mt-8 text-gray-300 text-sm sm:text-lg italic relative z-10 text-center px-4"
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2, duration: 1 }}>
        Signore e signori...
      </motion.p>
      <motion.p className="mt-2 text-gray-400 text-xs sm:text-base italic relative z-10 text-center px-4"
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 3.5, duration: 1 }}>
        Benvenuti alla notte più attesa del cinema.
      </motion.p>
    </motion.div>
  );
};

const PhasePresentation = ({ onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 6000); return () => clearTimeout(t); }, [onComplete]);
  const lines = [
    { text: 'Le storie hanno emozionato.', delay: 0.5 },
    { text: 'I protagonisti hanno brillato.', delay: 2 },
    { text: 'Ma solo pochi entreranno nella leggenda.', delay: 4 },
  ];
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <Particles count={15} color="white" />
      <div className="relative z-10 text-center px-4 max-w-2xl">
        {lines.map((line, i) => (
          <motion.p key={i} className="text-lg sm:text-2xl lg:text-3xl text-white/90 mb-3 sm:mb-4 font-light"
            initial={{ opacity: 0, x: -30 }} animate={{ opacity: 1, x: 0 }}
            transition={{ delay: line.delay, duration: 1 }}>
            {line.text}
          </motion.p>
        ))}
      </div>
    </motion.div>
  );
};

const PhaseCategory = ({ category, onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 3500); return () => clearTimeout(t); }, [onComplete]);
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.p className="text-gray-400 text-sm sm:text-lg mb-4 relative z-10"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }}>
        E ora...
      </motion.p>
      <motion.div className="relative z-10 text-center" initial={{ scale: 0.3, opacity: 0, rotateY: 90 }}
        animate={{ scale: 1, opacity: 1, rotateY: 0 }}
        transition={{ delay: 1, duration: 0.8, type: 'spring', damping: 12 }}>
        <div className="px-6 sm:px-12 py-4 sm:py-6 border-2 border-yellow-500/60 rounded-2xl bg-yellow-500/10 backdrop-blur-sm
          shadow-[0_0_60px_rgba(255,200,50,0.15)]">
          <p className="text-yellow-500/80 text-xs sm:text-sm tracking-[0.3em] mb-1">LA CATEGORIA</p>
          <h2 className="font-['Bebas_Neue'] text-2xl sm:text-4xl lg:text-5xl text-yellow-400 tracking-wide">
            {category?.name || category?.category_name || 'MIGLIOR FILM'}
          </h2>
        </div>
      </motion.div>
    </motion.div>
  );
};

const PhaseNomination = ({ nominees, onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 2000 + (nominees?.length || 5) * 1500); return () => clearTimeout(t); }, [onComplete, nominees]);
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative px-4"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.p className="text-gray-300 text-sm sm:text-lg mb-6 sm:mb-8 italic relative z-10"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        I candidati sono...
      </motion.p>
      <div className="flex flex-wrap justify-center gap-3 sm:gap-4 max-w-4xl relative z-10">
        {nominees?.map((nom, i) => (
          <motion.div key={nom.id} initial={{ opacity: 0, y: 40, scale: 0.8 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: 1.5 + i * 1.2, duration: 0.6, type: 'spring' }}
            className="w-28 sm:w-36 p-3 sm:p-4 rounded-xl bg-white/5 border border-white/10 backdrop-blur-sm text-center hover:border-yellow-500/30 transition-colors">
            <Film className="w-6 h-6 sm:w-8 sm:h-8 text-gray-500 mx-auto mb-2" />
            <p className="text-white text-xs sm:text-sm font-medium truncate">{nom.name}</p>
            {nom.film_title && nom.film_title !== nom.name && (
              <p className="text-gray-500 text-[10px] truncate mt-0.5">{nom.film_title}</p>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

const PhaseSuspense = ({ onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 4000); return () => clearTimeout(t); }, [onComplete]);
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <HeartbeatPulse />
      <motion.p className="text-xl sm:text-3xl lg:text-4xl text-white font-light relative z-10 text-center"
        initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 1, 0.7, 1] }}
        transition={{ duration: 2, repeat: 1, repeatDelay: 0.5 }}>
        E il vincitore è...
      </motion.p>
      <motion.div className="mt-6 sm:mt-8 flex gap-1 sm:gap-2 relative z-10" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1 }}>
        {[0, 1, 2].map(i => (
          <motion.div key={i} className="w-2 h-2 sm:w-3 sm:h-3 rounded-full bg-yellow-400"
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 0.8, delay: i * 0.3, repeat: Infinity }} />
        ))}
      </motion.div>
    </motion.div>
  );
};

const PhaseReveal = ({ winner, category, onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 5000); return () => clearTimeout(t); }, [onComplete]);
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <Particles count={50} color="gold" />
      {/* Flash */}
      <motion.div className="absolute inset-0 bg-yellow-400/20 z-0"
        initial={{ opacity: 1 }} animate={{ opacity: 0 }} transition={{ duration: 1 }} />
      {/* Winner card */}
      <motion.div className="relative z-10 text-center"
        initial={{ scale: 0.1, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.8, type: 'spring', damping: 10 }}>
        <div className="px-8 sm:px-16 py-6 sm:py-10 rounded-2xl border-2 border-yellow-500 bg-gradient-to-b from-yellow-500/20 to-transparent
          shadow-[0_0_80px_rgba(255,200,50,0.3)]">
          <Trophy className="w-12 h-12 sm:w-16 sm:h-16 text-yellow-400 mx-auto mb-3 sm:mb-4 drop-shadow-[0_0_20px_rgba(255,200,50,0.6)]" />
          <h2 className="font-['Bebas_Neue'] text-3xl sm:text-5xl lg:text-6xl text-yellow-400 tracking-wide mb-2 drop-shadow-[0_0_15px_rgba(255,200,50,0.5)]">
            {winner?.name}
          </h2>
          {winner?.film_title && (
            <p className="text-gray-300 text-sm sm:text-lg">{winner.film_title}</p>
          )}
          <motion.p className="text-yellow-500/70 text-xs sm:text-sm mt-3 sm:mt-4 italic"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 2 }}>
            entra nella storia di CineWorld!
          </motion.p>
        </div>
      </motion.div>
    </motion.div>
  );
};

const PhasePrize = ({ rewards, onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 3500); return () => clearTimeout(t); }, [onComplete]);
  const items = [
    rewards?.xp && { label: `+${rewards.xp} XP`, color: 'text-yellow-400', delay: 0.5 },
    rewards?.money && { label: `+$${(rewards.money/1000).toFixed(0)}K`, color: 'text-green-400', delay: 1 },
    rewards?.fame && { label: `+${rewards.fame} Fama`, color: 'text-purple-400', delay: 1.5 },
    rewards?.cinepass && { label: `+${rewards.cinepass} CinePass`, color: 'text-cyan-400', delay: 2 },
  ].filter(Boolean);

  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <motion.p className="text-gray-400 text-sm sm:text-lg mb-6 sm:mb-8 relative z-10"
        initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        Premio assegnato:
      </motion.p>
      <div className="flex flex-col items-center gap-2 sm:gap-3 relative z-10">
        {items.map((item, i) => (
          <motion.div key={i} className={`text-2xl sm:text-4xl font-bold ${item.color} drop-shadow-[0_0_10px_currentColor]`}
            initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }}
            transition={{ delay: item.delay, duration: 0.6, type: 'spring' }}>
            {item.label}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

const PhaseTransition = ({ onComplete }) => {
  useEffect(() => { const t = setTimeout(onComplete, 2500); return () => clearTimeout(t); }, [onComplete]);
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, scale: 0.95 }}>
      <motion.p className="text-gray-300 text-lg sm:text-2xl italic relative z-10 text-center px-4"
        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
        Preparati... il meglio deve ancora arrivare.
      </motion.p>
    </motion.div>
  );
};

const PhaseFinale = ({ onClose }) => {
  return (
    <motion.div className="flex flex-col items-center justify-center h-full relative"
      initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <Particles count={25} color="gold" />
      <div className="relative z-10 text-center px-4 max-w-xl">
        <motion.p className="text-xl sm:text-2xl lg:text-3xl text-white/80 font-light mb-3"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}>
          Il cinema non è solo spettacolo...
        </motion.p>
        <motion.p className="text-xl sm:text-2xl lg:text-3xl text-yellow-400 font-light italic"
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 2 }}>
          è potere, visione... e immortalità.
        </motion.p>
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 4 }}>
          <Button onClick={onClose} className="mt-8 sm:mt-12 bg-yellow-500 text-black hover:bg-yellow-400 text-sm sm:text-base px-8">
            Torna ai Festival
          </Button>
        </motion.div>
      </div>
    </motion.div>
  );
};

// ═══════════════════════════════════════
// CHAT SIDEBAR
// ═══════════════════════════════════════
const CeremonyChat = ({ messages, onSend, sending }) => {
  const [msg, setMsg] = useState('');
  const scrollRef = useRef(null);
  useEffect(() => { if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight; }, [messages]);
  const handleSend = () => { if (msg.trim()) { onSend(msg); setMsg(''); } };

  return (
    <div className="flex flex-col h-full">
      <div className="p-2 sm:p-3 border-b border-white/10 flex items-center gap-2">
        <MessageSquare className="w-3.5 h-3.5 text-yellow-400" />
        <span className="text-xs font-semibold text-gray-300">Chat Live</span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-2 sm:p-3 space-y-1.5 min-h-0">
        {messages?.map(m => (
          <div key={m.id} className="text-xs">
            <span className="font-semibold text-yellow-400">{m.nickname}</span>
            <span className="text-gray-400 ml-1">{m.message}</span>
          </div>
        ))}
        {(!messages || messages.length === 0) && <p className="text-gray-600 text-xs text-center py-4">Nessun messaggio</p>}
      </div>
      <div className="p-2 border-t border-white/10">
        <div className="flex gap-1.5">
          <Input value={msg} onChange={e => setMsg(e.target.value)} placeholder="Scrivi..."
            className="flex-1 bg-white/5 border-white/10 text-xs h-8" maxLength={200}
            onKeyDown={e => e.key === 'Enter' && handleSend()} />
          <Button size="sm" onClick={handleSend} disabled={sending || !msg.trim()}
            className="bg-yellow-500 text-black h-8 px-2"><Send className="w-3.5 h-3.5" /></Button>
        </div>
      </div>
    </div>
  );
};

// ═══════════════════════════════════════
// CSS KEYFRAMES (injected once)
// ═══════════════════════════════════════
const injectStyles = (() => {
  let injected = false;
  return () => {
    if (injected) return;
    injected = true;
    const style = document.createElement('style');
    style.textContent = `
      @keyframes particleFloat {
        0% { transform: translateY(0) translateX(0); opacity: 0; }
        10% { opacity: 1; }
        90% { opacity: 0.6; }
        100% { transform: translateY(-100vh) translateX(${Math.random() > 0.5 ? '' : '-'}30px); opacity: 0; }
      }
      @keyframes heartbeat {
        0%, 100% { transform: scale(1); opacity: 0.3; }
        50% { transform: scale(1.05); opacity: 0.6; }
      }
    `;
    document.head.appendChild(style);
  };
})();

// ═══════════════════════════════════════
// MAIN COMPONENT
// ═══════════════════════════════════════

export const CinematicCeremony = ({ festivalId, festivalName, edition, rewards, categories, chatMessages, viewersCount, onClose, onSendChat, sendingChat, onAnnounceWinner }) => {
  const [phase, setPhase] = useState('intro'); // intro|presentation|category|nomination|suspense|reveal|prize|transition|finale
  const [currentCatIdx, setCurrentCatIdx] = useState(0);
  const [currentWinner, setCurrentWinner] = useState(null);
  const [announcedCategories, setAnnouncedCategories] = useState(new Set());
  const [isAnnouncing, setIsAnnouncing] = useState(false);
  const [showChat, setShowChat] = useState(false);

  useEffect(() => { injectStyles(); }, []);

  // Check for already-announced categories from server
  useEffect(() => {
    if (categories) {
      const announced = new Set();
      categories.forEach((c, i) => { if (c.is_announced) announced.add(i); });
      setAnnouncedCategories(announced);
    }
  }, [categories]);

  const currentCat = categories?.[currentCatIdx];

  const advanceToNextCategory = useCallback(() => {
    const nextIdx = currentCatIdx + 1;
    if (nextIdx < (categories?.length || 0)) {
      setCurrentCatIdx(nextIdx);
      setPhase('transition');
    } else {
      setPhase('finale');
    }
  }, [currentCatIdx, categories]);

  const handleAnnounce = useCallback(async () => {
    if (!currentCat || isAnnouncing) return;
    setIsAnnouncing(true);
    try {
      const result = await onAnnounceWinner(currentCat.category_id);
      if (result?.winner) {
        setCurrentWinner(result.winner);
        setAnnouncedCategories(prev => new Set([...prev, currentCatIdx]));
        setPhase('reveal');
      }
    } catch (e) {
      console.error('Announce error:', e);
    } finally { setIsAnnouncing(false); }
  }, [currentCat, currentCatIdx, isAnnouncing, onAnnounceWinner]);

  // Phase auto-progression
  const handlePhaseComplete = useCallback(() => {
    switch (phase) {
      case 'intro': setPhase('presentation'); break;
      case 'presentation': setPhase('category'); break;
      case 'category': setPhase('nomination'); break;
      case 'nomination': setPhase('suspense'); break;
      case 'suspense': handleAnnounce(); break;
      case 'reveal': setPhase('prize'); break;
      case 'prize': advanceToNextCategory(); break;
      case 'transition': setPhase('category'); break;
      default: break;
    }
  }, [phase, handleAnnounce, advanceToNextCategory]);

  // Skip to specific phase
  const handleSkip = () => {
    if (phase === 'finale') return;
    handlePhaseComplete();
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black" data-testid="cinematic-ceremony" onClick={(e) => {
      if (e.target === e.currentTarget) handleSkip();
    }}>
      {/* Background ambient glow */}
      <div className="absolute inset-0" style={{
        background: phase === 'reveal'
          ? 'radial-gradient(ellipse at 50% 40%, rgba(255,200,50,0.12) 0%, transparent 60%)'
          : phase === 'suspense'
          ? 'radial-gradient(ellipse at 50% 50%, rgba(255,200,50,0.05) 0%, transparent 50%)'
          : 'radial-gradient(ellipse at 50% 30%, rgba(255,255,255,0.03) 0%, transparent 60%)'
      }} />

      {/* Top bar */}
      <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between p-3 sm:p-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            <span className="text-[10px] sm:text-xs text-red-400 font-bold tracking-wider">LIVE</span>
          </div>
          <span className="text-[10px] sm:text-xs text-gray-500"><Users className="w-3 h-3 inline mr-0.5" />{viewersCount || 0}</span>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={() => setShowChat(!showChat)}
            className="text-gray-400 hover:text-white h-7 px-2 text-[10px] sm:text-xs gap-1">
            <MessageSquare className="w-3.5 h-3.5" /> Chat
          </Button>
          <Button variant="ghost" size="sm" onClick={handleSkip}
            className="text-gray-500 hover:text-white h-7 px-2 text-[10px] sm:text-xs">
            Salta
          </Button>
          <Button variant="ghost" size="sm" onClick={onClose}
            className="text-gray-500 hover:text-white h-7 px-2">
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Progress bar */}
      <div className="absolute top-12 left-0 right-0 z-20 px-4">
        <div className="flex gap-0.5 sm:gap-1">
          {categories?.map((cat, i) => (
            <div key={i} className={`h-0.5 sm:h-1 flex-1 rounded-full transition-all duration-500 ${
              announcedCategories.has(i) ? 'bg-yellow-500' :
              i === currentCatIdx ? 'bg-yellow-500/40' : 'bg-white/10'
            }`} />
          ))}
        </div>
      </div>

      {/* Main stage */}
      <div className="absolute inset-0 pt-16 pb-4 flex">
        <div className={`flex-1 min-w-0 flex items-center justify-center transition-all ${showChat ? 'pr-64 sm:pr-72' : ''}`}>
          <AnimatePresence mode="wait">
            {phase === 'intro' && <PhaseIntro key="intro" festivalName={festivalName} onComplete={handlePhaseComplete} />}
            {phase === 'presentation' && <PhasePresentation key="presentation" onComplete={handlePhaseComplete} />}
            {phase === 'category' && <PhaseCategory key={`cat-${currentCatIdx}`} category={currentCat} onComplete={handlePhaseComplete} />}
            {phase === 'nomination' && <PhaseNomination key={`nom-${currentCatIdx}`} nominees={currentCat?.nominees} onComplete={handlePhaseComplete} />}
            {phase === 'suspense' && <PhaseSuspense key={`sus-${currentCatIdx}`} onComplete={handlePhaseComplete} />}
            {phase === 'reveal' && <PhaseReveal key={`rev-${currentCatIdx}`} winner={currentWinner} category={currentCat} onComplete={handlePhaseComplete} />}
            {phase === 'prize' && <PhasePrize key={`prize-${currentCatIdx}`} rewards={rewards} onComplete={handlePhaseComplete} />}
            {phase === 'transition' && <PhaseTransition key={`trans-${currentCatIdx}`} onComplete={handlePhaseComplete} />}
            {phase === 'finale' && <PhaseFinale key="finale" onClose={onClose} />}
          </AnimatePresence>
        </div>

        {/* Chat panel */}
        <AnimatePresence>
          {showChat && (
            <motion.div initial={{ x: 300, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 300, opacity: 0 }}
              className="w-64 sm:w-72 bg-[#0a0a0c] border-l border-white/10 flex-shrink-0">
              <CeremonyChat messages={chatMessages} onSend={onSendChat} sending={sendingChat} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Bottom info */}
      <div className="absolute bottom-3 left-0 right-0 z-20 flex justify-center">
        <Badge className="bg-white/5 text-gray-500 text-[10px] border-0">
          {phase === 'finale' ? 'Cerimonia conclusa' :
            `Categoria ${currentCatIdx + 1}/${categories?.length || 0}`}
        </Badge>
      </div>
    </div>
  );
};
