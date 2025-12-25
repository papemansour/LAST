import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import apiClient from '../utils/api';
import { Sparkles, Star, PartyPopper, Heart, Rocket } from 'lucide-react';
import { toast } from 'sonner';

const KidsWelcomeLetter = ({ user }) => {
  const [showLetter, setShowLetter] = useState(true);
  const [letterRead, setLetterRead] = useState(false);

  useEffect(() => {
    // Vérifier si la lettre a déjà été lue (stockage local)
    const read = localStorage.getItem(`kkid_welcome_${user?.id}`);
    if (read) {
      setLetterRead(true);
      setShowLetter(false);
    }
  }, [user?.id]);

  const handleClose = () => {
    localStorage.setItem(`kkid_welcome_${user?.id}`, 'true');
    setLetterRead(true);
    setShowLetter(false);
    toast.success('🎉 Super ! Amuse-toi bien !');
  };

  if (!showLetter || letterRead) {
    return null;
  }

  const childName = user?.first_name || 'Super Kid';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <Card className="max-w-2xl w-full bg-gradient-to-br from-pink-100 via-purple-100 to-blue-100 border-4 border-pink-300 shadow-2xl animate-bounce-slow overflow-hidden">
        {/* Confetti decoration */}
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-red-400 via-yellow-400 via-green-400 via-blue-400 to-purple-400"></div>
        
        <CardHeader className="text-center pb-2 relative">
          <div className="flex justify-center gap-2 mb-2">
            <Star className="w-8 h-8 text-yellow-500 animate-spin-slow" />
            <PartyPopper className="w-10 h-10 text-pink-500" />
            <Star className="w-8 h-8 text-yellow-500 animate-spin-slow" />
          </div>
          <CardTitle className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-pink-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
            🎉 BIENVENUE {childName.toUpperCase()} ! 🎉
          </CardTitle>
        </CardHeader>
        
        <CardContent className="text-center space-y-4 px-6 pb-6">
          <div className="bg-white/70 rounded-2xl p-6 space-y-4 border-2 border-pink-200">
            <p className="text-lg md:text-xl text-purple-800 font-medium">
              Coucou petit(e) champion(ne) ! 👋
            </p>
            
            <div className="text-gray-700 space-y-3">
              <p className="flex items-center justify-center gap-2">
                <Rocket className="w-5 h-5 text-blue-500" />
                Tu es prêt(e) pour une super aventure en anglais !
              </p>
              
              <p className="text-2xl py-2">
                🎮 🎨 📚 🎵 🏆
              </p>
              
              <div className="bg-yellow-100 rounded-xl p-4 text-left">
                <p className="font-semibold text-yellow-800 mb-2">🌟 Voici ce qui t'attend :</p>
                <ul className="space-y-2 text-yellow-700">
                  <li className="flex items-center gap-2">
                    <span className="text-xl">🧠</span>
                    <span>Des quiz super amusants pour apprendre en jouant</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-xl">🎥</span>
                    <span>Des vidéos rigolotes avec des chansons</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-xl">🎁</span>
                    <span>Des récompenses et des points à collecter</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <span className="text-xl">👩‍🏫</span>
                    <span>Un(e) professeur(e) gentil(le) pour t'aider</span>
                  </li>
                </ul>
              </div>
              
              <p className="text-purple-600 font-medium pt-2">
                Tu vas devenir un(e) vrai(e) champion(ne) de l'anglais ! 💪
              </p>
            </div>
            
            <div className="flex items-center justify-center gap-1 text-pink-500 text-2xl">
              <Heart className="w-6 h-6 fill-pink-500" />
              <Heart className="w-8 h-8 fill-pink-500" />
              <Heart className="w-6 h-6 fill-pink-500" />
            </div>
            
            <p className="text-gray-600 italic">
              On est trop contents de t'avoir avec nous !
            </p>
            
            <p className="font-bold text-lg text-teal-600">
              L'équipe My KALAMA English Kids 🎓
            </p>
          </div>
          
          <Button 
            onClick={handleClose}
            className="w-full md:w-auto px-8 py-6 text-xl bg-gradient-to-r from-pink-500 via-purple-500 to-blue-500 hover:from-pink-600 hover:via-purple-600 hover:to-blue-600 text-white font-bold rounded-full shadow-lg transform hover:scale-105 transition-all"
          >
            <Sparkles className="w-6 h-6 mr-2" />
            C'est parti ! 🚀
          </Button>
          
          <p className="text-xs text-gray-500">
            (Tes parents recevront aussi un email avec toutes les informations)
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default KidsWelcomeLetter;
