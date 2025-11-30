import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { TrendingUp, Calendar, Award, Flame, ExternalLink, CheckCircle2 } from 'lucide-react';

const StudentProgression = () => {
  const [progression, setProgression] = useState(null);
  const [meetLinks, setMeetLinks] = useState([]);
  const [badges, setBadges] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProgression();
    fetchMeetLinks();
    fetchBadges();
  }, []);

  const fetchProgression = async () => {
    try {
      const res = await apiClient.get('/student/my-progression');
      setProgression(res.data);
    } catch (error) {
      console.error('Error fetching progression:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMeetLinks = async () => {
    try {
      const res = await apiClient.get('/student/my-meet-links');
      setMeetLinks(res.data);
    } catch (error) {
      console.error('Error fetching meet links:', error);
    }
  };

  const fetchBadges = async () => {
    try {
      const res = await apiClient.get('/student/my-badges');
      setBadges(res.data);
    } catch (error) {
      console.error('Error fetching badges:', error);
    }
  };

  const handleMarkAttended = async (meetId) => {
    try {
      await apiClient.put(`/student/mark-meet-attended/${meetId}`);
      toast.success('Cours marqué comme suivi !');
      fetchProgression();
      fetchMeetLinks();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
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

  return (
    <div className="space-y-6">
      {/* Progression Statistics */}
      <div className="grid md:grid-cols-3 gap-6">
        {/* Global Progression */}
        <Card className="border-teal-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Progression Globale</CardTitle>
              <TrendingUp className="w-5 h-5 text-teal-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-teal-600">
                {progression?.percentage || 0}%
              </div>
              <Progress value={progression?.percentage || 0} className="h-2" />
              <p className="text-xs text-gray-500">
                {progression?.courses_completed || 0} cours sur {progression?.total_courses || 0}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Consecutive Days */}
        <Card className="border-orange-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Jours Consécutifs</CardTitle>
              <Flame className="w-5 h-5 text-orange-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-orange-600">
                {progression?.consecutive_days || 0}
              </div>
              <p className="text-xs text-gray-500">
                {progression?.consecutive_days > 0 
                  ? `🔥 ${progression?.consecutive_days} jour${progression?.consecutive_days > 1 ? 's' : ''} d'affilée !`
                  : 'Assistez à un cours pour commencer'}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Courses Completed */}
        <Card className="border-blue-200">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium">Cours Suivis</CardTitle>
              <Award className="w-5 h-5 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="text-3xl font-bold text-blue-600">
                {progression?.courses_completed || 0}
              </div>
              <p className="text-xs text-gray-500">
                {progression?.total_courses > 0
                  ? `${progression?.courses_completed} complété${progression?.courses_completed > 1 ? 's' : ''}`
                  : 'Aucun cours encore'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Meet Links List */}
      <Card>
        <CardHeader className="bg-teal-50">
          <CardTitle className="text-teal-800">📅 Mes Cours Programmés</CardTitle>
          <CardDescription>
            Liens Google Meet envoyés par votre professeur
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {meetLinks.length === 0 ? (
            <div className="text-center py-12">
              <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucun cours programmé</p>
              <p className="text-sm text-gray-400 mt-2">
                Votre professeur vous enverra des liens de cours ici
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {meetLinks.map((meet) => (
                <div
                  key={meet.id}
                  className={`p-4 border rounded-lg ${
                    meet.attended 
                      ? 'bg-green-50 border-green-200' 
                      : new Date(meet.scheduled_date) < new Date()
                      ? 'bg-gray-50 border-gray-200'
                      : 'bg-blue-50 border-blue-200'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-gray-900">{meet.title}</h3>
                        {meet.attended && (
                          <span className="px-2 py-0.5 bg-green-600 text-white text-xs font-semibold rounded-full flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            Suivi
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          {new Date(meet.scheduled_date).toLocaleDateString('fr-FR', {
                            day: '2-digit',
                            month: 'long',
                            year: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 flex-shrink-0">
                      <a
                        href={meet.meet_link}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <Button
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          <ExternalLink className="w-4 h-4 mr-1" />
                          Rejoindre
                        </Button>
                      </a>
                      
                      {!meet.attended && new Date(meet.scheduled_date) < new Date() && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkAttended(meet.id)}
                          className="border-green-600 text-green-600 hover:bg-green-50"
                        >
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          J'ai assisté
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Badges Section */}
      <Card className="border-purple-200">
        <CardHeader className="bg-purple-50">
          <CardTitle className="text-purple-800">🏆 Collection de Badges</CardTitle>
          <CardDescription>
            Gagnez des badges en progressant dans vos cours
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {badges.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Award className="w-12 h-12 mx-auto mb-2 text-gray-400" />
              <p className="text-sm">Chargement des badges...</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {badges.map((badge) => (
                <div
                  key={badge.id}
                  className={`p-6 rounded-xl border-2 text-center transition-all ${
                    badge.earned
                      ? 'bg-gradient-to-br from-yellow-50 to-orange-50 border-yellow-300 shadow-lg'
                      : 'bg-gray-50 border-gray-200 opacity-60'
                  }`}
                >
                  <div className="text-5xl mb-3">{badge.icon}</div>
                  <h3 className={`font-bold mb-1 ${badge.earned ? 'text-orange-700' : 'text-gray-500'}`}>
                    {badge.name}
                  </h3>
                  <p className="text-xs text-gray-600 mb-2">{badge.description}</p>
                  {badge.earned ? (
                    <div className="mt-3">
                      <span className="inline-block px-3 py-1 bg-green-600 text-white text-xs font-semibold rounded-full">
                        ✓ Obtenu
                      </span>
                      {badge.awarded_at && (
                        <p className="text-xs text-gray-500 mt-2">
                          {new Date(badge.awarded_at).toLocaleDateString('fr-FR')}
                        </p>
                      )}
                    </div>
                  ) : (
                    <div className="mt-3">
                      <span className="inline-block px-3 py-1 bg-gray-300 text-gray-600 text-xs font-semibold rounded-full">
                        🔒 Verrouillé
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentProgression;
