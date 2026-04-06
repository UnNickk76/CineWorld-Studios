import { useEffect, useRef, useContext } from 'react';
import { toast } from 'sonner';
import { Sparkles, TrendingUp, DollarSign } from 'lucide-react';
import { LanguageContext } from '../contexts';

export function AutoTickNotifications({ api }) {
  const { language } = useContext(LanguageContext);
  const lastCheck = useRef('');

  useEffect(() => {
    if (!api) return;

    const poll = async () => {
      try {
        const res = await api.get('/auto-tick/events');
        const events = res.data?.events || [];
        
        for (const ev of events) {
          const key = ev.type + '_' + ev.created_at;
          if (key === lastCheck.current) continue;
          
          if (ev.type === 'STAR_CREATED') {
            toast(
              language === 'it'
                ? `${ev.actor_name} e' diventata una STAR!`
                : `${ev.actor_name} became a STAR!`,
              {
                icon: <Sparkles className="w-4 h-4 text-yellow-400" />,
                duration: 6000,
                className: 'star-toast',
              }
            );
          } else if (ev.type === 'SKILL_UP') {
            toast(
              language === 'it'
                ? `${ev.actor_name}: ${ev.skill_name} Lv.${ev.new_level}`
                : `${ev.actor_name}: ${ev.skill_name} Lv.${ev.new_level}`,
              {
                icon: <TrendingUp className="w-4 h-4 text-cyan-400" />,
                duration: 4000,
              }
            );
          } else if (ev.type === 'REVENUE_GAINED' && ev.amount > 0) {
            toast(
              language === 'it'
                ? `+$${ev.amount.toLocaleString()} incassati (${ev.film_count} film)`
                : `+$${ev.amount.toLocaleString()} earned (${ev.film_count} films)`,
              {
                icon: <DollarSign className="w-4 h-4 text-green-400" />,
                duration: 4000,
              }
            );
          }
        }

        if (events.length > 0) {
          lastCheck.current = events[0].type + '_' + events[0].created_at;
          // Dismiss non-revenue events after showing
          await api.post('/auto-tick/dismiss').catch(() => {});
        }
      } catch {
        // Silently ignore polling errors
      }
    };

    // Initial check after 3s
    const initial = setTimeout(poll, 3000);
    // Then poll every 60s
    const interval = setInterval(poll, 60000);
    return () => { clearTimeout(initial); clearInterval(interval); };
  }, [api, language]);

  return null; // No visual component, just toast notifications
}
