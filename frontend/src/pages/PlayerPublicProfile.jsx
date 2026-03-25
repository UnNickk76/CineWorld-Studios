import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { AuthContext, useTranslations } from '../contexts';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { toast } from 'sonner';
import { Film, Heart, Trophy, Building, MessageSquare, RefreshCw } from 'lucide-react';
import { LoadingSpinner } from '../components/ErrorBoundary';
import { PlayerBadge } from '../components/PlayerBadge';

const PlayerPublicProfile = () => {
  const { api, user } = useContext(AuthContext);
  const { t } = useTranslations();
  const navigate = useNavigate();
  const [player, setPlayer] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const playerId = window.location.pathname.split('/').pop();
    api.get(`/players/${playerId}/profile`).then(r => {
      setPlayer(r.data);
      setLoading(false);
    }).catch(() => {
      toast.error('Giocatore non trovato');
      navigate('/leaderboard');
    });
  }, [api, navigate]);

  if (loading) return <div className="pt-16 flex items-center justify-center h-96"><RefreshCw className="w-8 h-8 animate-spin text-yellow-500" /></div>;
  if (!player) return null;


  if (loading) return <LoadingSpinner />;

  return (
    <div className="pt-16 pb-20 px-3 max-w-2xl mx-auto" data-testid="player-profile-page">
      <Card className="bg-[#1A1A1A] border-white/10">
        <CardContent className="p-6">
          <div className="flex items-center gap-4 mb-6">
            <Avatar className="w-20 h-20 border-2 border-yellow-500/30">
              <AvatarImage src={player.avatar_url} />
              <AvatarFallback className="bg-yellow-500/20 text-yellow-500 text-2xl">{player.nickname?.[0]}</AvatarFallback>
            </Avatar>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-['Bebas_Neue'] text-2xl"><PlayerBadge badge={player.badge} badgeExpiry={player.badge_expiry} size="lg" inline />{player.nickname}</h1>
                <Badge className="bg-purple-500/20 text-purple-400">Lv.{player.level}</Badge>
              </div>
              <p className="text-gray-400">{player.production_house_name}</p>
              <div className="flex items-center gap-2 mt-1">
                <Badge className="bg-yellow-500/20 text-yellow-400">Fame: {player.fame?.toFixed(0)}</Badge>
                <Badge className={`${player.fame_tier?.name === 'Legend' ? 'bg-yellow-500 text-black' : 'bg-white/10'}`}>
                  {player.fame_tier?.name}
                </Badge>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
            <div className="p-3 rounded bg-white/5 text-center">
              <Film className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
              <p className="text-lg font-bold">{player.films_count}</p>
              <p className="text-xs text-gray-400">Film</p>
            </div>
            <div className="p-3 rounded bg-white/5 text-center">
              <Building className="w-5 h-5 mx-auto mb-1 text-blue-400" />
              <p className="text-lg font-bold">{player.infrastructure_count}</p>
              <p className="text-xs text-gray-400">Infrastrutture</p>
            </div>
            <div className="p-3 rounded bg-white/5 text-center">
              <Heart className="w-5 h-5 mx-auto mb-1 text-red-400" />
              <p className="text-lg font-bold">{player.total_likes_received}</p>
              <p className="text-xs text-gray-400">Like ricevuti</p>
            </div>
            <div className="p-3 rounded bg-white/5 text-center">
              <Trophy className="w-5 h-5 mx-auto mb-1 text-yellow-500" />
              <p className="text-lg font-bold">{player.leaderboard_score?.toFixed(1)}</p>
              <p className="text-xs text-gray-400">Punteggio</p>
            </div>
          </div>

          <div className="p-3 rounded bg-purple-500/10 border border-purple-500/20 mb-4">
            <div className="flex justify-between text-sm mb-1">
              <span>Level {player.level}</span>
              <span className="text-purple-400">{player.level_info?.current_xp} / {player.level_info?.xp_for_next_level} XP</span>
            </div>
            <Progress value={player.level_info?.progress_percent || 0} className="h-2" />
          </div>

          {player.id !== user?.id && (
            <Button className="w-full bg-yellow-500 text-black" onClick={() => navigate(`/chat?dm=${player.id}`)}>
              <MessageSquare className="w-4 h-4 mr-2" /> Invia Messaggio
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default PlayerPublicProfile;
