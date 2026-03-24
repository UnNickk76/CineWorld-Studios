import React, { useState, useEffect, useContext } from 'react';
import { LanguageContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { CheckCircle, Download, Globe, Share2, Plus, Copy, Link2, Smartphone, X } from 'lucide-react';

const DownloadAppPage = () => {
  const { language } = useContext(LanguageContext);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isIOS, setIsIOS] = useState(false);
  const [isAndroid, setIsAndroid] = useState(false);

  useEffect(() => {
    const ua = navigator.userAgent || '';
    setIsIOS(/iPad|iPhone|iPod/.test(ua) && !window.MSStream);
    setIsAndroid(/android/i.test(ua));

    if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone) {
      setIsInstalled(true);
    }

    const handler = (e) => { e.preventDefault(); setDeferredPrompt(e); };
    window.addEventListener('beforeinstallprompt', handler);
    window.addEventListener('appinstalled', () => { setIsInstalled(true); setDeferredPrompt(null); });
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') setIsInstalled(true);
    setDeferredPrompt(null);
  };

  const appUrl = window.location.origin;

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white p-4 pt-20" style={{ paddingBottom: 'calc(5rem + env(safe-area-inset-bottom, 0px))' }}>
      <div className="max-w-lg mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-8">
          <img src="/icons/icon-192x192.png" alt="CineWorld" className="w-24 h-24 mx-auto rounded-2xl shadow-lg shadow-yellow-500/20 mb-4" />
          <h1 className="text-3xl font-['Bebas_Neue'] text-yellow-500">CineWorld Studio's</h1>
          <p className="text-gray-400 mt-2 text-sm">
            {language === 'it' ? 'Gioco multiplayer di produzione cinematografica' : 'Multiplayer movie production game'}
          </p>
        </motion.div>

        {isInstalled ? (
          <Card className="bg-green-500/10 border-green-500/30 mb-6">
            <CardContent className="p-6 text-center">
              <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
              <h2 className="text-xl font-semibold text-green-400">
                {language === 'it' ? 'App Installata!' : 'App Installed!'}
              </h2>
              <p className="text-gray-400 mt-2 text-sm">
                {language === 'it' ? 'Puoi trovare CineWorld nella tua home screen.' : 'You can find CineWorld on your home screen.'}
              </p>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Android / Desktop Install */}
            {(isAndroid || deferredPrompt) && (
              <Card className="bg-[#1A1A1A] border-green-500/30 mb-6" data-testid="android-install-card">
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-green-500/15 flex items-center justify-center">
                      <Smartphone className="w-5 h-5 text-green-500" />
                    </div>
                    <div>
                      <h2 className="font-semibold">{isAndroid ? 'Android' : 'Desktop'}</h2>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'Installazione diretta' : 'Direct installation'}</p>
                    </div>
                  </div>
                  <Button onClick={handleInstall} className="w-full bg-green-600 hover:bg-green-500" disabled={!deferredPrompt} data-testid="install-btn">
                    <Download className="w-4 h-4 mr-2" />
                    {language === 'it' ? 'Installa App' : 'Install App'}
                  </Button>
                </CardContent>
              </Card>
            )}

            {/* iOS Instructions */}
            {isIOS && (
              <Card className="bg-[#1A1A1A] border-blue-500/30 mb-6" data-testid="ios-install-card">
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-blue-500/15 flex items-center justify-center">
                      <Smartphone className="w-5 h-5 text-blue-500" />
                    </div>
                    <div>
                      <h2 className="font-semibold">iPhone / iPad</h2>
                      <p className="text-xs text-gray-400">{language === 'it' ? 'Installazione manuale' : 'Manual installation'}</p>
                    </div>
                  </div>
                  <div className="space-y-3 text-sm">
                    {[
                      { n: 1, title: language === 'it' ? 'Tocca l\'icona Condividi' : 'Tap the Share icon', desc: language === 'it' ? 'In basso nella barra di Safari' : 'At the bottom of Safari', icon: <Share2 className="w-5 h-5 text-blue-400" /> },
                      { n: 2, title: language === 'it' ? 'Seleziona "Aggiungi a Home"' : 'Select "Add to Home Screen"', desc: language === 'it' ? 'Scorri le opzioni' : 'Scroll the options', icon: <Plus className="w-5 h-5 text-blue-400" /> },
                      { n: 3, title: language === 'it' ? 'Conferma "Aggiungi"' : 'Confirm "Add"', desc: language === 'it' ? 'L\'app apparirà sulla Home' : 'The app will appear on Home', icon: <CheckCircle className="w-5 h-5 text-green-400" /> },
                    ].map(s => (
                      <div key={s.n} className="flex items-center gap-3 p-3 rounded-xl bg-black/30">
                        <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">{s.n}</span>
                        <div className="flex-1">
                          <p className="font-medium text-white">{s.title}</p>
                          <p className="text-[10px] text-gray-500">{s.desc}</p>
                        </div>
                        {s.icon}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Desktop generic */}
            {!isIOS && !isAndroid && !deferredPrompt && (
              <Card className="bg-[#1A1A1A] border-yellow-500/30 mb-6">
                <CardContent className="p-5">
                  <div className="flex items-center gap-3 mb-3">
                    <Globe className="w-6 h-6 text-yellow-500" />
                    <h2 className="font-semibold">{language === 'it' ? 'Browser Desktop' : 'Desktop Browser'}</h2>
                  </div>
                  <p className="text-sm text-gray-400">
                    {language === 'it'
                      ? 'Cerca l\'icona di installazione nella barra degli indirizzi del browser.'
                      : 'Look for the install icon in the browser address bar.'}
                  </p>
                </CardContent>
              </Card>
            )}
          </>
        )}

        {/* Share Link */}
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-5">
            <h3 className="font-semibold mb-3 flex items-center gap-2">
              <Link2 className="w-5 h-5 text-yellow-500" />
              {language === 'it' ? 'Condividi con amici' : 'Share with friends'}
            </h3>
            <div className="flex gap-2">
              <Input value={appUrl} readOnly className="bg-black/30 border-white/10 text-sm" />
              <Button
                variant="outline"
                className="border-yellow-500/30 text-yellow-400 shrink-0"
                onClick={() => { navigator.clipboard.writeText(appUrl); toast.success(language === 'it' ? 'Link copiato!' : 'Link copied!'); }}
              >
                <Copy className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="text-center text-xs text-gray-500 mt-8 pb-4">
          <p>CineWorld Studio's v1.0</p>
          <p className="mt-1">{language === 'it' ? 'L\'app si aggiorna automaticamente.' : 'The app updates automatically.'}</p>
        </div>
      </div>
    </div>
  );
};

export default DownloadAppPage;
