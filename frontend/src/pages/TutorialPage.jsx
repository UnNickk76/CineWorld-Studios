// CineWorld Studio's - Tutorial Page
// Extracted from App.js

import React, { useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Film, Clapperboard, Users, Trophy, Building, DollarSign, Star, HelpCircle, Ticket, Flame, GraduationCap, ScrollText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { AuthContext } from '../contexts';

const TutorialPage = () => {
  const { api } = useContext(AuthContext);
  const [tutorial, setTutorial] = useState({ steps: [] });
  const [currentStep, setCurrentStep] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/game/tutorial').then(r => setTutorial(r.data)).catch(console.error);
  }, [api]);

  const iconMap = {
    film: Film, clapperboard: Clapperboard, users: Users, trophy: Trophy,
    building: Building, 'dollar-sign': DollarSign, star: Star,
    ticket: Ticket, flame: Flame, 'graduation-cap': GraduationCap, scroll: ScrollText
  };

  return (
    <div className="pt-16 pb-20 px-3 max-w-4xl mx-auto" data-testid="tutorial-page">
      <h1 className="font-['Bebas_Neue'] text-3xl flex items-center gap-2 mb-6">
        <HelpCircle className="w-7 h-7 text-yellow-500" /> Tutorial
      </h1>
      
      <div className="grid gap-4">
        {tutorial.steps.map((step, index) => {
          const IconComp = iconMap[step.icon] || Star;
          return (
            <Card 
              key={step.id}
              className={`bg-[#1A1A1A] border-white/10 cursor-pointer transition-all ${currentStep === index ? 'ring-2 ring-yellow-500' : ''}`}
              onClick={() => setCurrentStep(index)}
            >
              <CardContent className="p-4 flex items-start gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${currentStep === index ? 'bg-yellow-500 text-black' : 'bg-white/10'}`}>
                  <IconComp className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{step.id}. {step.title}</h3>
                  <p className="text-gray-400 text-sm mt-1">{step.description}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
      
      <div className="mt-6 text-center">
        <Button onClick={() => navigate('/dashboard')} className="bg-yellow-500 text-black">
          Inizia a Giocare!
        </Button>
      </div>
    </div>
  );
};

export default TutorialPage;
