// CineWorld Studio's - Release Notes Page
// Extracted from App.js

import React, { useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, Check } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { AuthContext, useTranslations } from '../contexts';

const ReleaseNotes = () => {
  const { api } = useContext(AuthContext);
  const { language } = useTranslations();
  const navigate = useNavigate();
  const [releases, setReleases] = useState([]);
  const [currentVersion, setCurrentVersion] = useState('0.000');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/release-notes').then(res => {
      setReleases(res.data.releases || []);
      setCurrentVersion(res.data.current_version || '0.000');
      // Mark release notes as read when visiting the page
      api.post('/release-notes/mark-read').catch(() => {});
    }).finally(() => setLoading(false));
  }, [api]);

  if (loading) {
    return (
      <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-700 rounded w-1/3"></div>
          {[1,2,3].map(i => <div key={i} className="h-32 bg-gray-700 rounded"></div>)}
        </div>
      </div>
    );
  }

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="release-notes-page">
      <div className="flex items-center gap-3 mb-6">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="h-8 w-8">
          <ArrowLeft className="w-4 h-4" />
        </Button>
        <div>
          <h1 className="font-['Bebas_Neue'] text-2xl sm:text-3xl flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-400" />
            {language === 'it' ? 'NOTE DI RILASCIO' : 'RELEASE NOTES'}
          </h1>
          <p className="text-sm text-gray-400">
            {language === 'it' ? 'Versione Corrente' : 'Current Version'}: <span className="text-purple-400 font-bold">v{currentVersion}</span>
          </p>
        </div>
      </div>

      <div className="space-y-4">
        {releases.map((release, index) => (
          <Card key={release.version} className={`bg-[#1A1A1A] border-white/10 ${index === 0 ? 'ring-2 ring-purple-500/50' : ''}`}>
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Badge className={`${index === 0 ? 'bg-purple-500' : 'bg-gray-600'} text-white`}>
                    v{release.version}
                  </Badge>
                  <h3 className="font-semibold">{release.title}</h3>
                  {index === 0 && (
                    <Badge className="bg-green-500/20 text-green-400 text-[10px]">
                      {language === 'it' ? 'NUOVO' : 'NEW'}
                    </Badge>
                  )}
                </div>
                <span className="text-xs text-gray-500">{release.date}</span>
              </div>
              <ul className="space-y-1">
                {release.changes.map((change, i) => {
                  // Handle both string and object formats
                  const changeText = typeof change === 'string' ? change : change.text;
                  const changeType = typeof change === 'object' ? change.type : null;
                  
                  return (
                    <li key={i} className="text-sm text-gray-400 flex items-start gap-2">
                      {changeType === 'fix' ? (
                        <span className="w-3 h-3 mt-1 flex-shrink-0 text-red-400">🔧</span>
                      ) : changeType === 'new' ? (
                        <span className="w-3 h-3 mt-1 flex-shrink-0 text-green-400">✨</span>
                      ) : changeType === 'improvement' ? (
                        <span className="w-3 h-3 mt-1 flex-shrink-0 text-blue-400">⬆️</span>
                      ) : (
                        <Check className="w-3 h-3 text-green-400 mt-1 flex-shrink-0" />
                      )}
                      {changeText}
                    </li>
                  );
                })}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

export default ReleaseNotes;
