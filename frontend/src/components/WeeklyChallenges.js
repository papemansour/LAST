import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Target, Trophy, Coins, CheckCircle2, Lock } from 'lucide-react';

const WeeklyChallenges = () => {
  const [challenges, setChallenges] = useState([]);
  const [points, setPoints] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchChallenges();
    fetchPoints();
  }, []);

  const fetchChallenges = async () => {
    try {
      const res = await apiClient.get('/student/my-challenge-progress');
      setChallenges(res.data);
    } catch (error) {
      console.error('Error fetching challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPoints = async () => {
    try {
      const res = await apiClient.get('/student/my-points');
      setPoints(res.data);
    } catch (error) {
      console.error('Error fetching points:', error);
    }
  };

  const handleCompleteChallenge = async (challengeId) => {
    try {
      const res = await apiClient.post(`/student/complete-challenge/${challengeId}`);
      toast.success(`🎉 ${res.data.points_earned} points gagnés !`);
      fetchChallenges();
      fetchPoints();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur');
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12">
          <p className="text-center text-gray-500">Chargement...</p>
        </CardContent>
      </Card>
    );
  }

  const pointsPercentage = points ? Math.min((points.available_points / 50) * 100, 100) : 0;
  const isFullChest = points && points.available_points >= 50;

  return (
    <div className="space-y-6">
      {/* Points Treasure Chest - Nouveau Design */}
      <div className="relative">
        <Card className={`border-3 overflow-hidden ${
          isFullChest 
            ? 'border-yellow-400 shadow-2xl shadow-yellow-300/50 animate-pulse' 
            : 'border-purple-300 shadow-xl'
        }`}>
          {/* Header avec dégradé */}
          <div className={`relative ${
            isFullChest 
              ? 'bg-gradient-to-br from-yellow-400 via-orange-400 to-yellow-500' 
              : 'bg-gradient-to-br from-purple-600 via-purple-500 to-pink-500'
          } pt-8 pb-20`}>
            {/* Étoiles décoratives */}
            <div className="absolute top-2 left-4 text-yellow-200 opacity-70">✨</div>
            <div className="absolute top-4 right-8 text-yellow-200 opacity-70">⭐</div>
            <div className="absolute top-8 left-1/3 text-yellow-200 opacity-70">💫</div>
            
            <div className="text-center relative z-10">
              {/* Icône coffre animé */}
              <div className={`text-8xl mb-4 ${isFullChest ? 'animate-bounce' : ''}`}>
                {isFullChest ? '💎' : '🎁'}
              </div>
              
              <h2 className="text-3xl font-bold text-white mb-2 drop-shadow-lg">
                Mon Coffre aux Trésors
              </h2>
              <p className="text-white/90 text-sm">
                {isFullChest 
                  ? '🎉 Félicitations ! Votre coffre est plein !' 
                  : 'Collecte des points pour débloquer des récompenses'}
              </p>
            </div>
          </div>

          {/* Contenu principal avec overlap */}
          <CardContent className="relative -mt-12 px-6 pb-6">
            {/* Carte de points flottante */}
            <div className={`relative bg-white rounded-2xl shadow-2xl p-6 mb-6 border-2 ${
              isFullChest ? 'border-yellow-400' : 'border-purple-200'
            }`}>
              {/* Badge de points */}
              <div className="flex items-center justify-center mb-4">
                <div className={`relative inline-block ${isFullChest ? 'animate-pulse' : ''}`}>
                  <div className={`text-6xl font-black ${
                    isFullChest 
                      ? 'text-transparent bg-clip-text bg-gradient-to-r from-yellow-500 to-orange-500' 
                      : 'text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-pink-500'
                  }`}>
                    {points?.available_points || 0}
                  </div>
                  <div className="absolute -top-2 -right-8">
                    <Coins className={`w-10 h-10 ${isFullChest ? 'text-yellow-500' : 'text-purple-400'}`} />
                  </div>
                </div>
              </div>
              <p className="text-center text-gray-600 font-medium mb-4">Points XP disponibles</p>

              {/* Barre de progression stylée */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-semibold text-gray-700">🎯 Objectif : 50 points</span>
                  <span className={`font-bold ${isFullChest ? 'text-green-600' : 'text-purple-600'}`}>
                    {points?.available_points || 0} / 50
                  </span>
                </div>
                <div className="relative h-4 bg-gray-200 rounded-full overflow-hidden shadow-inner">
                  <div 
                    className={`h-full transition-all duration-1000 ease-out ${
                      isFullChest 
                        ? 'bg-gradient-to-r from-yellow-400 via-orange-400 to-yellow-500' 
                        : 'bg-gradient-to-r from-purple-500 to-pink-500'
                    }`}
                    style={{ width: `${pointsPercentage}%` }}
                  >
                    {pointsPercentage > 10 && (
                      <div className="h-full flex items-center justify-end pr-2">
                        <span className="text-white text-xs font-bold drop-shadow">
                          {Math.round(pointsPercentage)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Statut du coffre */}
              <div className={`mt-6 p-4 rounded-xl border-2 ${
                isFullChest 
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300' 
                  : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-start gap-3">
                  {isFullChest ? (
                    <CheckCircle2 className="w-8 h-8 text-green-600 flex-shrink-0 mt-1" />
                  ) : (
                    <Lock className="w-8 h-8 text-gray-400 flex-shrink-0 mt-1" />
                  )}
                  <div className="flex-1">
                    <p className={`font-bold text-lg mb-1 ${
                      isFullChest ? 'text-green-700' : 'text-gray-700'
                    }`}>
                      {isFullChest ? '🎊 Récompense Débloquée !' : '🔐 Récompense Verrouillée'}
                    </p>
                    <p className="text-sm text-gray-600">
                      {isFullChest 
                        ? `Bravo ! Vous avez débloqué ${points.euro_discount}€ ou ${points.fcfa_discount} FCFA de réduction`
                        : `Plus que ${50 - (points?.available_points || 0)} points pour débloquer votre première réduction !`
                      }
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Cartes de réduction */}
            <div className="grid md:grid-cols-2 gap-4">
              {/* Réduction Euros */}
              <div className="relative group">
                <div className={`p-5 rounded-xl border-2 transition-all duration-300 ${
                  isFullChest
                    ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-300 hover:shadow-lg hover:-translate-y-1'
                    : 'bg-gray-50 border-gray-200 opacity-60'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-3xl">💶</div>
                    {isFullChest && (
                      <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
                        ACTIF
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-blue-600 font-semibold mb-1">Réduction en Euros</p>
                  <p className="text-4xl font-black text-blue-700 mb-2">
                    {points?.euro_discount || 0}€
                  </p>
                  <p className="text-xs text-gray-500">
                    💡 50 points = 1€ de réduction
                  </p>
                </div>
              </div>

              {/* Réduction FCFA */}
              <div className="relative group">
                <div className={`p-5 rounded-xl border-2 transition-all duration-300 ${
                  isFullChest
                    ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300 hover:shadow-lg hover:-translate-y-1'
                    : 'bg-gray-50 border-gray-200 opacity-60'
                }`}>
                  <div className="flex items-center justify-between mb-3">
                    <div className="text-3xl">💵</div>
                    {isFullChest && (
                      <span className="px-2 py-1 bg-green-500 text-white text-xs font-bold rounded-full">
                        ACTIF
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-green-600 font-semibold mb-1">Réduction en FCFA</p>
                  <p className="text-4xl font-black text-green-700 mb-2">
                    {points?.fcfa_discount || 0}
                  </p>
                  <p className="text-xs text-gray-500">
                    💡 50 points = 100 FCFA de réduction
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Weekly Challenges */}
      <Card>
        <CardHeader className="bg-purple-50">
          <CardTitle className="text-purple-800">🎯 Défi de la Semaine</CardTitle>
          <CardDescription>
            Complétez les défis pour gagner des points XP
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {challenges.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucun défi disponible cette semaine</p>
            </div>
          ) : (
            <div className="space-y-4">
              {challenges.map((challenge) => (
                <div
                  key={challenge.id}
                  className={`p-5 rounded-xl border-2 ${
                    challenge.progress?.completed
                      ? 'bg-green-50 border-green-300'
                      : 'bg-white border-purple-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-bold text-gray-900">{challenge.title}</h3>
                        {challenge.progress?.completed && (
                          <span className="px-2 py-0.5 bg-green-600 text-white text-xs font-semibold rounded-full flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            Complété
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{challenge.description}</p>
                      
                      <div className="flex items-center gap-4 text-sm">
                        <span className="flex items-center gap-1 text-purple-600 font-semibold">
                          <Trophy className="w-4 h-4" />
                          +{challenge.points_reward} points
                        </span>
                        <span className="text-gray-500">
                          Objectif : {challenge.target_count} action{challenge.target_count > 1 ? 's' : ''}
                        </span>
                      </div>
                    </div>
                    
                    {challenge.progress?.completed ? (
                      <div className="flex-shrink-0 text-green-600">
                        <CheckCircle2 className="w-10 h-10" />
                      </div>
                    ) : (
                      <Button
                        size="sm"
                        onClick={() => handleCompleteChallenge(challenge.id)}
                        className="flex-shrink-0 bg-purple-600 hover:bg-purple-700"
                      >
                        Valider
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="border-blue-200">
        <CardHeader className="bg-blue-50">
          <CardTitle className="text-blue-800">ℹ️ Comment ça marche ?</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-2 text-sm text-gray-700">
            <p><strong>1.</strong> Complétez les défis hebdomadaires pour gagner des points XP</p>
            <p><strong>2.</strong> Accumulez 50 points pour débloquer une réduction de 1€ (ou 100 FCFA)</p>
            <p><strong>3.</strong> Les réductions peuvent être utilisées lors de votre prochain paiement</p>
            <p className="mt-4 text-xs text-gray-500">
              💡 Astuce : Plus vous participez, plus vous gagnez de réductions !
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default WeeklyChallenges;
