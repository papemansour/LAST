import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Users, UserCheck, Copy, CheckCircle } from 'lucide-react';

const PendingGroupRegistrations = () => {
  const [pendingGroups, setPendingGroups] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [selectedTeacher, setSelectedTeacher] = useState('');
  const [generatedCode, setGeneratedCode] = useState(null);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [groupsRes, teachersRes] = await Promise.all([
        apiClient.get('/admin/pending-group-registrations'),
        apiClient.get('/admin/users?role=teacher')
      ]);
      setPendingGroups(groupsRes.data);
      setTeachers(teachersRes.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement des données');
      setLoading(false);
    }
  };

  const handleOpenGenerateModal = (group) => {
    setSelectedGroup(group);
    setSelectedTeacher('');
    setGeneratedCode(null);
    setShowGenerateModal(true);
  };

  const handleGenerateCode = async () => {
    if (!selectedTeacher) {
      toast.error('Veuillez sélectionner un professeur');
      return;
    }

    setGenerating(true);
    try {
      const response = await apiClient.post(
        `/admin/generate-magic-code/${selectedGroup.id}?teacher_id=${selectedTeacher}`
      );
      
      setGeneratedCode(response.data);
      toast.success('Code magique généré avec succès !');
      
      // Refresh pending groups
      fetchData();
    } catch (error) {
      console.error('Error generating magic code:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la génération du code');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copié dans le presse-papiers !');
  };

  const getLevelLabel = (level) => {
    const labels = {
      'beginner': '🟢 Débutant',
      'intermediate': '🟡 Intermédiaire',
      'advanced': '🔴 Avancé',
      'kkid': '🎨 K-Kid'
    };
    return labels[level] || level;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800">📋 Inscriptions de Groupe en Attente</h2>
        <p className="text-sm text-gray-600 mt-1">
          Générez un code magique et assignez un professeur pour chaque groupe
        </p>
      </div>

      {/* Pending Groups List */}
      {pendingGroups.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <CheckCircle className="w-16 h-16 text-green-400 mb-4" />
            <p className="text-gray-500 text-center">
              Aucune inscription de groupe en attente<br />
              Toutes les inscriptions ont été traitées !
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pendingGroups.map((group) => (
            <Card
              key={group.id}
              className="border-l-4 border-l-orange-500"
            >
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Groupe de {group.total_members}
                </CardTitle>
                <CardDescription>{getLevelLabel(group.level)}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Main Contact Info */}
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-600 mb-1">Contact principal</p>
                    <p className="font-semibold text-sm">{group.members[0].first_name} {group.members[0].last_name}</p>
                    <p className="text-xs text-gray-600">{group.email}</p>
                    <p className="text-xs text-gray-600">{group.phone}</p>
                  </div>

                  {/* All Members */}
                  <div>
                    <p className="text-xs text-gray-600 mb-2">Membres du groupe :</p>
                    <div className="space-y-1">
                      {group.members.map((member, index) => (
                        <div key={index} className="flex items-center gap-2 text-sm">
                          <span className="text-blue-600">•</span>
                          <span>{member.first_name} {member.last_name}</span>
                          {member.is_main && (
                            <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded">
                              Principal
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Preferred Slots */}
                  {group.preferred_slots && (
                    <div>
                      <p className="text-xs text-gray-600">Créneaux préférés :</p>
                      <p className="text-sm">{group.preferred_slots}</p>
                    </div>
                  )}

                  {/* Registration Date */}
                  <div className="text-xs text-gray-500 pt-2 border-t">
                    Inscrit le {new Date(group.created_at).toLocaleDateString('fr-FR')}
                  </div>

                  {/* Generate Code Button */}
                  <Button
                    onClick={() => handleOpenGenerateModal(group)}
                    className="w-full bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700"
                  >
                    <UserCheck className="w-4 h-4 mr-2" />
                    Générer Code & Assigner
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Generate Magic Code Modal */}
      <Dialog open={showGenerateModal} onOpenChange={setShowGenerateModal}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Générer un Code Magique</DialogTitle>
            <DialogDescription>
              Assignez un professeur et générez un code de connexion pour ce groupe
            </DialogDescription>
          </DialogHeader>

          {!generatedCode ? (
            <div className="space-y-4 py-4">
              {/* Group Info */}
              {selectedGroup && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold mb-2">Informations du groupe</h4>
                  <div className="text-sm space-y-1">
                    <p><strong>Contact :</strong> {selectedGroup.members[0].first_name} {selectedGroup.members[0].last_name}</p>
                    <p><strong>Email :</strong> {selectedGroup.email}</p>
                    <p><strong>Membres :</strong> {selectedGroup.total_members} personne(s)</p>
                    <p><strong>Niveau :</strong> {getLevelLabel(selectedGroup.level)}</p>
                  </div>
                </div>
              )}

              {/* Teacher Selection */}
              <div className="space-y-2">
                <Label htmlFor="teacher">Sélectionner un professeur *</Label>
                <Select value={selectedTeacher} onValueChange={setSelectedTeacher}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choisir un professeur" />
                  </SelectTrigger>
                  <SelectContent>
                    {teachers.map((teacher) => (
                      <SelectItem key={teacher.id} value={teacher.id}>
                        {teacher.first_name} {teacher.last_name} - {teacher.email}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          ) : (
            /* Success - Show Generated Code */
            <div className="space-y-4 py-4">
              <div className="flex items-center justify-center mb-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-4xl">✅</span>
                </div>
              </div>

              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border-2 border-blue-300">
                <p className="text-sm text-gray-700 font-semibold mb-2 text-center">🔑 Code Magique Généré</p>
                <div className="bg-white p-4 rounded-lg border-2 border-blue-400 mb-3">
                  <p className="text-4xl font-bold text-center text-blue-600 tracking-widest font-mono">
                    {generatedCode.magic_code}
                  </p>
                </div>
                <Button
                  onClick={() => copyToClipboard(generatedCode.magic_code)}
                  variant="outline"
                  className="w-full border-blue-400 text-blue-600 hover:bg-blue-50"
                >
                  <Copy className="w-4 h-4 mr-2" />
                  Copier le code
                </Button>
              </div>

              <div className="bg-yellow-50 p-4 rounded-lg border-2 border-yellow-200">
                <h4 className="font-semibold text-gray-800 mb-2">📌 Instructions :</h4>
                <ul className="text-sm text-gray-700 space-y-2">
                  <li className="flex items-start gap-2">
                    <span className="text-yellow-600 font-bold">1.</span>
                    <span>Communiquez ce code au professeur <strong>{generatedCode.teacher_name}</strong></span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-yellow-600 font-bold">2.</span>
                    <span>Le professeur partagera le code avec tous les membres du groupe</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <span className="text-yellow-600 font-bold">3.</span>
                    <span>Tous se connecteront avec l'email <strong>{generatedCode.email}</strong> et ce code</span>
                  </li>
                </ul>
              </div>

              <div className="bg-gray-50 p-3 rounded-lg border border-gray-200 text-sm">
                <p><strong>Membres :</strong> {generatedCode.members_names}</p>
              </div>
            </div>
          )}

          <DialogFooter>
            {!generatedCode ? (
              <>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowGenerateModal(false)}
                  disabled={generating}
                >
                  Annuler
                </Button>
                <Button
                  onClick={handleGenerateCode}
                  disabled={!selectedTeacher || generating}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {generating ? 'Génération...' : 'Générer le Code'}
                </Button>
              </>
            ) : (
              <Button
                onClick={() => {
                  setShowGenerateModal(false);
                  setGeneratedCode(null);
                }}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                Fermer
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PendingGroupRegistrations;
