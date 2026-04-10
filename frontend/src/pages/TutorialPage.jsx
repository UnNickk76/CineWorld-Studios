// CineWorld Studio's - Tutorial Page (reads from DB)
import React, { useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, Clapperboard, Users, Trophy, Building, DollarSign, Star, HelpCircle, Ticket, Flame, GraduationCap, ScrollText, Globe, Eye, Play } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { AuthContext } from '../contexts';

const TutorialPage = () => {
  const { api } = useContext(AuthContext);
  const [steps, setSteps] = useState([]);
  const [version, setVersion] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    // Try new tutorial content endpoint first, fallback to old
    api.get('/tutorial/content').then(r => {
      setSteps(r.data.steps || []);
      setVersion(r.data.version || 0);
    }).catch(() => {
      api.get('/game/tutorial').then(r => setSteps(r.data.steps || [])).catch(() => {});
    });
  }, [api]);

  const iconMap = {
    film: Film, clapperboard: Clapperboard, users: Users, trophy: Trophy,
    building: Building, 'dollar-sign': DollarSign, star: Star,
    ticket: Ticket, flame: Flame, 'graduation-cap': GraduationCap, scroll: ScrollText,
    globe: Globe
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="tutorial-page">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2">
          <HelpCircle className="w-7 h-7 text-yellow-500" /> Tutorial
        </h1>
        <div className="flex items-center gap-2">
          {version > 0 && (
            <Badge variant="outline" className="text-[10px] border-white/10 text-gray-500">
              v{version}
            </Badge>
          )}
        </div>
      </div>

      {/* Quick Launch Buttons */}
      <div className="grid grid-cols-2 gap-2 mb-4">
        <Button
          size="sm"
          className="h-9 text-xs bg-cyan-500/10 text-cyan-400 hover:bg-cyan-500/20 border border-cyan-500/20"
          onClick={() => window.dispatchEvent(new Event('velion-tutorial-open'))}
          data-testid="launch-velion-tutorial-btn"
        >
          <Eye className="w-3.5 h-3.5 mr-1.5" /> Tutorial Velion
        </Button>
        <Button
          size="sm"
          className="h-9 text-xs bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border border-amber-500/20"
          onClick={() => window.dispatchEvent(new Event('pipeline-tutorial-open'))}
          data-testid="launch-pipeline-tutorial-btn"
        >
          <Play className="w-3.5 h-3.5 mr-1.5" /> Pipeline Film
        </Button>
      </div>
      
      <div className="grid gap-3">
        {steps.map((step, index) => {
          const IconComp = iconMap[step.icon] || Star;
          const title = step.title || `Step ${step.id || index + 1}`;
          const desc = step.description || step.text || '';
          return (
            <Card 
              key={step.id || index}
              className={`bg-[#1A1A1A] border-white/10 cursor-pointer transition-all ${currentStep === index ? 'ring-2 ring-yellow-500/60' : ''}`}
              onClick={() => setCurrentStep(index)}
              data-testid={`tutorial-step-${index}`}
            >
              <CardContent className="p-4 flex items-start gap-3">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${currentStep === index ? 'bg-yellow-500 text-black' : 'bg-white/10'}`}>
                  <IconComp className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-sm">{step.id ? `${step.id}. ` : ''}{title}</h3>
                  <p className="text-gray-400 text-xs mt-1">{desc}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      <div className="mt-6 text-center">
        <Button onClick={() => navigate('/dashboard')} className="bg-yellow-500 text-black hover:bg-yellow-400" data-testid="tutorial-start-btn">
          Inizia a Giocare!
        </Button>
      </div>
    </div>
  );
};

export default TutorialPage;
