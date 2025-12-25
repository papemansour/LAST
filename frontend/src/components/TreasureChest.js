import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Gift, Star, Lock, Unlock, Trophy, Diamond, Medal } from 'lucide-react';

const TreasureChest = () => {
  const [pointsData, setPointsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPoints();
  }, []);

  const fetchPoints = async () => {
    try {
      const response = await apiClient.get('/student/my-points');
      setPointsData(response.data);
    } catch (error) {
      console.error('Error fetching points:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="animate-pulse">
        <CardHeader>
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
        </CardHeader>
        <CardContent>
          <div className="h-20 bg-gray-200 rounded"></div>
        </CardContent>
      </Card>
    );
  }

  if (!pointsData) return null;

  const { total_points, available_points, rewards, current_discount_eur, current_discount_fcfa, points_to_next_tier } = pointsData;
  const progressToNext = rewards?.next_tier_points 
    ? ((available_points / rewards.next_tier_points) * 100) 
    : 100;

  const getTierIcon = (index) => {
    switch(index) {
      case 0: return <Medal className="w-5 h-5 text-amber-600" />;
      case 1: return <Medal className="w-5 h-5 text-gray-400" />;
      case 2: return <Trophy className="w-5 h-5 text-yellow-500" />;
      case 3: return <Diamond className="w-5 h-5 text-blue-400" />;
      default: return <Star className="w-5 h-5" />;
    }
  };

  return (
    <Card className="bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50 border-2 border-amber-200 shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full shadow-lg">
              <Gift className="w-6 h-6 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl text-amber-800">🎁 Mon Coffre aux Trésors</CardTitle>
              <CardDescription className="text-amber-600">
                Collectez des points pour débloquer des récompenses !
              </CardDescription>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold text-amber-600">{available_points}</p>
            <p className="text-sm text-amber-500">points disponibles</p>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Status des récompenses */}
        <div className={`p-4 rounded-lg ${rewards?.unlocked ? 'bg-green-100 border-2 border-green-300' : 'bg-gray-100 border-2 border-gray-200'}`}>
          <div className="flex items-center gap-2">
            {rewards?.unlocked ? (
              <>
                <Unlock className="w-5 h-5 text-green-600" />
                <span className="font-semibold text-green-700">🎉 Récompenses débloquées !</span>
              </>
            ) : (
              <>
                <Lock className="w-5 h-5 text-gray-500" />
                <span className="font-semibold text-gray-600">
                  Encore {50 - available_points} points pour débloquer les réductions
                </span>
              </>
            )}
          </div>
          
          {rewards?.unlocked && current_discount_eur > 0 && (
            <div className="mt-3 p-3 bg-white rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Votre réduction actuelle :</p>
              <div className="flex gap-4">
                <span className="text-lg font-bold text-green-600">-{current_discount_eur}€</span>
                <span className="text-gray-400">ou</span>
                <span className="text-lg font-bold text-green-600">-{current_discount_fcfa?.toLocaleString()} FCFA</span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Applicable sur votre prochain abonnement
              </p>
            </div>
          )}
        </div>

        {/* Progression vers le prochain palier */}
        {rewards?.next_tier_points && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-amber-700">Progression vers le prochain palier</span>
              <span className="font-semibold text-amber-600">{available_points} / {rewards.next_tier_points}</span>
            </div>
            <Progress value={progressToNext} className="h-3 bg-amber-100" />
            <p className="text-xs text-amber-600 text-center">
              Plus que {points_to_next_tier} points pour atteindre le niveau suivant !
            </p>
          </div>
        )}

        {/* Paliers de récompenses */}
        <div className="mt-4">
          <h4 className="text-sm font-semibold text-amber-800 mb-3">🏆 Paliers de récompenses</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {rewards?.tiers?.map((tier, index) => (
              <div 
                key={index}
                className={`p-3 rounded-lg text-center transition-all ${
                  tier.unlocked 
                    ? 'bg-gradient-to-br from-green-100 to-emerald-100 border-2 border-green-300 shadow-md' 
                    : 'bg-gray-100 border-2 border-gray-200 opacity-60'
                }`}
              >
                <div className="flex justify-center mb-1">
                  {getTierIcon(index)}
                </div>
                <p className="font-bold text-sm">{tier.label}</p>
                <p className="text-xs text-gray-600">{tier.points} pts</p>
                <div className="mt-1 text-xs">
                  {tier.unlocked ? (
                    <span className="text-green-600 font-semibold">-{tier.discount_eur}€</span>
                  ) : (
                    <span className="text-gray-400">🔒</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Comment gagner des points */}
        <div className="mt-4 p-3 bg-amber-100 rounded-lg">
          <h4 className="text-sm font-semibold text-amber-800 mb-2">💡 Comment gagner des points ?</h4>
          <ul className="text-xs text-amber-700 space-y-1">
            <li>✨ +2 points par lien de cours reçu de votre professeur</li>
            <li>✨ +2 points par inscription à un cours groupé</li>
            <li>✨ +5 points par défi hebdomadaire complété</li>
            <li>✨ +10 points par quiz terminé avec 100%</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default TreasureChest;
