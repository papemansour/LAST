import React from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Gift, Star, Moon, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const RamadanPromoBanner = ({ showButton = true, compact = false }) => {
  const navigate = useNavigate();
  
  // Check if Ramadan promo is active (Feb 17 - Mar 20, 2026)
  const currentDate = new Date();
  const isRamadanPromo = currentDate >= new Date('2026-02-17') && currentDate <= new Date('2026-03-20');
  
  // Calculate days remaining
  const promoEndDate = new Date('2026-03-20');
  const daysRemaining = Math.max(0, Math.ceil((promoEndDate - currentDate) / (1000 * 60 * 60 * 24)));
  
  if (!isRamadanPromo) return null;
  
  if (compact) {
    return (
      <div className="bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 text-white p-3 rounded-lg mb-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🌙</span>
            <div>
              <p className="font-bold text-sm">Promo Ramadan -10%</p>
              <p className="text-xs opacity-90">Code: RAMADAN2026</p>
            </div>
          </div>
          <span className="text-lg">⭐</span>
        </div>
      </div>
    );
  }
  
  return (
    <Card className="border-2 border-emerald-300 bg-gradient-to-br from-emerald-50 via-teal-50 to-amber-50 mb-6 overflow-hidden relative">
      {/* Decorative elements */}
      <div className="absolute top-2 right-4 text-4xl opacity-30 animate-pulse">🌙</div>
      <div className="absolute bottom-2 left-4 text-3xl opacity-30 animate-pulse" style={{ animationDelay: '0.5s' }}>⭐</div>
      <div className="absolute top-1/2 right-1/4 text-2xl opacity-20">✨</div>
      
      <CardContent className="p-6 relative z-10">
        <div className="flex flex-col md:flex-row items-center gap-6">
          {/* Icon */}
          <div className="w-24 h-24 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg relative">
            <Moon className="w-12 h-12 text-white" />
            <div className="absolute -top-1 -right-1 w-8 h-8 bg-amber-400 rounded-full flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
          </div>
          
          {/* Content */}
          <div className="flex-1 text-center md:text-left">
            <div className="flex items-center gap-2 justify-center md:justify-start mb-2">
              <h3 className="text-2xl font-bold text-emerald-800">🌙 Ramadan Mubarak ! 🌙</h3>
            </div>
            
            <p className="text-emerald-700 text-lg mb-1">
              رمضان مبارك - Que ce mois sacré soit rempli de bénédictions
            </p>
            
            <div className="bg-white/60 rounded-lg p-3 mt-3 border border-emerald-200">
              <div className="flex items-center gap-3 justify-center md:justify-start">
                <Gift className="w-6 h-6 text-emerald-600" />
                <div>
                  <p className="text-xl font-bold text-emerald-800">PROMO RAMADAN : -10% sur tous les packs !</p>
                  <p className="text-sm text-emerald-600">
                    Code promo : <span className="font-mono bg-emerald-100 px-2 py-0.5 rounded">RAMADAN2026</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">(Hors Pack K-Kid)</p>
                </div>
              </div>
            </div>
            
            <p className="text-sm text-amber-700 mt-2 flex items-center gap-1 justify-center md:justify-start">
              <Star className="w-4 h-4" />
              Plus que {daysRemaining} jours pour profiter de cette offre !
            </p>
          </div>
          
          {/* CTA */}
          {showButton && (
            <div className="flex flex-col gap-2">
              <Button 
                onClick={() => navigate('/')}
                className="bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white px-8 py-6 text-lg shadow-lg"
              >
                <Gift className="w-5 h-5 mr-2" />
                Profiter de -10%
              </Button>
              <p className="text-xs text-emerald-600 text-center">
                Valable jusqu&apos;au 20 mars 2026
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default RamadanPromoBanner;
