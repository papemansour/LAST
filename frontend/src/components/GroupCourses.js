import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Users, Calendar, Clock, MapPin, Star, CheckCircle, Euro } from 'lucide-react';

const GroupCourses = ({ userRole = 'student' }) => {
  const [courses, setCourses] = useState([]);
  const [myCourses, setMyCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [enrollingId, setEnrollingId] = useState(null);

  useEffect(() => {
    fetchCourses();
  }, [userRole]);

  const fetchCourses = async () => {
    try {
      // Fetch available courses
      const availableResponse = await apiClient.get('/group-courses');
      setCourses(availableResponse.data);
      
      // Fetch my enrolled courses if student
      if (userRole === 'student') {
        const myResponse = await apiClient.get('/student/my-group-courses');
        setMyCourses(myResponse.data);
      } else if (userRole === 'teacher') {
        const myResponse = await apiClient.get('/teacher/my-group-courses');
        setMyCourses(myResponse.data);
      }
    } catch (error) {
      console.error('Error fetching courses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleEnroll = async (courseId) => {
    setEnrollingId(courseId);
    try {
      await apiClient.post(`/group-courses/${courseId}/enroll`);
      toast.success('🎉 Inscription réussie ! +2 points ajoutés à votre Coffre aux Trésors');
      fetchCourses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'inscription');
    } finally {
      setEnrollingId(null);
    }
  };

  const getLevelBadge = (level) => {
    const colors = {
      beginner: 'bg-green-100 text-green-700',
      intermediate: 'bg-blue-100 text-blue-700',
      advanced: 'bg-purple-100 text-purple-700'
    };
    const labels = {
      beginner: 'Débutant',
      intermediate: 'Intermédiaire',
      advanced: 'Avancé'
    };
    return (
      <Badge className={colors[level] || 'bg-gray-100'}>
        {labels[level] || level}
      </Badge>
    );
  };

  const formatDays = (days) => {
    const dayLabels = {
      monday: 'Lun',
      tuesday: 'Mar',
      wednesday: 'Mer',
      thursday: 'Jeu',
      friday: 'Ven',
      saturday: 'Sam',
      sunday: 'Dim'
    };
    return days?.map(d => dayLabels[d] || d).join(', ') || 'À définir';
  };

  const isEnrolled = (courseId) => {
    return myCourses.some(c => c.id === courseId);
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse h-48 bg-gray-200 rounded-lg"></div>
        <div className="animate-pulse h-48 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Mes cours groupés */}
      {myCourses.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            Mes cours groupés
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            {myCourses.map((course) => (
              <Card key={course.id} className="border-2 border-green-200 bg-green-50">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{course.title}</CardTitle>
                      <CardDescription>
                        {course.teacher_name && `Prof. ${course.teacher_name}`}
                      </CardDescription>
                    </div>
                    {getLevelBadge(course.level)}
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDays(course.scheduled_days)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>{course.scheduled_time || 'Horaire à confirmer'}</span>
                    </div>
                    {course.group_members?.length > 0 && (
                      <div className="flex items-center gap-2 text-gray-600">
                        <Users className="w-4 h-4" />
                        <span>Avec: {course.group_members.join(', ')}</span>
                      </div>
                    )}
                    {course.meet_link && (
                      <a 
                        href={course.meet_link} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-block mt-2 px-4 py-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 text-sm"
                      >
                        🎥 Rejoindre le cours
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Cours disponibles */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
          <Users className="w-5 h-5 text-teal-600" />
          Cours groupés disponibles
        </h3>
        
        {courses.length === 0 ? (
          <Card className="bg-gray-50">
            <CardContent className="py-8 text-center">
              <Users className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600">Aucun cours groupé disponible pour le moment</p>
              <p className="text-sm text-gray-500 mt-1">Revenez bientôt pour découvrir de nouveaux cours !</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {courses.map((course) => (
              <Card 
                key={course.id} 
                className={`hover:shadow-lg transition-shadow ${
                  course.status === 'full' ? 'opacity-75' : ''
                } ${course.discount_applied ? 'border-2 border-orange-300' : ''}`}
              >
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{course.title}</CardTitle>
                      <CardDescription>
                        {course.teacher_name && `Prof. ${course.teacher_name}`}
                      </CardDescription>
                    </div>
                    {getLevelBadge(course.level)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {course.description && (
                    <p className="text-sm text-gray-600">{course.description}</p>
                  )}
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-gray-600">
                      <Calendar className="w-4 h-4" />
                      <span>{formatDays(course.scheduled_days)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Clock className="w-4 h-4" />
                      <span>{course.scheduled_time || 'Horaire à confirmer'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                      <Users className="w-4 h-4" />
                      <span>{course.enrolled_count}/{course.max_students} inscrits</span>
                      {course.spots_left > 0 && course.spots_left <= 2 && (
                        <Badge className="bg-red-100 text-red-700 text-xs">
                          Plus que {course.spots_left} place(s) !
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Prix */}
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Prix/pers :</span>
                      <div className="text-right">
                        {course.discount_applied ? (
                          <div>
                            <span className="line-through text-gray-400 text-sm mr-2">
                              {course.price_per_person_eur}€
                            </span>
                            <span className="font-bold text-green-600">
                              {course.final_price_eur}€
                            </span>
                            <Badge className="ml-2 bg-orange-100 text-orange-700 text-xs">
                              -{course.discount_4_plus}%
                            </Badge>
                          </div>
                        ) : (
                          <span className="font-bold text-gray-800">
                            {course.price_per_person_eur}€ / {course.price_per_person_fcfa?.toLocaleString()} FCFA
                          </span>
                        )}
                      </div>
                    </div>
                    {!course.discount_applied && course.enrolled_count < 4 && (
                      <p className="text-xs text-orange-600 mt-1">
                        ✨ -{course.discount_4_plus}% si 4+ étudiants s'inscrivent !
                      </p>
                    )}
                  </div>

                  {/* Bouton d'inscription */}
                  {userRole === 'student' && (
                    <Button
                      className="w-full"
                      disabled={course.status === 'full' || isEnrolled(course.id) || enrollingId === course.id}
                      onClick={() => handleEnroll(course.id)}
                    >
                      {isEnrolled(course.id) ? (
                        <>✅ Déjà inscrit</>
                      ) : course.status === 'full' ? (
                        <>😢 Complet</>
                      ) : enrollingId === course.id ? (
                        <>⏳ Inscription...</>
                      ) : (
                        <>🎓 S'inscrire (+2 pts)</>
                      )}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Info box */}
      <Card className="bg-gradient-to-r from-teal-50 to-cyan-50 border-teal-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Star className="w-6 h-6 text-teal-600 flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-semibold text-teal-800">Pourquoi choisir un cours groupé ?</h4>
              <ul className="text-sm text-teal-700 mt-2 space-y-1">
                <li>💰 Tarif avantageux : 80€/pers au lieu de cours individuels</li>
                <li>👥 Apprenez avec d'autres étudiants de votre niveau</li>
                <li>🎮 Exercices interactifs et discussions de groupe</li>
                <li>📈 Réduction supplémentaire de 10% à partir de 4 étudiants !</li>
                <li>🎁 +2 points dans votre Coffre aux Trésors à l'inscription</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default GroupCourses;
