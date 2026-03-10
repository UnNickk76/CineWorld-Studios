// CineWorld Studio's - Credits Page
// Extracted from App.js

import React, { useContext, useState, useEffect } from 'react';
import { Clapperboard, Award, Mail, Send, CheckCircle } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { Input } from '../components/ui/input';
import { AuthContext } from '../contexts';
import { toast } from 'sonner';

const CreditsPage = () => {
  const { api, user } = useContext(AuthContext);
  const [credits, setCredits] = useState(null);
  const [contactSubject, setContactSubject] = useState('');
  const [contactMessage, setContactMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    api.get('/game/credits').then(r => setCredits(r.data)).catch(console.error);
  }, [api]);

  const handleContactSubmit = async () => {
    if (!contactSubject.trim() || !contactMessage.trim()) {
      toast.error('Compila tutti i campi');
      return;
    }
    
    setSending(true);
    try {
      await api.post('/contact/creator', {
        subject: contactSubject,
        message: contactMessage
      });
      toast.success('Messaggio inviato al Creator!');
      setSent(true);
      setContactSubject('');
      setContactMessage('');
      setTimeout(() => setSent(false), 5000);
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Errore invio messaggio');
    } finally {
      setSending(false);
    }
  };

  if (!credits) return <div className="pt-20 text-center">Caricamento...</div>;

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="credits-page">
      <div className="text-center mb-8">
        <Clapperboard className="w-16 h-16 text-yellow-500 mx-auto mb-4" />
        <h1 className="font-['Bebas_Neue'] text-4xl">{credits.game_title}</h1>
        <p className="text-gray-400">Versione {credits.version}</p>
      </div>
      
      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-2xl mb-4 text-yellow-500">Credits</h2>
          <div className="space-y-4">
            {credits.credits.map((credit, i) => (
              <div key={i} className="flex items-center gap-4 p-4 bg-white/5 rounded-lg border border-white/10">
                <Award className="w-10 h-10 text-yellow-500 flex-shrink-0" />
                <div>
                  <p className="font-bold text-lg">{credit.name}</p>
                  <p className="text-sm text-yellow-400 font-semibold">{credit.role}</p>
                  <p className="text-xs text-gray-400 mt-1">{credit.description}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Contact Creator Section */}
      <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/5 border-purple-500/20 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-2xl mb-2 text-purple-400 flex items-center gap-2">
            <Mail className="w-6 h-6" /> Contattaci
          </h2>
          <p className="text-gray-400 text-sm mb-4">
            Hai suggerimenti, bug da segnalare o vuoi semplicemente dire ciao? Scrivi direttamente al Creator!
          </p>
          
          {sent ? (
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <p className="text-green-400 font-semibold">Messaggio inviato con successo!</p>
              <p className="text-gray-400 text-sm">Il Creator ti risponderà nella chat.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Oggetto</label>
                <Input
                  placeholder="Es: Suggerimento, Bug Report, Feedback..."
                  value={contactSubject}
                  onChange={(e) => setContactSubject(e.target.value)}
                  className="bg-black/30 border-white/10"
                  maxLength={100}
                />
              </div>
              <div>
                <label className="text-sm text-gray-400 mb-1 block">Messaggio</label>
                <Textarea
                  placeholder="Scrivi il tuo messaggio qui..."
                  value={contactMessage}
                  onChange={(e) => setContactMessage(e.target.value)}
                  className="bg-black/30 border-white/10 min-h-[120px]"
                  maxLength={2000}
                />
                <p className="text-xs text-gray-500 mt-1 text-right">{contactMessage.length}/2000</p>
              </div>
              <Button 
                onClick={handleContactSubmit}
                disabled={sending || !contactSubject.trim() || !contactMessage.trim()}
                className="w-full bg-purple-500 hover:bg-purple-600"
              >
                {sending ? (
                  <><span className="animate-spin mr-2">⏳</span> Invio in corso...</>
                ) : (
                  <><Send className="w-4 h-4 mr-2" /> Invia Messaggio</>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
      
      <Card className="bg-[#1A1A1A] border-white/10 mb-6">
        <CardContent className="p-6">
          <h2 className="font-['Bebas_Neue'] text-xl mb-3">Tecnologie Utilizzate</h2>
          <div className="flex flex-wrap gap-2">
            {credits.technologies.map((tech, i) => (
              <Badge key={i} className="bg-white/10 text-sm py-1">{tech}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Legal Section */}
      {credits.legal && (
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h2 className="font-['Bebas_Neue'] text-xl mb-4 text-gray-300">Note Legali</h2>
            <div className="space-y-4 text-sm text-gray-400">
              <div className="p-3 bg-yellow-500/10 rounded border border-yellow-500/20">
                <p className="text-yellow-400 font-semibold">{credits.legal.trademark}</p>
              </div>
              <p className="italic">{credits.legal.disclaimer}</p>
              <div className="border-t border-white/10 pt-3">
                <p className="font-semibold text-gray-300 mb-2">Diritti Riservati:</p>
                <ul className="list-disc list-inside space-y-1">
                  {credits.legal.rights.map((right, i) => (
                    <li key={i}>{right}</li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Special Thanks */}
      {credits.special_thanks && (
        <Card className="bg-[#1A1A1A] border-white/10 mb-6">
          <CardContent className="p-6">
            <h2 className="font-['Bebas_Neue'] text-xl mb-3">Ringraziamenti Speciali</h2>
            <div className="flex flex-wrap gap-2">
              {credits.special_thanks.map((thanks, i) => (
                <Badge key={i} variant="outline" className="border-yellow-500/30 text-yellow-400">{thanks}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
      
      <div className="text-center space-y-2 mt-8 pt-6 border-t border-white/10">
        <p className="text-yellow-500 font-semibold">{credits.copyright}</p>
        {credits.legal && (
          <p className="text-gray-500 text-xs">Proprietario: {credits.legal.owner}</p>
        )}
      </div>
    </div>
  );
};

export default CreditsPage;
