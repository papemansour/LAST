import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Input } from './ui/input';
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
  DialogTrigger,
  DialogFooter,
} from './ui/dialog';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Copy, Users, CheckCircle, XCircle, Plus, ToggleLeft, ToggleRight } from 'lucide-react';

const GroupCodeManager = () => {
  const [groupCodes, setGroupCodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [formData, setFormData] = useState({
    group_name: '',
    level: '',
    max_students: 3
  });

  useEffect(() => {
    fetchGroupCodes();
  }, []);

  const fetchGroupCodes = async () => {
    try {
      const response = await apiClient.get('/teacher/my-group-codes');
      setGroupCodes(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching group codes:', error);
      toast.error('Erreur lors du chargement des codes');
      setLoading(false);
    }
  };

  const handleCreateCode = async (e) => {
    e.preventDefault();
    
    if (!formData.group_name || !formData.level) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      const response = await apiClient.post('/teacher/create-group-code', formData);
      toast.success('Code de groupe créé avec succès !');
      setShowCreateDialog(false);
      setFormData({ group_name: '', level: '', max_students: 3 });
      fetchGroupCodes();
    } catch (error) {
      console.error('Error creating group code:', error);
      toast.error(error.response?.data?.detail || 'Erreur lors de la création du code');
    }
  };

  const handleToggleCode = async (codeId, currentStatus) => {
    try {
      const response = await apiClient.put(`/teacher/toggle-group-code/${codeId}`);
      toast.success(response.data.message);
      fetchGroupCodes();
    } catch (error) {
      console.error('Error toggling code:', error);
      toast.error('Erreur lors de la modification du code');
    }
  };

  const copyToClipboard = (code) => {
    navigator.clipboard.writeText(code);
    toast.success('Code copié dans le presse-papiers !');
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
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Codes de Groupe Magiques ✨</h2>
          <p className="text-sm text-gray-600 mt-1">
            Créez des codes uniques pour permettre à vos étudiants de s'inscrire facilement
          </p>
        </div>
        <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
          <DialogTrigger asChild>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="w-4 h-4 mr-2" />
              Créer un Code
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Créer un Code de Groupe</DialogTitle>
              <DialogDescription>
                Générez un code unique que vos étudiants pourront utiliser pour s'inscrire
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateCode} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="group_name">Nom du Groupe *</Label>
                <Input
                  id="group_name"
                  placeholder="Ex: Groupe du Lundi Matin"
                  value={formData.group_name}
                  onChange={(e) => setFormData({ ...formData, group_name: e.target.value })}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="level">Niveau *</Label>
                <Select
                  value={formData.level}
                  onValueChange={(value) => setFormData({ ...formData, level: value })}
                  required
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionnez un niveau" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">🟢 Débutant</SelectItem>
                    <SelectItem value="intermediate">🟡 Intermédiaire</SelectItem>
                    <SelectItem value="advanced">🔴 Avancé</SelectItem>
                    <SelectItem value="kkid">🎨 K-Kid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="max_students">Nombre Maximum d'Étudiants</Label>
                <Input
                  id="max_students"
                  type="number"
                  min="1"
                  max="10"
                  value={formData.max_students}
                  onChange={(e) => setFormData({ ...formData, max_students: parseInt(e.target.value) })}
                />
              </div>
              
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setShowCreateDialog(false)}>
                  Annuler
                </Button>
                <Button type="submit" className="bg-blue-600 hover:bg-blue-700">
                  Créer le Code
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Group Codes List */}
      {groupCodes.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Users className="w-16 h-16 text-gray-300 mb-4" />
            <p className="text-gray-500 text-center">
              Vous n'avez pas encore créé de code de groupe.<br />
              Cliquez sur "Créer un Code" pour commencer !
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {groupCodes.map((code) => (
            <Card
              key={code.id}
              className={`${
                code.is_active
                  ? 'border-l-4 border-l-green-500'
                  : 'border-l-4 border-l-gray-400 opacity-70'
              }`}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{code.group_name}</CardTitle>
                    <CardDescription>{getLevelLabel(code.level)}</CardDescription>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleCode(code.id, code.is_active)}
                    className="ml-2"
                  >
                    {code.is_active ? (
                      <ToggleRight className="w-5 h-5 text-green-600" />
                    ) : (
                      <ToggleLeft className="w-5 h-5 text-gray-400" />
                    )}
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Code Display */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-4 rounded-lg border-2 border-blue-200">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Code Magique</p>
                        <p className="text-2xl font-bold text-blue-600 font-mono tracking-wider">
                          {code.code}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => copyToClipboard(code.code)}
                        className="hover:bg-blue-100"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Student Count */}
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center space-x-2">
                      <Users className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600">Étudiants inscrits</span>
                    </div>
                    <span className="font-semibold text-gray-800">
                      {code.current_students} / {code.max_students}
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all ${
                        code.current_students >= code.max_students
                          ? 'bg-red-500'
                          : 'bg-blue-600'
                      }`}
                      style={{
                        width: `${(code.current_students / code.max_students) * 100}%`
                      }}
                    ></div>
                  </div>

                  {/* Status */}
                  <div className="flex items-center justify-center pt-2">
                    {code.is_active ? (
                      code.current_students >= code.max_students ? (
                        <span className="flex items-center text-xs text-red-600 font-medium">
                          <XCircle className="w-3 h-3 mr-1" />
                          Groupe Complet
                        </span>
                      ) : (
                        <span className="flex items-center text-xs text-green-600 font-medium">
                          <CheckCircle className="w-3 h-3 mr-1" />
                          Actif - {code.max_students - code.current_students} place(s) disponible(s)
                        </span>
                      )
                    ) : (
                      <span className="flex items-center text-xs text-gray-600 font-medium">
                        <XCircle className="w-3 h-3 mr-1" />
                        Désactivé
                      </span>
                    )}
                  </div>

                  {/* Created Date */}
                  <div className="text-xs text-gray-500 text-center pt-2 border-t">
                    Créé le {new Date(code.created_at).toLocaleDateString('fr-FR')}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

export default GroupCodeManager;
