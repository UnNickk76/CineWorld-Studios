import React, { useState, useEffect, useContext } from 'react';
import { AuthContext, LanguageContext } from '../contexts';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Button } from '../components/ui/button';
import { Ticket, Gift, Flame, Check } from 'lucide-react';
import { toast } from 'sonner';

const DAY_REWARDS = [3, 5, 7, 10, 14, 19, 35];
const DAY_COLORS = ['bg-gray-700', 'bg-gray-600', 'bg-blue-700', 'bg-blue-600', 'bg-purple-700', 'bg-purple-600', 'bg-gradient-to-br from-yellow-500 to-orange-500'];

const LoginRewardPopup = () => {
  const { api, user, refreshUser } = useContext(AuthContext);
  const { language } = useContext(LanguageContext);
  const [open, setOpen] = useState(false);
  const [rewardData, setRewardData] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [justClaimed, setJustClaimed] = useState(false);

  useEffect(() => {
    if (!user) return;
    // Skip reward popup during guest tutorial to avoid overlay clash
    if (user.is_guest && !user.tutorial_completed) return;
    const checkReward = async () => {
      try {
        const res = await api.get('/cinepass/login-reward');
        if (!res.data.claimed_today) {
          setRewardData(res.data);
          setOpen(true);
        }
      } catch {}
    };
    const timer = setTimeout(checkReward, 1500);
    return () => clearTimeout(timer);
  }, [user]);

  const claimReward = async () => {
    setClaiming(true);
    try {
      const res = await api.post('/cinepass/claim-login-reward');
      setJustClaimed(true);
      toast.success(`+${res.data.total} CinePass! ${res.data.bonus > 0 ? `(Bonus 15 giorni: +${res.data.bonus})` : ''}`);
      refreshUser();
      setTimeout(() => setOpen(false), 2000);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore');
    } finally {
      setClaiming(false);
    }
  };

  if (!rewardData) return null;

  const currentDay = rewardData.next_day;

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="bg-[#141416] border-gray-800 text-white max-w-sm" data-testid="login-reward-popup">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-center gap-2 text-lg">
            <Flame className="w-5 h-5 text-orange-400" />
            {language === 'it' ? 'Bonus Giornaliero' : 'Daily Bonus'}
          </DialogTitle>
        </DialogHeader>

        {/* Streak info */}
        <div className="text-center mb-2">
          <p className="text-xs text-gray-400">
            {language === 'it' ? 'Giorni consecutivi:' : 'Consecutive days:'}{' '}
            <span className="text-cyan-400 font-bold">{rewardData.total_consecutive}</span>
          </p>
          {rewardData.bonus_15 && (
            <p className="text-xs text-yellow-400 mt-1 font-bold">+15 Bonus 15 giorni!</p>
          )}
        </div>

        {/* 7 day cards */}
        <div className="grid grid-cols-7 gap-1">
          {rewardData.days.map((day, i) => {
            const isCurrent = day.current && !justClaimed;
            const isClaimed = day.claimed || (day.current && justClaimed);
            return (
              <button
                key={i}
                disabled={!isCurrent || claiming}
                onClick={isCurrent ? claimReward : undefined}
                className={`relative flex flex-col items-center justify-center rounded-lg py-2 transition-all ${
                  isCurrent ? 'ring-2 ring-cyan-400 scale-105 cursor-pointer' :
                  isClaimed ? 'opacity-50' : 'opacity-40 cursor-default'
                } ${DAY_COLORS[i]}`}
                data-testid={`login-day-${day.day}`}
              >
                {isClaimed && <Check className="absolute top-0.5 right-0.5 w-3 h-3 text-green-400" />}
                <span className="text-[9px] font-bold text-white/80">G{day.day}</span>
                <Ticket className="w-3.5 h-3.5 text-white my-0.5" />
                <span className="text-[10px] font-bold text-white">{day.reward}</span>
                {day.bonus && <Gift className="w-2.5 h-2.5 text-yellow-300 mt-0.5" />}
              </button>
            );
          })}
        </div>

        {/* Claim button */}
        {!justClaimed ? (
          <Button
            onClick={claimReward}
            disabled={claiming}
            className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 font-bold mt-2"
            data-testid="claim-login-reward"
          >
            <Ticket className="w-4 h-4 mr-2" />
            {claiming ? '...' : `${language === 'it' ? 'Riscuoti' : 'Claim'} +${DAY_REWARDS[currentDay - 1]} CinePass`}
          </Button>
        ) : (
          <div className="text-center text-green-400 font-bold text-sm mt-2" data-testid="reward-claimed">
            CinePass riscossi!
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default LoginRewardPopup;
