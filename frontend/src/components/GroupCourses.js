import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Users, Plus, Calendar, Video, Euro, Trash2, UserPlus, UserMinus, Clock, BookOpen } from 'lucide-react';
import apiClient from '../utils/api';

const GroupCourses = ({ userRole = 'admin' }) => {
  const [groups, setGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAddStudentModal, setShowAddStudentModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [newGroup, setNewGroup] = useState({
    name: '',
    description: '',
    teacher_id: '',
    max_students: 10,
    price_per_person: 80,
    currency: 'EUR',
    level: 'beginner',
    schedule: '',
    meet_link: '',
    start_date: '',
    end_date: '',
    total_hours: 20
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [groupsRes, teachersRes, studentsRes] = await Promise.all([
        apiClient.get('/group-courses'),
        apiClient.get('/admin/users?role=teacher'),
        apiClient.get('/admin/users?role=student')
      ]);
      setGroups(groupsRes.data || []);
      setTeachers(teachersRes.data || []);
      setStudents(studentsRes.data || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroup.name || !newGroup.teacher_id) {
      toast.error('Veuillez remplir les champs obligatoires');
      return;
    }

    try {
      await apiClient.post('/group-courses', newGroup);
      toast.success('🎓 Cours groupé créé avec succès!');
      setShowCreateModal(false);
      setNewGroup({
        name: '',
        description: '',
        teacher_id: '',
        max_students: 10,
        price_per_person: 80,
        currency: 'EUR',
        level: 'beginner',
        schedule: '',
        meet_link: '',
        start_date: '',
        end_date: '',
        total_hours: 20
      });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!window.confirm('Supprimer ce cours groupé ?')) return;
    
    try {
      await apiClient.delete(`/group-courses/${groupId}`);
      toast.success('Cours groupé supprimé');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleAddStudent = async (studentId) => {
    if (!selectedGroup) return;
    
    try {
      await apiClient.post(`/group-courses/${selectedGroup.id}/add-student`, { student_id: studentId });
      toast.success('✅ Étudiant ajouté au groupe!');
      setShowAddStudentModal(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'ajout');
    }
  };

  const handleRemoveStudent = async (groupId, studentId) => {
    if (!window.confirm('Retirer cet étudiant du groupe ?')) return;
    
    try {
      await apiClient.post(`/group-courses/${groupId}/remove-student`, { student_id: studentId });
      toast.success('Étudiant retiré du groupe');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors du retrait');
    }
  };

  const getLevelBadgeColor = (level) => {
    switch(level) {
      case 'beginner': return 'bg-green-100 text-green-700';
      case 'intermediate': return 'bg-blue-100 text-blue-700';
      case 'advanced': return 'bg-purple-100 text-purple-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getLevelLabel = (level) => {
    switch(level) {
      case 'beginner': return 'Débutant';
      case 'intermediate': return 'Intermédiaire';
      case 'advanced': return 'Avancé';
      default: return level;
    }
  };

  // Get students not in the selected group
  const availableStudents = selectedGroup 
    ? students.filter(s => !selectedGroup.student_ids?.includes(s.id))
    : students;

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
            <Users className="w-7 h-7 text-teal-600" />
            Cours Groupés
          </h2>
          <p className="text-gray-500">Gérez les cours avec plusieurs étudiants • 80€/personne</p>
        </div>
        
        {(userRole === 'admin' || userRole === 'secretary') && (
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button className="bg-teal-600 hover:bg-teal-700">
                <Plus className="w-4 h-4 mr-2" />
                Nouveau Groupe
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Créer un Cours Groupé</DialogTitle>
              </DialogHeader>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="col-span-2">
                  <Label>Nom du groupe *</Label>
                  <Input
                    value={newGroup.name}
                    onChange={(e) => setNewGroup({...newGroup, name: e.target.value})}
                    placeholder="Ex: Groupe Débutants Février 2026"
                  />
                </div>
                
                <div className="col-span-2">
                  <Label>Description</Label>
                  <Input
                    value={newGroup.description}
                    onChange={(e) => setNewGroup({...newGroup, description: e.target.value})}
                    placeholder="Description du cours..."
                  />
                </div>
                
                <div>
                  <Label>Professeur *</Label>
                  <Select
                    value={newGroup.teacher_id}
                    onValueChange={(value) => setNewGroup({...newGroup, teacher_id: value})}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Sélectionner" />
                    </SelectTrigger>
                    <SelectContent>
                      {teachers.map(t => (
                        <SelectItem key={t.id} value={t.id}>
                          {t.first_name} {t.last_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Niveau</Label>
                  <Select
                    value={newGroup.level}
                    onValueChange={(value) => setNewGroup({...newGroup, level: value})}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="beginner">Débutant</SelectItem>
                      <SelectItem value="intermediate">Intermédiaire</SelectItem>
                      <SelectItem value="advanced">Avancé</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div>
                  <Label>Prix par personne</Label>
                  <div className="flex gap-2">
                    <Input
                      type="number"
                      value={newGroup.price_per_person}
                      onChange={(e) => setNewGroup({...newGroup, price_per_person: parseFloat(e.target.value)})}
                    />
                    <Select
                      value={newGroup.currency}
                      onValueChange={(value) => setNewGroup({...newGroup, currency: value})}
                    >
                      <SelectTrigger className="w-24">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="EUR">EUR</SelectItem>
                        <SelectItem value="FCFA">FCFA</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                
                <div>
                  <Label>Nombre max d'étudiants</Label>
                  <Input
                    type="number"
                    value={newGroup.max_students}
                    onChange={(e) => setNewGroup({...newGroup, max_students: parseInt(e.target.value)})}
                  />
                </div>
                
                <div>
                  <Label>Heures totales</Label>
                  <Input
                    type="number"
                    value={newGroup.total_hours}
                    onChange={(e) => setNewGroup({...newGroup, total_hours: parseInt(e.target.value)})}
                  />
                </div>
                
                <div>
                  <Label>Horaires</Label>
                  <Input
                    value={newGroup.schedule}
                    onChange={(e) => setNewGroup({...newGroup, schedule: e.target.value})}
                    placeholder="Ex: Lundi et Mercredi 18h-19h30"
                  />
                </div>
                
                <div className="col-span-2">
                  <Label>Lien Google Meet</Label>
                  <Input
                    value={newGroup.meet_link}
                    onChange={(e) => setNewGroup({...newGroup, meet_link: e.target.value})}
                    placeholder="https://meet.google.com/..."
                  />
                </div>
                
                <div>
                  <Label>Date de début</Label>
                  <Input
                    type="date"
                    value={newGroup.start_date}
                    onChange={(e) => setNewGroup({...newGroup, start_date: e.target.value})}
                  />
                </div>
                
                <div>
                  <Label>Date de fin</Label>
                  <Input
                    type="date"
                    value={newGroup.end_date}
                    onChange={(e) => setNewGroup({...newGroup, end_date: e.target.value})}
                  />
                </div>
                
                <div className="col-span-2 flex justify-end gap-2 mt-4">
                  <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                    Annuler
                  </Button>
                  <Button onClick={handleCreateGroup} className="bg-teal-600 hover:bg-teal-700">
                    Créer le Groupe
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-teal-500 to-teal-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-teal-100 text-sm">Groupes actifs</p>
                <p className="text-3xl font-bold">{groups.filter(g => g.status === 'active').length}</p>
              </div>
              <Users className="w-10 h-10 text-teal-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Étudiants inscrits</p>
                <p className="text-3xl font-bold">
                  {groups.reduce((acc, g) => acc + (g.student_ids?.length || 0), 0)}
                </p>
              </div>
              <BookOpen className="w-10 h-10 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm">Revenus potentiels</p>
                <p className="text-3xl font-bold">
                  {groups.reduce((acc, g) => {
                    if (g.currency === 'EUR') {
                      return acc + (g.student_ids?.length || 0) * (g.price_per_person || 80);
                    }
                    return acc;
                  }, 0)}€
                </p>
              </div>
              <Euro className="w-10 h-10 text-green-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Heures totales</p>
                <p className="text-3xl font-bold">
                  {groups.reduce((acc, g) => acc + (g.total_hours || 0), 0)}h
                </p>
              </div>
              <Clock className="w-10 h-10 text-purple-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Groups List */}
      {groups.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <Users className="w-16 h-16 mx-auto text-gray-300 mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 mb-2">Aucun cours groupé</h3>
            <p className="text-gray-500 mb-4">Créez votre premier cours groupé pour commencer</p>
            {(userRole === 'admin' || userRole === 'secretary') && (
              <Button onClick={() => setShowCreateModal(true)} className="bg-teal-600 hover:bg-teal-700">
                <Plus className="w-4 h-4 mr-2" />
                Créer un Groupe
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6">
          {groups.map(group => (
            <Card key={group.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-xl flex items-center gap-2">
                      {group.name}
                      <Badge className={getLevelBadgeColor(group.level)}>
                        {getLevelLabel(group.level)}
                      </Badge>
                      {group.status === 'active' ? (
                        <Badge className="bg-green-100 text-green-700">Actif</Badge>
                      ) : (
                        <Badge className="bg-gray-100 text-gray-700">{group.status}</Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      {group.description || 'Aucune description'}
                    </CardDescription>
                  </div>
                  
                  {(userRole === 'admin' || userRole === 'secretary') && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDeleteGroup(group.id)}
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="grid md:grid-cols-3 gap-6">
                  {/* Info */}
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm">
                      <Users className="w-4 h-4 text-teal-600" />
                      <span className="font-medium">Professeur:</span>
                      <span>{group.teacher_name || 'Non assigné'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Calendar className="w-4 h-4 text-teal-600" />
                      <span className="font-medium">Horaires:</span>
                      <span>{group.schedule || 'Non défini'}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Euro className="w-4 h-4 text-green-600" />
                      <span className="font-medium">Prix:</span>
                      <span className="text-green-600 font-semibold">
                        {group.price_per_person} {group.currency}/personne
                      </span>
                    </div>
                    {group.meet_link && (
                      <a
                        href={group.meet_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"
                      >
                        <Video className="w-4 h-4" />
                        Rejoindre le cours
                      </a>
                    )}
                  </div>
                  
                  {/* Students */}
                  <div className="md:col-span-2">
                    <div className="flex justify-between items-center mb-3">
                      <h4 className="font-semibold text-gray-700">
                        Étudiants ({group.enrolled_count || 0}/{group.max_students})
                      </h4>
                      {(userRole === 'admin' || userRole === 'secretary') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedGroup(group);
                            setShowAddStudentModal(true);
                          }}
                          disabled={(group.enrolled_count || 0) >= group.max_students}
                          className="text-teal-600 border-teal-300 hover:bg-teal-50"
                        >
                          <UserPlus className="w-4 h-4 mr-1" />
                          Ajouter
                        </Button>
                      )}
                    </div>
                    
                    {/* Progress bar */}
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-3">
                      <div
                        className="bg-teal-600 h-2 rounded-full transition-all"
                        style={{ width: `${((group.enrolled_count || 0) / group.max_students) * 100}%` }}
                      />
                    </div>
                    
                    {/* Student list */}
                    <div className="flex flex-wrap gap-2">
                      {group.student_names?.length > 0 ? (
                        group.student_names.map((name, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-1 bg-gray-100 rounded-full px-3 py-1 text-sm"
                          >
                            <span>{name}</span>
                            {(userRole === 'admin' || userRole === 'secretary') && (
                              <button
                                onClick={() => handleRemoveStudent(group.id, group.student_ids[idx])}
                                className="text-red-400 hover:text-red-600 ml-1"
                              >
                                <UserMinus className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        ))
                      ) : (
                        <p className="text-gray-400 text-sm italic">Aucun étudiant inscrit</p>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Student Modal */}
      <Dialog open={showAddStudentModal} onOpenChange={setShowAddStudentModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter un étudiant au groupe</DialogTitle>
          </DialogHeader>
          <div className="mt-4 space-y-4">
            <p className="text-sm text-gray-500">
              Groupe: <strong>{selectedGroup?.name}</strong>
            </p>
            
            <div className="max-h-64 overflow-y-auto space-y-2">
              {availableStudents.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Aucun étudiant disponible</p>
              ) : (
                availableStudents.map(student => (
                  <div
                    key={student.id}
                    className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                    onClick={() => handleAddStudent(student.id)}
                  >
                    <div>
                      <p className="font-medium">{student.first_name} {student.last_name}</p>
                      <p className="text-sm text-gray-500">{student.email}</p>
                    </div>
                    <Button size="sm" variant="ghost" className="text-teal-600">
                      <UserPlus className="w-4 h-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GroupCourses;
