import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { 
  Video, Calendar, ExternalLink, CheckCircle2, Clock, 
  User, Bell, RefreshCw, Link2
} from 'lucide-react';

const StudentCourseLinks = () => {
  const [meetLinks, setMeetLinks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMeetLinks();
  }, []);

  const fetchMeetLinks = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/student/my-meet-links');
      setMeetLinks(res.data);
    } catch (error) {
      console.error('Error fetching meet links:', error);
      toast.error('Erreur de chargement des liens');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAttended = async (meetId) => {
    try {
      await apiClient.put(`/student/mark-meet-attended/${meetId}`);
      toast.success('Cours marqué comme suivi ! 🎉');
      fetchMeetLinks();
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleJoinCourse = (link) => {
    // Open link in new tab
    window.open(link, '_blank', 'noopener,noreferrer');
  };

  const isUpcoming = (dateStr) => {
    return new Date(dateStr) > new Date();
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Separate upcoming and past links
  const upcomingLinks = meetLinks.filter(m => isUpcoming(m.scheduled_date) && !m.attended);
  const pastLinks = meetLinks.filter(m => !isUpcoming(m.scheduled_date) || m.attended);

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement des liens de cours...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-teal-800 flex items-center gap-2">
            <Video className="w-6 h-6" />
            Mes Liens de Cours
          </h2>
          <p className="text-gray-600">Accédez à vos cours en ligne envoyés par vos professeurs</p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={fetchMeetLinks}
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualiser
        </Button>
      </div>

      {/* Upcoming Courses Alert */}
      {upcomingLinks.length > 0 && (
        <Card className="border-2 border-blue-300 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-blue-700 flex items-center gap-2">
              <Bell className="w-5 h-5 animate-pulse" />
              🎯 Cours à venir ({upcomingLinks.length})
            </CardTitle>
            <CardDescription>N&apos;oubliez pas de rejoindre vos cours programmés !</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {upcomingLinks.map((meet) => (
                <div 
                  key={meet.id} 
                  className="p-4 bg-white rounded-xl border-2 border-blue-200 shadow-sm hover:shadow-md transition-all"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <h3 className="font-bold text-lg text-blue-800 flex items-center gap-2">
                        <Video className="w-5 h-5" />
                        {meet.title}
                      </h3>
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-600 flex-wrap">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-4 h-4 text-blue-600" />
                          {formatDate(meet.scheduled_date)}
                        </span>
                        {meet.teacher_name && (
                          <span className="flex items-center gap-1">
                            <User className="w-4 h-4" />
                            {meet.teacher_name}
                          </span>
                        )}
                      </div>
                      
                      {/* Clickable Link Display */}
                      <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                        <p className="text-xs text-blue-600 mb-1 flex items-center gap-1">
                          <Link2 className="w-3 h-3" />
                          Lien du cours :
                        </p>
                        <a 
                          href={meet.meet_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-700 hover:text-blue-900 underline break-all text-sm font-medium"
                          onClick={(e) => e.stopPropagation()}
                        >
                          {meet.meet_link}
                        </a>
                      </div>
                    </div>
                    
                    <div className="flex gap-2 flex-shrink-0">
                      <Button
                        onClick={() => handleJoinCourse(meet.meet_link)}
                        className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6"
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Rejoindre le cours
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Past/Completed Courses */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-600" />
            Historique des cours ({pastLinks.length})
          </CardTitle>
          <CardDescription>Vos cours passés et terminés</CardDescription>
        </CardHeader>
        <CardContent>
          {pastLinks.length === 0 && upcomingLinks.length === 0 ? (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
              <Video className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">Aucun lien de cours reçu</p>
              <p className="text-sm text-gray-400 mt-2">
                Les liens de cours envoyés par vos professeurs apparaîtront ici
              </p>
            </div>
          ) : pastLinks.length === 0 ? (
            <p className="text-center text-gray-500 py-8">Aucun cours passé</p>
          ) : (
            <div className="space-y-3">
              {pastLinks.map((meet) => (
                <div 
                  key={meet.id} 
                  className={`p-4 rounded-lg border ${
                    meet.attended 
                      ? 'bg-green-50 border-green-200' 
                      : 'bg-gray-50 border-gray-200'
                  }`}
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-800">{meet.title}</h3>
                        {meet.attended && (
                          <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full flex items-center gap-1">
                            <CheckCircle2 className="w-3 h-3" />
                            Suivi
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 flex-wrap">
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(meet.scheduled_date)}
                        </span>
                        {meet.teacher_name && (
                          <span className="flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {meet.teacher_name}
                          </span>
                        )}
                      </div>
                      
                      {/* Clickable Link */}
                      <a 
                        href={meet.meet_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-teal-600 hover:text-teal-800 underline text-sm mt-2 inline-flex items-center gap-1"
                      >
                        <Link2 className="w-3 h-3" />
                        Voir le lien
                      </a>
                    </div>
                    
                    <div className="flex gap-2">
                      {!meet.attended && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkAttended(meet.id)}
                          className="border-green-600 text-green-600 hover:bg-green-50"
                        >
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          Marquer comme suivi
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleJoinCourse(meet.meet_link)}
                      >
                        <ExternalLink className="w-4 h-4 mr-1" />
                        Ouvrir
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentCourseLinks;
