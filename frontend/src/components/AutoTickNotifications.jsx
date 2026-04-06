import { useEffect, useRef, useContext, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Sparkles, TrendingUp, DollarSign } from 'lucide-react';
import { LanguageContext } from '../contexts';
import { useNavigate } from 'react-router-dom';
import VelionCinematicEvent from './VelionCinematicEvent';

const TOAST_COOLDOWN_MS = 5000; // max 1 toast every 5 seconds

export function AutoTickNotifications({ api }) {
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const lastCheck = useRef('');
  const lastToastTime = useRef(0);
  const toastQueue = useRef([]);
  const toastTimerRef = useRef(null);
  const [cinematicEvents, setCinematicEvents] = useState([]);

  const handleAllDone = useCallback(() => {
    setCinematicEvents([]);
  }, []);

  // Process toast queue: fire max 1 toast per 5 seconds
  const processToastQueue = useCallback(() => {
    if (toastQueue.current.length === 0) {
      if (toastTimerRef.current) { clearTimeout(toastTimerRef.current); toastTimerRef.current = null; }
      return;
    }
    const now = Date.now();
    const elapsed = now - lastToastTime.current;
    if (elapsed < TOAST_COOLDOWN_MS) {
      // Wait remaining time then retry
      if (!toastTimerRef.current) {
        toastTimerRef.current = setTimeout(() => {
          toastTimerRef.current = null;
          processToastQueue();
        }, TOAST_COOLDOWN_MS - elapsed + 50);
      }
      return;
    }
    const item = toastQueue.current.shift();
    lastToastTime.current = now;
    toast(item.message, item.options);
    // Continue processing if more in queue
    if (toastQueue.current.length > 0) {
      toastTimerRef.current = setTimeout(() => {
        toastTimerRef.current = null;
        processToastQueue();
      }, TOAST_COOLDOWN_MS);
    }
  }, []);

  // Enqueue a toast with anti-spam
  const enqueueToast = useCallback((message, options) => {
    toastQueue.current.push({ message, options });
    processToastQueue();
  }, [processToastQueue]);

  useEffect(() => {
    if (!api) return;

    const poll = async () => {
      try {
        const res = await api.get('/auto-tick/events');
        const events = res.data?.events || [];
        const newCinematic = [];
        const nonCinematic = []; // common/rare PROJECT_EVENT, SKILL_UP, REVENUE

        for (const ev of events) {
          const key = ev.type + '_' + ev.created_at;
          if (key === lastCheck.current) continue;

          if (ev.type === 'PROJECT_EVENT') {
            if (ev.tier === 'epic' || ev.tier === 'legendary') {
              // Epic/legendary → always cinematic (not compressed)
              newCinematic.push(ev);
            } else {
              nonCinematic.push(ev);
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
            nonCinematic.push(ev);
          } else if (ev.type === 'REVENUE_GAINED' && ev.amount > 0) {
            nonCinematic.push(ev);
          }
        }

        // --- NON-CINEMATIC TOAST MANAGEMENT ---
        if (nonCinematic.length > 0) {
          // Update unread counter (all non-cinematic events)
          const prev = parseInt(sessionStorage.getItem('cw_unread_events') || '0');
          const next = prev + nonCinematic.length;
          sessionStorage.setItem('cw_unread_events', String(next));
          window.dispatchEvent(new Event('cw-unread-update'));

          if (nonCinematic.length <= 3) {
            // Show normally (max 3 toasts, queued with anti-spam)
            for (const ev of nonCinematic.slice(0, 3)) {
              enqueueToast(...buildToastArgs(ev, language));
            }
          } else {
            // > 3 events: show only the most recent + summary badge toast
            const mostRecent = nonCinematic[0]; // already sorted desc by backend
            enqueueToast(...buildToastArgs(mostRecent, language));

            const totalCount = nonCinematic.length;
            enqueueToast(
              language === 'it'
                ? `+${totalCount - 1} altri eventi in Cronologia`
                : `+${totalCount - 1} more events in History`,
              {
                icon: <span className="inline-flex items-center justify-center w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full">{totalCount}</span>,
                duration: 4000,
                action: {
                  label: 'Vedi',
                  onClick: () => navigate('/event-history'),
                },
              }
            );
          }
        }

        if (events.length > 0) {
          lastCheck.current = events[0].type + '_' + events[0].created_at;
          await api.post('/auto-tick/dismiss').catch(() => {});
        }

        // Backend already throttles to max 1 cinematic event per poll
        if (newCinematic.length > 0) {
          setCinematicEvents([newCinematic[0]]);
        }
      } catch {
        // Silently ignore polling errors
      }
    };

    const initial = setTimeout(poll, 3000);
    const interval = setInterval(poll, 60000);
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, [api, language, enqueueToast, navigate]);

  return (
    <>
      {cinematicEvents.length > 0 && (
        <VelionCinematicEvent events={cinematicEvents} onAllDone={handleAllDone} />
      )}
    </>
  );
}

// Build toast arguments from an event
function buildToastArgs(ev, language) {
  if (ev.type === 'PROJECT_EVENT') {
    const icon = ev.event_type === 'negative'
      ? <span className="text-red-400 text-sm">!</span>
      : <Sparkles className="w-4 h-4 text-yellow-400" />;
    return [ev.text, { icon, duration: ev.tier === 'rare' ? 5000 : 3000 }];
  }
  if (ev.type === 'SKILL_UP') {
    return [
      `${ev.actor_name}: ${ev.skill_name} Lv.${ev.new_level}`,
      { icon: <TrendingUp className="w-4 h-4 text-cyan-400" />, duration: 4000 }
    ];
  }
  if (ev.type === 'REVENUE_GAINED') {
    const filmPart = ev.film_count ? `${ev.film_count} film` : '';
    const seriesPart = ev.series_count ? `${ev.series_count} serie` : '';
    const countLabel = [filmPart, seriesPart].filter(Boolean).join(' + ') || 'progetti';
    return [
      language === 'it'
        ? `+$${ev.amount.toLocaleString()} incassati (${countLabel})`
        : `+$${ev.amount.toLocaleString()} earned (${countLabel})`,
      { icon: <DollarSign className="w-4 h-4 text-green-400" />, duration: 4000 }
    ];
  }
  return [ev.text || 'Evento', { duration: 3000 }];
}
