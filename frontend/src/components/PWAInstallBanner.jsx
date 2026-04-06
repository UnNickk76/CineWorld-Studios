import React, { useState, useEffect, useContext } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, Share2, Plus } from 'lucide-react';
import { LanguageContext } from '../contexts';

// Detect platform
const isIOS = () => /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
const isAndroid = () => /android/i.test(navigator.userAgent);
const isStandalone = () =>
  window.matchMedia('(display-mode: standalone)').matches ||
  window.navigator.standalone === true;

export function PWAInstallBanner({ variant = 'floating' }) {
  const { language } = useContext(LanguageContext);
  const [deferredPrompt, setDeferredPrompt] = useState(null);
  const [showIOSGuide, setShowIOSGuide] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [installed, setInstalled] = useState(isStandalone());

  useEffect(() => {
    if (isStandalone()) { setInstalled(true); return; }

    // Check if user previously dismissed
    const dismissedAt = localStorage.getItem('pwa-dismissed');
    if (dismissedAt && Date.now() - parseInt(dismissedAt) < 24 * 60 * 60 * 1000) {
      setDismissed(true);
    }

    const handler = (e) => { e.preventDefault(); setDeferredPrompt(e); };
    window.addEventListener('beforeinstallprompt', handler);

    const installHandler = () => { setInstalled(true); setDeferredPrompt(null); };
    window.addEventListener('appinstalled', installHandler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
      window.removeEventListener('appinstalled', installHandler);
    };
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') setInstalled(true);
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setDismissed(true);
    setShowIOSGuide(false);
    localStorage.setItem('pwa-dismissed', Date.now().toString());
  };

  // Don't show if already installed or dismissed
  if (installed || dismissed) return null;
  // Don't show if no prompt available AND not iOS
  if (!deferredPrompt && !isIOS()) return null;

  // Inline variant: compact banner inside parent container
  if (variant === 'inline') {
    return (
      <>
        {deferredPrompt && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="w-full mt-2 bg-gradient-to-r from-yellow-500/15 to-amber-600/15 rounded-xl p-2.5 border border-yellow-400/20"
            data-testid="pwa-install-inline"
          >
            <div className="flex items-center gap-2.5">
              <img src="/icons/icon-96x96.png" alt="" className="w-8 h-8 rounded-lg" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-bold text-yellow-400">Installa CineWorld</p>
                <p className="text-[9px] text-gray-400">Esperienza fullscreen</p>
              </div>
              <button
                onClick={handleInstall}
                className="px-3 py-1.5 bg-yellow-500 rounded-lg text-black text-[10px] font-bold flex items-center gap-1 active:scale-95 transition-transform shrink-0"
                data-testid="pwa-install-inline-btn"
              >
                <Download className="w-3 h-3" />
                Installa
              </button>
              <button onClick={handleDismiss} className="p-0.5 text-gray-500 hover:text-white">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </motion.div>
        )}

        {isIOS() && !deferredPrompt && (
          <>
            {!showIOSGuide && (
              <motion.button
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="w-full mt-2 bg-gradient-to-r from-blue-500/15 to-cyan-600/15 rounded-xl p-2.5 border border-blue-400/20 flex items-center gap-2.5"
                onClick={() => setShowIOSGuide(true)}
                data-testid="pwa-ios-inline"
              >
                <img src="/icons/icon-96x96.png" alt="" className="w-8 h-8 rounded-lg" />
                <div className="flex-1 text-left min-w-0">
                  <p className="text-xs font-bold text-white">Installa CineWorld</p>
                  <p className="text-[9px] text-gray-400">Tocca per le istruzioni</p>
                </div>
                <button onClick={(e) => { e.stopPropagation(); handleDismiss(); }} className="p-0.5 text-gray-500">
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.button>
            )}

            <AnimatePresence>
              {showIOSGuide && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-end justify-center"
                  onClick={() => setShowIOSGuide(false)}
                >
                  <motion.div
                    initial={{ y: '100%' }}
                    animate={{ y: 0 }}
                    exit={{ y: '100%' }}
                    transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                    className="w-full max-w-md bg-[#1A1A1A] rounded-t-3xl p-5 pb-8"
                    onClick={e => e.stopPropagation()}
                    style={{ paddingBottom: 'calc(2rem + env(safe-area-inset-bottom, 0px))' }}
                  >
                    <div className="w-10 h-1 bg-gray-600 rounded-full mx-auto mb-5" />
                    <div className="text-center mb-5">
                      <img src="/icons/icon-96x96.png" alt="" className="w-14 h-14 rounded-2xl mx-auto mb-3" />
                      <h2 className="text-lg font-bold text-white">Installa CineWorld</h2>
                      <p className="text-xs text-gray-400 mt-1">Segui questi 3 passaggi</p>
                    </div>
                    <div className="space-y-3">
                      <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                        <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white">Tocca l'icona Condividi</p>
                          <p className="text-[10px] text-gray-500">In basso nella barra di Safari</p>
                        </div>
                        <Share2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                      </div>
                      <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                        <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white">Aggiungi a Home</p>
                          <p className="text-[10px] text-gray-500">Scorri e seleziona questa opzione</p>
                        </div>
                        <Plus className="w-5 h-5 text-blue-400 flex-shrink-0" />
                      </div>
                      <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                        <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">3</span>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-white">Conferma "Aggiungi"</p>
                          <p className="text-[10px] text-gray-500">L'app apparirà sulla tua Home</p>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => setShowIOSGuide(false)}
                      className="w-full mt-5 py-2.5 bg-blue-500 rounded-xl text-white text-sm font-bold active:scale-95 transition-transform"
                      data-testid="pwa-ios-close-guide"
                    >
                      Ho capito
                    </button>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </>
    );
  }

  return (
    <>
      {/* Android/Desktop: Native install prompt */}
      {deferredPrompt && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: 100, opacity: 0 }}
          className="fixed bottom-16 left-3 right-3 sm:left-auto sm:right-4 sm:bottom-4 sm:w-80 z-[60] bg-gradient-to-r from-yellow-500/90 to-amber-600/90 backdrop-blur-lg rounded-2xl p-3 shadow-2xl shadow-yellow-500/20 border border-yellow-400/30"
          data-testid="pwa-install-banner"
        >
          <div className="flex items-center gap-3">
            <img src="/icons/icon-96x96.png" alt="" className="w-11 h-11 rounded-xl" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-black">CineWorld Studio's</p>
              <p className="text-[10px] text-black/70">
                {language === 'it' ? 'Installa per esperienza fullscreen' : 'Install for fullscreen experience'}
              </p>
            </div>
            <button onClick={handleDismiss} className="p-1 text-black/50 hover:text-black">
              <X className="w-4 h-4" />
            </button>
          </div>
          <button
            onClick={handleInstall}
            className="w-full mt-2 py-2 bg-black rounded-xl text-yellow-400 text-sm font-bold flex items-center justify-center gap-2 active:scale-95 transition-transform"
            data-testid="pwa-install-btn"
          >
            <Download className="w-4 h-4" />
            {language === 'it' ? 'Installa App' : 'Install App'}
          </button>
        </motion.div>
      )}

      {/* iOS: Custom guide */}
      {isIOS() && !deferredPrompt && (
        <>
          {!showIOSGuide && (
            <motion.button
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="fixed bottom-16 left-3 right-3 z-[60] bg-gradient-to-r from-blue-500/90 to-cyan-600/90 backdrop-blur-lg rounded-2xl p-3 shadow-2xl border border-blue-400/30 flex items-center gap-3"
              onClick={() => setShowIOSGuide(true)}
              data-testid="pwa-ios-banner"
            >
              <img src="/icons/icon-96x96.png" alt="" className="w-10 h-10 rounded-xl" />
              <div className="flex-1 text-left">
                <p className="text-sm font-bold text-white">Installa CineWorld</p>
                <p className="text-[10px] text-white/70">Tocca per le istruzioni</p>
              </div>
              <button onClick={(e) => { e.stopPropagation(); handleDismiss(); }} className="p-1 text-white/50">
                <X className="w-4 h-4" />
              </button>
            </motion.button>
          )}

          <AnimatePresence>
            {showIOSGuide && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-[100] bg-black/80 backdrop-blur-sm flex items-end justify-center"
                onClick={() => setShowIOSGuide(false)}
              >
                <motion.div
                  initial={{ y: '100%' }}
                  animate={{ y: 0 }}
                  exit={{ y: '100%' }}
                  transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                  className="w-full max-w-md bg-[#1A1A1A] rounded-t-3xl p-5 pb-8"
                  onClick={e => e.stopPropagation()}
                  style={{ paddingBottom: 'calc(2rem + env(safe-area-inset-bottom, 0px))' }}
                >
                  <div className="w-10 h-1 bg-gray-600 rounded-full mx-auto mb-5" />
                  <div className="text-center mb-5">
                    <img src="/icons/icon-96x96.png" alt="" className="w-14 h-14 rounded-2xl mx-auto mb-3" />
                    <h2 className="text-lg font-bold text-white">Installa CineWorld</h2>
                    <p className="text-xs text-gray-400 mt-1">Segui questi 3 passaggi</p>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                      <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">1</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">Tocca l'icona Condividi</p>
                        <p className="text-[10px] text-gray-500">In basso nella barra di Safari</p>
                      </div>
                      <Share2 className="w-5 h-5 text-blue-400 flex-shrink-0" />
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                      <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">2</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">Aggiungi a Home</p>
                        <p className="text-[10px] text-gray-500">Scorri e seleziona questa opzione</p>
                      </div>
                      <Plus className="w-5 h-5 text-blue-400 flex-shrink-0" />
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded-xl bg-white/5">
                      <span className="w-7 h-7 rounded-full bg-blue-500 flex items-center justify-center text-xs font-bold flex-shrink-0">3</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-white">Conferma "Aggiungi"</p>
                        <p className="text-[10px] text-gray-500">L'app apparirà sulla tua Home</p>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => setShowIOSGuide(false)}
                    className="w-full mt-5 py-2.5 bg-blue-500 rounded-xl text-white text-sm font-bold active:scale-95 transition-transform"
                    data-testid="pwa-ios-close-guide"
                  >
                    Ho capito
                  </button>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </>
  );
}
