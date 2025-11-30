import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Send, Calendar, Users } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';

const TeacherMeetLinks = () => {
  const [students, setStudents] = useState([]);
  const [showDialog, setShowDialog] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    student_id: '',
    meet_link: '',
    title: '',
    scheduled_date: ''
  });

  useEffect(() => {
    fetchStudents();
  }, []);

  const fetchStudents = async () => {
    try {
      // Get teacher's students
      const res = await apiClient.get('/auth/me');
      const myStudents = res.data.students || [];
      
      // Fetch student details
      const allUsersRes = await apiClient.get('/admin/all-users');
      const studentDetails = allUsersRes.data.filter(u => 
        u.role === 'student' && myStudents.includes(u.id)
      );
      setStudents(studentDetails);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.student_id || !formData.meet_link || !formData.title || !formData.scheduled_date) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/teacher/send-meet-link', formData);
      toast.success('Lien de cours envoyé !');
      setShowDialog(false);
      setFormData({ student_id: '', meet_link: '', title: '', scheduled_date: '' });
    } catch (error) {
      toast.error("Erreur lors de l'envoi du lien");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader className="bg-teal-50">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-teal-800">📅 Envoyer un lien Google Meet</CardTitle>
            <CardDescription>
              Programmez des cours en ligne avec vos étudiants
            </CardDescription>
          </div>
          <Dialog open={showDialog} onOpenChange={setShowDialog}>
            <DialogTrigger asChild>
              <Button className="bg-teal-600 hover:bg-teal-700">
                <Send className="w-4 h-4 mr-2" />
                Envoyer un lien
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nouveau lien Google Meet</DialogTitle>
                <DialogDescription>
                  Envoyez un lien de cours à un étudiant
                </DialogDescription>
              </DialogHeader>
              
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="student">Étudiant *</Label>
                  <select
                    id="student"
                    required
                    value={formData.student_id}
                    onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}
                    className="w-full mt-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="">Sélectionnez un étudiant</option>
                    {students.map((student) => (
                      <option key={student.id} value={student.id}>
                        {student.first_name} {student.last_name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <Label htmlFor="title">Titre du cours *</Label>
                  <Input
                    id="title"
                    required
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    placeholder="Ex: Cours d'anglais - Grammaire"
                  />
                </div>

                <div>
                  <Label htmlFor="meet_link">Lien Google Meet *</Label>
                  <Input
                    id="meet_link"
                    type="url"
                    required
                    value={formData.meet_link}
                    onChange={(e) => setFormData({ ...formData, meet_link: e.target.value })}
                    placeholder="https://meet.google.com/xxx-xxxx-xxx"
                  />
                </div>

                <div>
                  <Label htmlFor="scheduled_date">Date et heure *</Label>
                  <Input
                    id="scheduled_date"
                    type="datetime-local"
                    required
                    value={formData.scheduled_date}
                    onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <Button
                    type="button"
                    onClick={() => setShowDialog(false)}
                    variant="outline"
                    className="flex-1"
                  >
                    Annuler
                  </Button>
                  <Button
                    type="submit"
                    disabled={loading}
                    className="flex-1 bg-teal-600 hover:bg-teal-700"
                  >
                    {loading ? 'Envoi...' : 'Envoyer'}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="flex items-center gap-4 p-6 bg-blue-50 border-2 border-blue-200 rounded-lg">
          <Calendar className="w-12 h-12 text-blue-600" />
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">
              Programmez vos cours en ligne
            </h3>
            <p className="text-sm text-gray-600">
              Envoyez des liens Google Meet à vos étudiants. Ils recevront une notification et pourront suivre leur progression.
            </p>
          </div>
        </div>

        {students.length > 0 && (
          <div className="mt-6">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-gray-600" />
              <h4 className="font-semibold text-gray-700">Vos étudiants ({students.length})</h4>
            </div>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {students.map((student) => (
                <div key={student.id} className="p-3 border rounded-lg bg-white">
                  <p className="font-medium text-sm">{student.first_name} {student.last_name}</p>
                  <p className="text-xs text-gray-500">{student.email}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TeacherMeetLinks;
