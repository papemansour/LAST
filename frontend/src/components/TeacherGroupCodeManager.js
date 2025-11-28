import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Checkbox } from './ui/checkbox';
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
import { Users, CheckCircle, Copy, Sparkles, UserCheck } from 'lucide-react';

const TeacherGroupCodeManager = () => {
  const [pendingStudents, setPendingStudents] = useState([]);
  const [generatedGroups, setGeneratedGroups] = useState([]);
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [groupName, setGroupName] = useState('');
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [pendingRes, groupsRes] = await Promise.all([
        apiClient.get('/teacher/pending-group-students'),
        apiClient.get('/teacher/my-generated-groups')
      ]);
      setPendingStudents(pendingRes.data);
      setGeneratedGroups(groupsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleStudentToggle = (studentId) => {
    setSelectedStudents(prev =>
      prev.includes(studentId)
        ? prev.filter(id => id !== studentId)
        : [...prev, studentId]
    );
  };

  const handleGenerateCode = async () => {
    if (selectedStudents.length === 0) {
      toast.error('Veuillez sélectionner au moins un étudiant');
      return;
    }

    if (!groupName.trim()) {
      toast.error('Veuillez entrer un nom pour le groupe');
      return;
    }

    try {
      setGenerating(true);
      const response = await apiClient.post('/teacher/generate-group-magic-code', {
        student_ids: selectedStudents,
        group_name: groupName.trim()
      });

      toast.success(`Code magique généré : ${response.data.magic_code}`);
      setShowCreateDialog(false);
      setSelectedStudents([]);
      setGroupName('');
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error generating code:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la génération du code');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('Code copié dans le presse-papiers !');
  };

  const getStudentDisplayName = (student) => {
    if (student.members && student.members.length > 0) {
      const mainMember = student.members.find(m => m.is_main) || student.members[0];
      return `${mainMember.first_name} ${mainMember.last_name}`;
    }
    return student.email;
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Pending Students Section */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Users className="w-6 h-6 text-blue-600" />
              Étudiants en Attente
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Sélectionnez les étudiants et générez un code magique pour leur groupe
            </p>
          </div>
          {pendingStudents.length > 0 && (
            <Button
              onClick={() => setShowCreateDialog(true)}
              disabled={selectedStudents.length === 0}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Générer Code Magique ({selectedStudents.length})
            </Button>
          )}
        </div>

        {pendingStudents.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <UserCheck className="w-16 h-16 text-gray-300 mb-4" />
              <p className="text-gray-500 text-center">
                Aucun étudiant en attente.<br />
                Tous vos étudiants de groupe ont déjà reçu leur code magique !
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {pendingStudents.map((student) => (
              <Card
                key={student.id}
                className={`cursor-pointer transition-all ${
                  selectedStudents.includes(student.id)
                    ? 'border-2 border-blue-500 bg-blue-50'
                    : 'border hover:border-gray-400'
                }`}
                onClick={() => handleStudentToggle(student.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <Checkbox
                      checked={selectedStudents.includes(student.id)}
                      onCheckedChange={() => handleStudentToggle(student.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="font-semibold text-gray-800">
                        {getStudentDisplayName(student)}
                      </div>
                      <div className="text-sm text-gray-600 mt-1">{student.email}</div>
                      <div className="text-xs text-gray-500 mt-2 flex items-center gap-2">
                        <span className="px-2 py-0.5 bg-gray-100 rounded">
                          {student.level === 'beginner' && '🟢 Débutant'}
                          {student.level === 'intermediate' && '🟡 Intermédiaire'}
                          {student.level === 'advanced' && '🔴 Avancé'}
                          {student.level === 'kkid' && '🎨 K-Kid'}
                        </span>
                      </div>
                      {student.members && (
                        <div className="text-xs text-gray-500 mt-2">
                          <div className="font-medium">Membres du groupe:</div>
                          {student.members.map((member, idx) => (
                            <div key={idx} className="ml-2">
                              • {member.first_name} {member.last_name}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Generated Groups Section */}
      <div>
        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2 mb-4">
          <CheckCircle className="w-6 h-6 text-green-600" />
          Codes Magiques Générés
        </h2>

        {generatedGroups.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Sparkles className="w-16 h-16 text-gray-300 mb-4" />
              <p className="text-gray-500 text-center">
                Vous n'avez pas encore généré de code magique.<br />
                Sélectionnez des étudiants ci-dessus pour commencer !
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {generatedGroups.map((group, idx) => (
              <Card key={idx} className="border-l-4 border-l-green-500">
                <CardHeader>
                  <CardTitle className="text-lg">{group.group_name}</CardTitle>
                  <CardDescription>
                    Créé le {new Date(group.created_at).toLocaleDateString('fr-FR')}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Magic Code Display */}
                    <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-4 rounded-lg border-2 border-green-200">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-xs text-gray-600 mb-1">Code Magique</p>
                          <p className="text-2xl font-bold text-green-600 font-mono tracking-wider">
                            {group.magic_code}
                          </p>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => copyToClipboard(group.magic_code)}
                          className="hover:bg-green-100"
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Students List */}
                    <div>
                      <div className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        Étudiants ({group.students.length})
                      </div>
                      <div className="space-y-1">
                        {group.students.map((student, studentIdx) => (
                          <div
                            key={studentIdx}
                            className="text-sm text-gray-600 bg-gray-50 p-2 rounded flex justify-between items-center"
                          >
                            <div>
                              <div className="font-medium">{student.name}</div>
                              <div className="text-xs text-gray-500">{student.email}</div>
                            </div>
                            <span className="text-xs px-2 py-1 bg-white rounded border">
                              {student.level === 'beginner' && '🟢'}
                              {student.level === 'intermediate' && '🟡'}
                              {student.level === 'advanced' && '🔴'}
                              {student.level === 'kkid' && '🎨'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Create Code Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Générer un Code Magique</DialogTitle>
            <DialogDescription>
              Créez un code unique pour les {selectedStudents.length} étudiant(s) sélectionné(s)
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="groupName">Nom du Groupe *</Label>
              <Input
                id="groupName"
                placeholder="Ex: Groupe Lundi Matin"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                disabled={generating}
              />
            </div>

            <div className="bg-blue-50 p-3 rounded border border-blue-200">
              <p className="text-sm text-blue-800 font-medium mb-2">
                Étudiants sélectionnés:
              </p>
              {pendingStudents
                .filter(s => selectedStudents.includes(s.id))
                .map((student, idx) => (
                  <div key={idx} className="text-sm text-blue-700 ml-2">
                    • {getStudentDisplayName(student)}
                  </div>
                ))}
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowCreateDialog(false)}
              disabled={generating}
            >
              Annuler
            </Button>
            <Button
              onClick={handleGenerateCode}
              disabled={generating || !groupName.trim()}
              className="bg-gradient-to-r from-blue-600 to-indigo-600"
            >
              {generating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Génération...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Générer le Code
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TeacherGroupCodeManager;
