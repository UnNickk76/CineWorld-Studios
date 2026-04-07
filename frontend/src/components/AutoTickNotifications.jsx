import { useEffect, useRef, useContext, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { Sparkles, TrendingUp, DollarSign } from 'lucide-react';
import { LanguageContext } from '../contexts';
import { useNavigate } from 'react-router-dom';
import VelionCinematicEvent from './VelionCinematicEvent';

// Timed distribution: 1st after 2min, 2nd after 10min, 3rd after 20min, 4th after 35min
const EVENT_SCHEDULE_MS = [120000, 600000, 1200000, 2100000];

export function AutoTickNotifications({ api }) {
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();
  const loginTime = useRef(Date.now());
  const scheduledTimers = useRef([]);
  const deliveredCinematic = useRef(new Set());
  const [cinematicEvent, setCinematicEvent] = useState(null);

  const handleDone = useCallback(() => {
    setCinematicEvent(null);
  }, []);

  // Show only the latest toast + badge count for rest
  const showEventToast = useCallback((ev, totalPending) => {
    if (ev.type === 'PROJECT_EVENT' && (ev.tier === 'epic' || ev.tier === 'legendary')) {
      // Cinematic — show full animation
      const key = ev.created_at + ev.text;
      if (deliveredCinematic.current.has(key)) return;
      deliveredCinematic.current.add(key);
      setCinematicEvent(ev);
    } else if (ev.type === 'STAR_CREATED') {
      const key = ev.created_at + ev.actor_name;
      if (deliveredCinematic.current.has(key)) return;
      deliveredCinematic.current.add(key);
      setCinematicEvent({
        ...ev,
        text: language === 'it'
          ? `${ev.actor_name} e' diventata una STAR!`
          : `${ev.actor_name} became a STAR!`,
        tier: 'legendary', event_type: 'star_born',
        revenue_mod: 0.30, fame_mod: 50, hype_mod: 25,
      });
    } else if (ev.type === 'REVENUE_GAINED' && ev.amount > 0) {
      // Silenzioso: nessuna notifica per gli incassi automatici
    } else if (ev.type === 'SKILL_UP') {
      toast(
        `${ev.actor_name}: ${ev.skill_name} Lv.${ev.new_level}`,
        { icon: <TrendingUp className="w-4 h-4 text-cyan-400" />, duration: 3000 }
      );
    } else if (ev.type === 'PROJECT_EVENT') {
      // Common/rare — show toast only if sole event, else compress
      if (totalPending <= 1) {
        const icon = ev.event_type === 'negative'
          ? <span className="text-red-400 text-sm">!</span>
          : <Sparkles className="w-4 h-4 text-yellow-400" />;
        toast(ev.text, { icon, duration: ev.tier === 'rare' ? 5000 : 3000 });
      }
    }
  }, [language, navigate]);

  useEffect(() => {
    if (!api) return;
    loginTime.current = Date.now();
    deliveredCinematic.current.clear();

    // Clear old timers on mount (fresh login)
    sessionStorage.setItem('cw_unread_events', '0');
    window.dispatchEvent(new Event('cw-unread-update'));

    const poll = async () => {
      try {
        const res = await api.get('/auto-tick/events');
        const events = res.data?.events || [];
        if (events.length === 0) return;

        // Sort: legendary first, then epic, rare, common
        const priorityOrder = { legendary: 0, epic: 1, rare: 2, common: 3 };
        const cinematicEvents = [];
        const normalEvents = [];

        for (const ev of events) {
          if (ev.type === 'PROJECT_EVENT' && (ev.tier === 'epic' || ev.tier === 'legendary')) {
            cinematicEvents.push(ev);
          } else if (ev.type === 'STAR_CREATED') {
            cinematicEvents.push(ev);
          } else {
            normalEvents.push(ev);
          }
        }

        // Schedule cinematic events with timed distribution
        cinematicEvents.sort((a, b) => (priorityOrder[a.tier] || 3) - (priorityOrder[b.tier] || 3));
        
        const elapsed = Date.now() - loginTime.current;
        cinematicEvents.forEach((ev, i) => {
          const scheduleAt = EVENT_SCHEDULE_MS[i] || EVENT_SCHEDULE_MS[EVENT_SCHEDULE_MS.length - 1] + (i - 3) * 900000;
          const delay = Math.max(0, scheduleAt - elapsed);
          const timer = setTimeout(() => {
            showEventToast(ev, cinematicEvents.length - i);
          }, delay);
          scheduledTimers.current.push(timer);
        });

        // Show only latest normal toast immediately + update badge
        if (normalEvents.length > 0) {
          // Always show revenue
          const revenueEv = normalEvents.find(e => e.type === 'REVENUE_GAINED');
          // Revenue events are silent — skip toast
          
          // Show only latest PROJECT_EVENT or SKILL_UP (not revenue)
          const latestNormal = normalEvents.find(e => e.type !== 'REVENUE_GAINED');
          if (latestNormal) showEventToast(latestNormal, normalEvents.length);

          // If more than 1 non-revenue event, show summary toast
          const nonRevenue = normalEvents.filter(e => e.type !== 'REVENUE_GAINED');
          if (nonRevenue.length > 1) {
            toast(
              language === 'it'
                ? `+${nonRevenue.length - 1} altri eventi`
                : `+${nonRevenue.length - 1} more events`,
              {
                icon: <span className="inline-flex items-center justify-center w-5 h-5 bg-red-500 text-white text-[10px] font-bold rounded-full">{nonRevenue.length}</span>,
                duration: 4000,
                action: { label: language === 'it' ? 'Vedi' : 'View', onClick: () => navigate('/event-history') },
              }
            );
          }

          // Update unread badge
          const prev = parseInt(sessionStorage.getItem('cw_unread_events') || '0');
          sessionStorage.setItem('cw_unread_events', String(prev + events.length));
          window.dispatchEvent(new Event('cw-unread-update'));
        }

        // Dismiss processed events
        await api.post('/auto-tick/dismiss').catch(() => {});
      } catch {
        // Silent fail
      }
    };

    const initial = setTimeout(poll, 3000);
    const interval = setInterval(poll, 60000);

    return () => {
      clearTimeout(initial);
      clearInterval(interval);
      scheduledTimers.current.forEach(clearTimeout);
      scheduledTimers.current = [];
    };
  }, [api, language, showEventToast, navigate]);

  return (
    <>
      {cinematicEvent && (
        <VelionCinematicEvent events={[cinematicEvent]} onAllDone={handleDone} />
      )}
    </>
  );
}
