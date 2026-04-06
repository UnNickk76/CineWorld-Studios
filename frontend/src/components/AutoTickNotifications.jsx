import { useEffect, useRef, useContext, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Sparkles, TrendingUp, DollarSign } from 'lucide-react';
import { LanguageContext } from '../contexts';
import VelionCinematicEvent from './VelionCinematicEvent';

const CINEMATIC_COOLDOWN_MS = 20000; // 20 seconds between cinematics

export function AutoTickNotifications({ api }) {
  const { language } = useContext(LanguageContext);
  const lastCheck = useRef('');
  const lastCinematicTime = useRef(0);
  const cinematicQueue = useRef([]);
  const [cinematicEvents, setCinematicEvents] = useState([]);

  const processQueue = useCallback(() => {
    const now = Date.now();
    if (cinematicQueue.current.length === 0) return;
    if (now - lastCinematicTime.current < CINEMATIC_COOLDOWN_MS) {
      // Wait and retry
      setTimeout(processQueue, CINEMATIC_COOLDOWN_MS - (now - lastCinematicTime.current) + 100);
      return;
    }
    const next = cinematicQueue.current.shift();
    lastCinematicTime.current = now;
    setCinematicEvents([next]);
  }, []);

  const handleAllDone = useCallback(() => {
    setCinematicEvents([]);
    // Process next queued event after cooldown
    if (cinematicQueue.current.length > 0) {
      setTimeout(processQueue, CINEMATIC_COOLDOWN_MS);
    }
  }, [processQueue]);

  useEffect(() => {
    if (!api) return;

    const poll = async () => {
      try {
        const res = await api.get('/auto-tick/events');
        const events = res.data?.events || [];
        const newCinematic = [];

        for (const ev of events) {
          const key = ev.type + '_' + ev.created_at;
          if (key === lastCheck.current) continue;

          if (ev.type === 'PROJECT_EVENT') {
            if (ev.tier === 'epic' || ev.tier === 'legendary') {
              newCinematic.push(ev);
            } else {
              const icon = ev.event_type === 'negative'
                ? <span className="text-red-400 text-sm">!</span>
                : <Sparkles className="w-4 h-4 text-yellow-400" />;
              toast(ev.text, { icon, duration: ev.tier === 'rare' ? 5000 : 3000 });
            }
          } else if (ev.type === 'STAR_CREATED') {
            newCinematic.push({
              ...ev,
              text: language === 'it'
                ? `${ev.actor_name} e' diventata una STAR!`
                : `${ev.actor_name} became a STAR!`,
              tier: 'legendary',
              event_type: 'star_born',
              revenue_mod: 0.30,
              fame_mod: 50,
              hype_mod: 25,
            });
          } else if (ev.type === 'SKILL_UP') {
            toast(
              `${ev.actor_name}: ${ev.skill_name} Lv.${ev.new_level}`,
              { icon: <TrendingUp className="w-4 h-4 text-cyan-400" />, duration: 4000 }
            );
          } else if (ev.type === 'REVENUE_GAINED' && ev.amount > 0) {
            toast(
              language === 'it'
                ? `+$${ev.amount.toLocaleString()} incassati (${ev.film_count} film)`
                : `+$${ev.amount.toLocaleString()} earned (${ev.film_count} films)`,
              { icon: <DollarSign className="w-4 h-4 text-green-400" />, duration: 4000 }
            );
          }
        }

        if (events.length > 0) {
          lastCheck.current = events[0].type + '_' + events[0].created_at;
          await api.post('/auto-tick/dismiss').catch(() => {});
        }

        // Queue cinematic events with anti-spam (max 3)
        if (newCinematic.length > 0) {
          cinematicQueue.current.push(...newCinematic.slice(0, 3));
          processQueue();
        }
      } catch {
        // Silently ignore polling errors
      }
    };

    const initial = setTimeout(poll, 3000);
    const interval = setInterval(poll, 60000);
    return () => { clearTimeout(initial); clearInterval(interval); };
  }, [api, language, processQueue]);

  return (
    <>
      {cinematicEvents.length > 0 && (
        <VelionCinematicEvent events={cinematicEvents} onAllDone={handleAllDone} />
      )}
    </>
  );
}
