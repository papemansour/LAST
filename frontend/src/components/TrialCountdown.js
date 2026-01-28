import React, { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Clock, Gift, Calendar, Star, AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const TrialCountdown = ({ registrationDate }) => {
  const navigate = useNavigate();
  const [daysRemaining, setDaysRemaining] = useState(7);
  const [hoursRemaining, setHoursRemaining] = useState(0);
  
  useEffect(() => {
    const calculateRemaining = () => {
      const regDate = registrationDate ? new Date(registrationDate) : new Date();
      const trialEndDate = new Date(regDate);
      trialEndDate.setDate(trialEndDate.getDate() + 7); // 7 days trial
      
      const now = new Date();
      const diff = trialEndDate - now;
      
      if (diff <= 0) {
        setDaysRemaining(0);
        setHoursRemaining(0);
        return;
      }
      
      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      
      setDaysRemaining(days);
      setHoursRemaining(hours);
    };
    
    calculateRemaining();
    const interval = setInterval(calculateRemaining, 1000 * 60); // Update every minute
    
    return () => clearInterval(interval);
  }, [registrationDate]);

  const getUrgencyColor = () => {
    if (daysRemaining <= 1) return 'from-red-500 to-orange-500';
    if (daysRemaining <= 3) return 'from-orange-500 to-yellow-500';
    return 'from-teal-500 to-emerald-500';
  };

  const getUrgencyBg = () => {
    if (daysRemaining <= 1) return 'bg-red-50 border-red-200';
    if (daysRemaining <= 3) return 'bg-orange-50 border-orange-200';
    return 'bg-teal-50 border-teal-200';
  };

  if (daysRemaining <= 0 && hoursRemaining <= 0) {
    return (
      <Card className="border-2 border-red-300 bg-red-50 mb-6">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center">
              <AlertTriangle className="w-8 h-8 text-red-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-bold text-red-800">Votre essai gratuit est terminé</h3>
              <p className="text-sm text-red-600 mt-1">
                Passez à un abonnement pour continuer à apprendre l&apos;anglais avec nous !
              </p>
            </div>
            <Button 
              onClick={() => navigate('/')}
              className="bg-red-600 hover:bg-red-700"
            >
              Voir les offres
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`border-2 ${getUrgencyBg()} mb-6`}>
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row items-center gap-4">
          {/* Timer icon */}
          <div className={`w-20 h-20 rounded-full bg-gradient-to-br ${getUrgencyColor()} flex items-center justify-center shadow-lg`}>
            <Clock className="w-10 h-10 text-white" />
          </div>
          
          {/* Countdown display */}
          <div className="flex-1 text-center md:text-left">
            <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2 justify-center md:justify-start">
              <Gift className="w-5 h-5 text-teal-600" />
              🎁 Votre Essai Gratuit
            </h3>
            
            <div className="flex items-center gap-4 mt-3 justify-center md:justify-start">
              {/* Days */}
              <div className="text-center">
                <div className={`text-4xl font-bold bg-gradient-to-br ${getUrgencyColor()} bg-clip-text text-transparent`}>
                  {daysRemaining}
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  {daysRemaining === 1 ? 'Jour' : 'Jours'}
                </div>
              </div>
              
              <div className="text-2xl text-gray-400">:</div>
              
              {/* Hours */}
              <div className="text-center">
                <div className={`text-4xl font-bold bg-gradient-to-br ${getUrgencyColor()} bg-clip-text text-transparent`}>
                  {hoursRemaining}
                </div>
                <div className="text-xs text-gray-500 uppercase tracking-wide">
                  {hoursRemaining === 1 ? 'Heure' : 'Heures'}
                </div>
              </div>
            </div>
            
            <p className="text-sm text-gray-600 mt-2">
              {daysRemaining <= 1 
                ? '⚠️ Dernière chance ! Votre essai se termine bientôt.'
                : daysRemaining <= 3
                  ? '⏰ Plus que quelques jours pour profiter de votre essai gratuit !'
                  : '✨ Profitez de votre essai gratuit pour découvrir nos cours.'}
            </p>
          </div>
          
          {/* CTA Button */}
          <div className="flex flex-col gap-2">
            <Button 
              onClick={() => navigate('/')}
              className={`bg-gradient-to-r ${getUrgencyColor()} hover:opacity-90 text-white px-6`}
            >
              <Star className="w-4 h-4 mr-2" />
              Passer au Premium
            </Button>
            {daysRemaining > 0 && (
              <p className="text-xs text-gray-500 text-center">
                -10% avec RAMADAN2026
              </p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TrialCountdown;
