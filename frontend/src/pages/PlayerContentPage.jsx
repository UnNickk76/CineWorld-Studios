// CineWorld — Player Content Page (I Suoi Contenuti)
// Public view of another player's content
import React, { useState, useEffect, useContext } from 'react';
import { useParams } from 'react-router-dom';
import { AuthContext } from '../contexts';
import MyFilms from './MyFilms';

export default function PlayerContentPage() {
  const { playerId } = useParams();
  const { api } = useContext(AuthContext);
  const [playerName, setPlayerName] = useState('');

  useEffect(() => {
    if (playerId) {
      api.get(`/players/${playerId}/profile`).then(r => {
        setPlayerName(r.data?.nickname || r.data?.production_house_name || 'Player');
      }).catch(() => setPlayerName('Player'));
    }
  }, [playerId, api]);

  return <MyFilms playerId={playerId} playerName={playerName} isPublicView={true} />;
}
