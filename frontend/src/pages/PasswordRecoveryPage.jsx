import React, { useState, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { LanguageContext } from '../contexts';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { KeyRound, Mail, RefreshCw } from 'lucide-react';
import axios from 'axios';

const PasswordRecoveryPage = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { language } = useContext(LanguageContext);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${process.env.REACT_APP_BACKEND_URL}/api/auth/recovery/request`, {
        email,
        recovery_type: 'password'
      });
      setSent(true);
      toast.success(language === 'it' ? 'Controlla la tua email!' : 'Check your email!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Errore');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F0F10] flex items-center justify-center p-4">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <Card className="bg-[#1A1A1A] border-white/10">
          <CardHeader className="text-center space-y-3">
            <div className="flex justify-center">
              <KeyRound className="w-12 h-12 text-yellow-500" />
            </div>
            <CardTitle className="font-['Bebas_Neue'] text-2xl">
              {language === 'it' ? 'Recupera Password' : 'Reset Password'}
            </CardTitle>
            <CardDescription className="text-xs">
              {language === 'it' 
                ? 'Inserisci la tua email per ricevere il link di reset'
                : 'Enter your email to receive a reset link'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="text-center space-y-4">
                <div className="w-16 h-16 mx-auto bg-green-500/20 rounded-full flex items-center justify-center">
                  <Mail className="w-8 h-8 text-green-500" />
                </div>
                <p className="text-green-400">
                  {language === 'it' 
                    ? 'Email inviata! Controlla la tua casella di posta.'
                    : 'Email sent! Check your inbox.'}
                </p>
                <Button variant="outline" onClick={() => navigate('/auth')} className="mt-4">
                  {language === 'it' ? 'Torna al Login' : 'Back to Login'}
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-1">
                  <Label className="text-xs">Email</Label>
                  <Input
                    type="email"
                    placeholder="email@example.com"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    className="h-10 bg-black/20 border-white/10"
                    required
                    data-testid="recovery-email-input"
                  />
                </div>
                <Button 
                  type="submit" 
                  className="w-full bg-yellow-500 text-black hover:bg-yellow-400 font-bold"
                  disabled={loading}
                  data-testid="recovery-submit-btn"
                >
                  {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : (language === 'it' ? 'Invia Link' : 'Send Link')}
                </Button>
                <Button variant="ghost" onClick={() => navigate('/auth')} className="w-full text-gray-400">
                  {language === 'it' ? 'Torna al Login' : 'Back to Login'}
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default PasswordRecoveryPage;
