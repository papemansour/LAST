import React, { useState } from 'react';
import { Button } from './ui/button';
import { X, Sparkles } from 'lucide-react';
import WelcomeLetter from './WelcomeLetter';
import apiClient from '../utils/api';

const GiftWelcomeLetter = ({ user, onClose }) => {
  const [isOpening, setIsOpening] = useState(false);
  const [isOpened, setIsOpened] = useState(false);
  const [showLetter, setShowLetter] = useState(false);

  const handleOpenGift = async () => {
    setIsOpening(true);
    
    // Animation d'ouverture du cadeau
    setTimeout(() => {
      setIsOpened(true);
    }, 500);
    
    // Apparition de la lettre
    setTimeout(() => {
      setShowLetter(true);
    }, 1200);
    
    // Marquer comme ouvert dans le backend
    try {
      await apiClient.post('/auth/mark-welcome-letter-opened');
    } catch (error) {
      console.error('Error marking welcome letter as opened:', error);
    }
  };

  const handleClose = () => {
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      {/* Confettis décoratifs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(20)].map((_, i) => (
          <div
            key={i}
            className="absolute animate-fall"
            style={{
              left: `${Math.random() * 100}%`,
              top: `-20px`,
              animationDelay: `${Math.random() * 2}s`,
              animationDuration: `${3 + Math.random() * 2}s`
            }}
          >
            {['✨', '🎉', '🎊', '⭐', '💫'][Math.floor(Math.random() * 5)]}
          </div>
        ))}
      </div>

      <div className="relative max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {!showLetter ? (
          // Cadeau animé
          <div className="flex flex-col items-center justify-center py-12">
            <div className={`relative transition-all duration-1000 ${
              isOpening ? 'scale-110' : 'scale-100'
            }`}>
              {/* Cadeau */}
              <div className={`relative ${isOpened ? 'animate-bounce-once' : ''}`}>
                {/* Couvercle du cadeau */}
                <div className={`transition-all duration-700 ${
                  isOpened 
                    ? 'transform -translate-y-32 rotate-12 opacity-0' 
                    : ''
                }`}>
                  <div className="w-48 h-24 bg-gradient-to-br from-red-500 to-red-600 rounded-t-3xl relative shadow-2xl">
                    {/* Ruban du couvercle */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-16 h-full bg-gradient-to-r from-yellow-400 to-yellow-500"></div>
                    {/* Noeud */}
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 w-20 h-16">
                      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-12 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full"></div>
                      <div className="absolute top-4 left-0 w-8 h-10 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full transform -rotate-45"></div>
                      <div className="absolute top-4 right-0 w-8 h-10 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full transform rotate-45"></div>
                    </div>
                  </div>
                </div>

                {/* Corps du cadeau */}
                <div className={`w-48 h-48 bg-gradient-to-br from-red-600 to-red-700 rounded-b-3xl shadow-2xl relative overflow-hidden ${
                  isOpened ? 'animate-shake' : ''
                }`}>
                  {/* Ruban vertical */}
                  <div className="absolute top-0 left-1/2 -translate-x-1/2 w-16 h-full bg-gradient-to-r from-yellow-400 to-yellow-500"></div>
                  
                  {/* Paillettes */}
                  {isOpening && (
                    <div className="absolute inset-0 flex items-center justify-center">
                      {[...Array(8)].map((_, i) => (
                        <Sparkles
                          key={i}
                          className={`absolute text-yellow-300 animate-ping`}
                          style={{
                            top: `${Math.random() * 100}%`,
                            left: `${Math.random() * 100}%`,
                            animationDelay: `${i * 0.1}s`
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Ombre du cadeau */}
              <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-40 h-8 bg-black/30 rounded-full blur-xl"></div>
            </div>

            {/* Texte et bouton */}
            <div className="mt-16 text-center space-y-6">
              <div className="space-y-2">
                <h2 className="text-4xl font-bold text-white drop-shadow-lg">
                  🎁 Bienvenue {user?.first_name} !
                </h2>
                <p className="text-xl text-white/90">
                  Vous avez un cadeau de bienvenue
                </p>
              </div>

              {!isOpening && (
                <Button
                  onClick={handleOpenGift}
                  size="lg"
                  className="bg-gradient-to-r from-yellow-400 to-orange-500 hover:from-yellow-500 hover:to-orange-600 text-white font-bold text-xl px-12 py-6 rounded-full shadow-2xl transform hover:scale-105 transition-all duration-300 animate-pulse"
                >
                  👆 Toucher pour ouvrir
                </Button>
              )}

              {isOpening && !isOpened && (
                <div className="text-2xl text-white font-semibold animate-pulse">
                  Ouverture en cours...
                </div>
              )}

              {isOpened && !showLetter && (
                <div className="text-2xl text-white font-semibold animate-bounce">
                  ✨ Surprise ! ✨
                </div>
              )}
            </div>
          </div>
        ) : (
          // Lettre de bienvenue avec animation
          <div className="bg-white rounded-2xl shadow-2xl overflow-hidden animate-slideUp">
            <div className="relative">
              <Button
                onClick={handleClose}
                variant="ghost"
                size="sm"
                className="absolute top-4 right-4 z-10 hover:bg-gray-100"
              >
                <X className="w-5 h-5" />
              </Button>
              <div className="overflow-y-auto max-h-[80vh]">
                <WelcomeLetter userRole={user?.role} />
              </div>
            </div>
          </div>
        )}
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes fall {
          to {
            transform: translateY(100vh) rotate(360deg);
            opacity: 0;
          }
        }

        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(100px) scale(0.9);
          }
          to {
            opacity: 1;
            transform: translateY(0) scale(1);
          }
        }

        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px) rotate(-2deg); }
          75% { transform: translateX(5px) rotate(2deg); }
        }

        @keyframes bounce-once {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-20px); }
        }

        .animate-fadeIn {
          animation: fadeIn 0.3s ease-out;
        }

        .animate-fall {
          animation: fall linear forwards;
        }

        .animate-slideUp {
          animation: slideUp 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
        }

        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }

        .animate-bounce-once {
          animation: bounce-once 0.6s ease-out;
        }
      `}</style>
    </div>
  );
};

export default GiftWelcomeLetter;
