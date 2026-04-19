import React, { useEffect, useState, useContext } from 'react';
import { Dialog, DialogContent } from './ui/dialog';
import { Heart, Loader2, User } from 'lucide-react';
import { AuthContext } from '../contexts';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const avatarSrc = (url) => {
  if (!url) return null;
  if (url.startsWith('/')) return `${BACKEND_URL}${url}`;
  return url;
};

function timeAgo(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    const diff = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diff < 60) return 'ora';
    if (diff < 3600) return `${Math.floor(diff / 60)}m fa`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h fa`;
    if (diff < 2592000) return `${Math.floor(diff / 86400)}g fa`;
    return `${Math.floor(diff / 2592000)}mes fa`;
  } catch { return ''; }
}

const CTX_LABEL = { poster: 'Locandina', screenplay: 'Sceneggiatura', trailer: 'Trailer' };

export default function RecentLikesPopup({ open, onClose, contentId, context }) {
  const { api } = useContext(AuthContext);
  const [likers, setLikers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    if (!open || !contentId || !context || !api) return;
    setLoading(true);
    api.get(`/content/${contentId}/likes/recent`, { params: { context, limit: 20 } })
      .then(r => { setLikers(r.data.likers || []); setTotal(r.data.total || 0); })
      .catch(() => { setLikers([]); setTotal(0); })
      .finally(() => setLoading(false));
  }, [open, contentId, context, api]);

  const onLikerClick = (uid) => {
    if (!uid) return;
    onClose?.();
    navigate(`/profile/${uid}`);
  };

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose?.()}>
      <DialogContent className="bg-[#0E0E10] border-white/10 text-white max-w-sm p-4 max-h-[80vh] overflow-y-auto" data-testid="recent-likes-popup">
        <div className="flex items-center gap-2 mb-3 pb-2 border-b border-white/10">
          <Heart className="w-4 h-4 fill-red-500 text-red-500" />
          <h3 className="text-sm font-bold">Ultimi like</h3>
          <span className="text-[10px] text-gray-400 ml-auto">{CTX_LABEL[context] || context}</span>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-gray-500" /></div>
        ) : likers.length === 0 ? (
          <div className="text-center py-6 text-gray-500 text-xs">Ancora nessun like</div>
        ) : (
          <>
            <div className="space-y-1.5" data-testid="recent-likers-list">
              {likers.map((l) => (
                <button key={`${l.user_id}-${l.created_at}`}
                  onClick={() => onLikerClick(l.user_id)}
                  className="w-full flex items-center gap-2 p-1.5 rounded-lg hover:bg-white/5 active:scale-[0.98] transition-all text-left"
                  data-testid={`liker-row-${l.user_id}`}>
                  <div className="w-8 h-8 rounded-full overflow-hidden bg-gradient-to-br from-gray-700 to-gray-900 flex items-center justify-center flex-shrink-0 border border-white/10">
                    {l.avatar_url ? (
                      <img src={avatarSrc(l.avatar_url)} alt="" className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                    ) : (
                      <User className="w-4 h-4 text-gray-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-white truncate">{l.nickname}</p>
                    {l.studio && <p className="text-[9px] text-gray-500 truncate">{l.studio}</p>}
                  </div>
                  <span className="text-[9px] text-gray-500 flex-shrink-0">{timeAgo(l.created_at)}</span>
                </button>
              ))}
            </div>
            {total > likers.length && (
              <p className="text-center text-[10px] text-gray-500 mt-3 pt-2 border-t border-white/5">
                + altri {total - likers.length} like
              </p>
            )}
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
