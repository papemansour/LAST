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
      {/* Points Treasure Chest */}
      <Card className={`border-2 ${isFullChest ? 'border-yellow-400 bg-gradient-to-br from-yellow-50 to-orange-50' : 'border-gray-300'}`}>
        <CardHeader className={isFullChest ? 'bg-gradient-to-r from-yellow-100 to-orange-100' : 'bg-gray-50'}>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className={isFullChest ? 'text-yellow-800' : 'text-gray-800'}>
                💰 Mon Coffre de Points XP
              </CardTitle>
              <CardDescription>
                Complétez les défis pour gagner des points et débloquer des réductions
              </CardDescription>
            </div>
            <div className="text-right">
              <div className={`text-4xl font-bold ${isFullChest ? 'text-yellow-600' : 'text-gray-700'}`}>
                {points?.available_points || 0}
              </div>
              <p className="text-xs text-gray-500">points disponibles</p>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Progress Bar */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Progression vers 50 points
                </span>
                <span className="text-sm font-bold text-teal-600">
                  {points?.available_points || 0} / 50
                </span>
              </div>
              <Progress 
                value={pointsPercentage} 
                className={`h-3 ${isFullChest ? 'bg-yellow-200' : ''}`}
              />
            </div>

            {/* Discount Info */}
            <div className={`p-4 rounded-lg border-2 ${
              isFullChest 
                ? 'bg-green-50 border-green-300' 
                : 'bg-gray-50 border-gray-200'
            }`}>
              <div className="flex items-center gap-3">
                <Coins className={`w-8 h-8 ${isFullChest ? 'text-yellow-600' : 'text-gray-400'}`} />
                <div className="flex-1">
                  <p className={`font-semibold ${isFullChest ? 'text-green-700' : 'text-gray-600'}`}>
                    {isFullChest ? '✅ Réduction disponible !' : '🔒 Réduction verrouillée'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {isFullChest 
                      ? `Vous pouvez obtenir ${points.euro_discount}€ ou ${points.fcfa_discount} FCFA de réduction`
                      : `Il vous reste ${50 - (points?.available_points || 0)} points pour débloquer une réduction`
                    }
                  </p>
                </div>
              </div>
            </div>

            {/* Conversion Info */}
            <div className="grid md:grid-cols-2 gap-3">
              <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-xs text-blue-600 font-semibold mb-1">💶 Réduction en Euros</p>
                <p className="text-2xl font-bold text-blue-700">{points?.euro_discount || 0}€</p>
                <p className="text-xs text-gray-500 mt-1">50 points = 1€</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <p className="text-xs text-green-600 font-semibold mb-1">💵 Réduction en FCFA</p>
                <p className="text-2xl font-bold text-green-700">{points?.fcfa_discount || 0} FCFA</p>
                <p className="text-xs text-gray-500 mt-1">50 points = 100 FCFA</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

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
