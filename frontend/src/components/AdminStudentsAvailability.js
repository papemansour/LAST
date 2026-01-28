import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Calendar, Clock, RefreshCw, Users, Check, User, Search, Filter } from 'lucide-react';

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

const AdminStudentsAvailability = () => {
  const [studentsAvailability, setStudentsAvailability] = useState([]);
  const [filteredStudents, setFilteredStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterTeacher, setFilterTeacher] = useState('all');
  const [teachers, setTeachers] = useState([]);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    filterStudents();
  }, [searchTerm, filterTeacher, studentsAvailability]);

  const fetchData = async () => {
    try {
      const [availRes, teachersRes] = await Promise.all([
        apiClient.get('/admin/all-students-availability'),
        apiClient.get('/admin/all-users').then(res => res.data.filter(u => u.role === 'teacher'))
      ]);
      setStudentsAvailability(availRes.data);
      setTeachers(teachersRes);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  };

  const filterStudents = () => {
    let filtered = [...studentsAvailability];
    
    if (searchTerm) {
      filtered = filtered.filter(s => 
        s.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        s.email?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    if (filterTeacher !== 'all') {
      filtered = filtered.filter(s => s.teacher_name === filterTeacher);
    }
    
    setFilteredStudents(filtered);
  };

  const getSlotStatus = (day, time) => {
    if (!selectedStudent) return false;
    return selectedStudent.slots?.some(s => s.day === day && s.time === time && s.available);
  };

  const countAvailableSlots = (student) => {
    return student.slots?.filter(s => s.available)?.length || 0;
  };

  const uniqueTeachers = [...new Set(studentsAvailability.map(s => s.teacher_name).filter(Boolean))];

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-6 h-6 text-blue-600" />
                Disponibilités des Étudiants
              </CardTitle>
              <CardDescription>
                Vue d'ensemble des créneaux disponibles de tous les étudiants
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={fetchData}>
              <RefreshCw className="w-4 h-4 mr-1" />
              Actualiser
            </Button>
          </div>
          
          {/* Filters */}
          <div className="flex flex-col md:flex-row gap-4 mt-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                placeholder="Rechercher un étudiant..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <select
                value={filterTeacher}
                onChange={(e) => setFilterTeacher(e.target.value)}
                className="border rounded-md px-3 py-2 text-sm"
              >
                <option value="all">Tous les professeurs</option>
                {uniqueTeachers.map(teacher => (
                  <option key={teacher} value={teacher}>{teacher}</option>
                ))}
                <option value="">Sans professeur</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredStudents.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Aucun étudiant trouvé</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-4 gap-6">
              {/* Student List */}
              <div className="md:col-span-1 space-y-2">
                <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <User className="w-4 h-4" />
                  Étudiants ({filteredStudents.length})
                </h3>
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {filteredStudents.map((student) => (
                    <button
                      key={student.student_id}
                      onClick={() => setSelectedStudent(student)}
                      className={`w-full p-3 rounded-lg text-left transition ${
                        selectedStudent?.student_id === student.student_id
                          ? 'bg-blue-100 border-2 border-blue-500'
                          : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                      }`}
                    >
                      <p className="font-medium text-sm">{student.student_name}</p>
                      <p className="text-xs text-gray-500">{student.email}</p>
                      {student.teacher_name && (
                        <p className="text-xs text-blue-600 mt-1">
                          👨‍🏫 {student.teacher_name}
                        </p>
                      )}
                      <div className="mt-1 flex items-center gap-1 text-xs text-green-600">
                        <Clock className="w-3 h-3" />
                        {countAvailableSlots(student)} créneau(x)
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Calendar View */}
              <div className="md:col-span-3">
                {selectedStudent ? (
                  <div>
                    <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                      <h4 className="font-semibold text-blue-800">
                        📅 Disponibilités de {selectedStudent.student_name}
                      </h4>
                      {selectedStudent.teacher_name && (
                        <p className="text-sm text-blue-600">
                          Professeur: {selectedStudent.teacher_name}
                        </p>
                      )}
                      {selectedStudent.updated_at && (
                        <p className="text-xs text-blue-600 mt-1">
                          Mis à jour le {new Date(selectedStudent.updated_at).toLocaleString('fr-FR')}
                        </p>
                      )}
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full border-collapse text-sm">
                        <thead>
                          <tr>
                            <th className="p-2 border bg-gray-50 text-left w-16">Heure</th>
                            {DAYS.map(day => (
                              <th key={day.id} className="p-2 border bg-gray-50 text-center">
                                {day.label}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {TIME_SLOTS.map(time => (
                            <tr key={time}>
                              <td className="p-2 border bg-gray-50 font-medium text-xs">
                                {time}
                              </td>
                              {DAYS.map(day => {
                                const isAvailable = getSlotStatus(day.id, time);
                                return (
                                  <td key={`${day.id}-${time}`} className="p-1 border">
                                    <div
                                      className={`w-full h-8 rounded flex items-center justify-center ${
                                        isAvailable
                                          ? 'bg-green-500 text-white'
                                          : 'bg-gray-100 text-gray-300'
                                      }`}
                                    >
                                      {isAvailable && <Check className="w-4 h-4" />}
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p>Sélectionnez un étudiant pour voir ses disponibilités</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminStudentsAvailability;
