import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Calendar, Clock, User, RefreshCw, ChevronDown, ChevronUp, Check } from 'lucide-react';

const DAYS = [
  { id: 'monday', label: 'Lun' },
  { id: 'tuesday', label: 'Mar' },
  { id: 'wednesday', label: 'Mer' },
  { id: 'thursday', label: 'Jeu' },
  { id: 'friday', label: 'Ven' },
  { id: 'saturday', label: 'Sam' },
  { id: 'sunday', label: 'Dim' }
];

const TIME_SLOTS = [
  '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
  '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'
];

const TeacherStudentsAvailability = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedStudent, setExpandedStudent] = useState(null);

  useEffect(() => {
    fetchStudentsAvailability();
  }, []);

  const fetchStudentsAvailability = async () => {
    try {
      const res = await apiClient.get('/teacher/students-availability');
      setStudents(res.data);
    } catch (error) {
      console.error('Error fetching availability:', error);
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const getSlotKey = (day, time) => `${day}-${time}`;

  const hasSlot = (student, day, time) => {
    return student.slots?.some(s => s.day === day && s.time === time && s.available);
  };

  const countAvailableSlots = (student) => {
    return student.slots?.filter(s => s.available).length || 0;
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-6 h-6 text-teal-600" />
                📅 Disponibilités de mes Étudiants
              </CardTitle>
              <CardDescription>
                Consultez les créneaux disponibles de chaque étudiant
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={fetchStudentsAvailability}>
              <RefreshCw className="w-4 h-4 mr-1" />
              Actualiser
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {students.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <User className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Aucun étudiant assigné</p>
            </div>
          ) : (
            <div className="space-y-4">
              {students.map(student => (
                <Card key={student.student_id} className="border hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div 
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedStudent(expandedStudent === student.student_id ? null : student.student_id)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-teal-600" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-gray-800">{student.student_name}</h4>
                          <p className="text-sm text-gray-500">{student.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            countAvailableSlots(student) > 0 
                              ? 'bg-green-100 text-green-700' 
                              : 'bg-gray-100 text-gray-500'
                          }`}>
                            <Clock className="w-3 h-3 inline mr-1" />
                            {countAvailableSlots(student)} créneaux
                          </span>
                          {student.updated_at && (
                            <p className="text-xs text-gray-400 mt-1">
                              Mis à jour: {new Date(student.updated_at).toLocaleDateString('fr-FR')}
                            </p>
                          )}
                        </div>
                        {expandedStudent === student.student_id 
                          ? <ChevronUp className="w-5 h-5 text-gray-400" />
                          : <ChevronDown className="w-5 h-5 text-gray-400" />
                        }
                      </div>
                    </div>

                    {/* Expanded availability grid */}
                    {expandedStudent === student.student_id && (
                      <div className="mt-4 pt-4 border-t overflow-x-auto">
                        {countAvailableSlots(student) === 0 ? (
                          <p className="text-center text-gray-500 py-4">
                            Cet étudiant n&apos;a pas encore défini ses disponibilités
                          </p>
                        ) : (
                          <table className="w-full border-collapse min-w-[500px]">
                            <thead>
                              <tr>
                                <th className="p-2 border bg-gray-50 text-xs w-16">Heure</th>
                                {DAYS.map(day => (
                                  <th key={day.id} className="p-2 border bg-gray-50 text-xs text-center">
                                    {day.label}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {TIME_SLOTS.map(time => (
                                <tr key={time}>
                                  <td className="p-1 border bg-gray-50 text-xs font-medium text-center">
                                    {time}
                                  </td>
                                  {DAYS.map(day => {
                                    const isAvailable = hasSlot(student, day.id, time);
                                    return (
                                      <td key={`${day.id}-${time}`} className="p-1 border">
                                        <div className={`w-full h-6 rounded flex items-center justify-center ${
                                          isAvailable
                                            ? 'bg-teal-500 text-white'
                                            : 'bg-gray-100'
                                        }`}>
                                          {isAvailable && <Check className="w-4 h-4" />}
                                        </div>
                                      </td>
                                    );
                                  })}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherStudentsAvailability;
