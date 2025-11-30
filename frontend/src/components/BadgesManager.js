import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Award, UserPlus } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';

const BadgesManager = () => {
  const [badges, setBadges] = useState([]);
  const [students, setStudents] = useState([]);
  const [showAwardDialog, setShowAwardDialog] = useState(false);
  const [selectedBadge, setSelectedBadge] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState('');

  useEffect(() => {
    fetchBadges();
    fetchStudents();
  }, []);

  const fetchBadges = async () => {
    try {
      const res = await apiClient.get('/badges');
      setBadges(res.data);
    } catch (error) {
      console.error('Error fetching badges:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const res = await apiClient.get('/admin/all-users');
      const allStudents = res.data.filter(u => u.role === 'student');
      setStudents(allStudents);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const handleAwardBadge = async () => {
    if (!selectedStudent) {
      toast.error('Veuillez sélectionner un étudiant');
      return;
    }

    try {
      await apiClient.post('/admin/award-badge', {
        student_id: selectedStudent,
        badge_id: selectedBadge.id
      });
      toast.success(`Badge "${selectedBadge.name}" attribué !`);
      setShowAwardDialog(false);
      setSelectedStudent('');
      setSelectedBadge(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'attribution du badge');
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="bg-purple-50">
          <CardTitle className="text-purple-800">🏆 Gestion des Badges</CardTitle>
          <CardDescription>
            Attribuez des badges aux étudiants pour reconnaître leurs accomplissements
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          {badges.length === 0 ? (
            <div className="text-center py-12">
              <Award className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucun badge disponible</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              {badges.map((badge) => (
                <div
                  key={badge.id}
                  className="p-6 rounded-xl border-2 border-purple-200 bg-gradient-to-br from-purple-50 to-pink-50 text-center"
                >
                  <div className="text-6xl mb-3">{badge.icon}</div>
                  <h3 className="font-bold text-lg text-purple-700 mb-2">{badge.name}</h3>
                  <p className="text-sm text-gray-600 mb-4">{badge.description}</p>
                  
                  <Button
                    size="sm"
                    className="w-full bg-purple-600 hover:bg-purple-700"
                    onClick={() => {
                      setSelectedBadge(badge);
                      setShowAwardDialog(true);
                    }}
                  >
                    <UserPlus className="w-4 h-4 mr-2" />
                    Attribuer
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Award Badge Dialog */}
      <Dialog open={showAwardDialog} onOpenChange={setShowAwardDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Attribuer le badge "{selectedBadge?.name}"</DialogTitle>
            <DialogDescription>
              Sélectionnez un étudiant pour lui attribuer ce badge
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-5xl mb-2">{selectedBadge?.icon}</div>
              <p className="text-sm text-gray-600">{selectedBadge?.description}</p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Étudiant</label>
              <select
                value={selectedStudent}
                onChange={(e) => setSelectedStudent(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Sélectionnez un étudiant</option>
                {students.map((student) => (
                  <option key={student.id} value={student.id}>
                    {student.first_name} {student.last_name} ({student.email})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                onClick={() => setShowAwardDialog(false)}
                variant="outline"
                className="flex-1"
              >
                Annuler
              </Button>
              <Button
                onClick={handleAwardBadge}
                className="flex-1 bg-purple-600 hover:bg-purple-700"
              >
                Attribuer le badge
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Info Card */}
      <Card className="border-blue-200">
        <CardHeader className="bg-blue-50">
          <CardTitle className="text-blue-800">ℹ️ Information</CardTitle>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="space-y-2 text-sm text-gray-700">
            <p><strong>4 badges disponibles :</strong></p>
            <ul className="list-disc list-inside space-y-1 ml-2">
              <li>🚀 Débutant : Première connexion</li>
              <li>📚 Étudiant Assidu : 5 cours complétés</li>
              <li>⭐ Expert : 10 cours complétés</li>
              <li>🏆 Champion : Niveau complété</li>
            </ul>
            <p className="mt-4 text-xs text-gray-500">
              Les étudiants reçoivent une notification lorsqu'un badge leur est attribué.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BadgesManager;
