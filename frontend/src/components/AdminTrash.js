import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { RotateCcw, Trash2, AlertCircle, AlertTriangle } from 'lucide-react';

const AdminTrash = () => {
  const [deletedUsers, setDeletedUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [emptyingTrash, setEmptyingTrash] = useState(false);

  useEffect(() => {
    fetchDeletedUsers();
  }, []);

  const fetchDeletedUsers = async () => {
    try {
      const response = await apiClient.get('/admin/trash');
      setDeletedUsers(response.data);
      setLoading(false);
    } catch (error) {
      toast.error('Erreur lors du chargement de la poubelle');
      setLoading(false);
    }
  };

  const handleRestore = async (userId, userName) => {
    if (!window.confirm(`Restaurer ${userName} ?`)) return;
    try {
      await apiClient.post(`/admin/restore-user/${userId}`);
      toast.success(`${userName} restauré avec succès ! 🎉`);
      fetchDeletedUsers();
    } catch (error) {
      toast.error('Erreur lors de la restauration');
    }
  };

  const handlePermanentDelete = async (userId, userName) => {
    if (!window.confirm(`ATTENTION ! Supprimer définitivement ${userName} ? Cette action est irréversible !`)) return;
    try {
      await apiClient.delete(`/admin/permanent-delete/${userId}`);
      toast.success(`${userName} supprimé définitivement`);
      fetchDeletedUsers();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleEmptyTrash = async () => {
    if (!window.confirm(`⚠️ ATTENTION !\n\nVous êtes sur le point de supprimer DÉFINITIVEMENT ${deletedUsers.length} utilisateur(s).\n\nCette action est IRRÉVERSIBLE !\n\nÊtes-vous sûr de vouloir continuer ?`)) return;
    
    // Double confirmation
    if (!window.confirm(`🔴 DERNIÈRE CHANCE !\n\nConfirmez la suppression définitive de TOUS les utilisateurs de la poubelle.`)) return;
    
    setEmptyingTrash(true);
    try {
      const response = await apiClient.delete('/admin/empty-trash');
      toast.success(`🗑️ ${response.data.message}`);
      fetchDeletedUsers();
    } catch (error) {
      toast.error('Erreur lors du vidage de la poubelle');
    } finally {
      setEmptyingTrash(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Chargement...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Trash2 className="w-6 h-6 text-red-500" />
              🗑️ Poubelle
            </CardTitle>
            <CardDescription>
              Utilisateurs supprimés - Vous pouvez les restaurer ou les supprimer définitivement
            </CardDescription>
          </div>
          {deletedUsers.length > 0 && (
            <Button
              onClick={handleEmptyTrash}
              variant="destructive"
              disabled={emptyingTrash}
              className="flex items-center gap-2"
              data-testid="empty-trash-button"
            >
              <AlertTriangle className="w-4 h-4" />
              {emptyingTrash ? 'Suppression...' : `Vider la poubelle (${deletedUsers.length})`}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {deletedUsers.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎉</div>
            <p className="text-gray-500">La poubelle est vide !</p>
          </div>
        ) : (
          <div className="space-y-4">
            {deletedUsers.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-4 border-2 border-red-200 rounded-lg bg-red-50"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-lg">
                      {user.first_name} {user.last_name}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full font-semibold ${
                      user.role === 'teacher' ? 'bg-blue-200 text-blue-700' :
                      user.role === 'student' ? 'bg-green-200 text-green-700' :
                      'bg-gray-200 text-gray-700'
                    }`}>
                      {user.role === 'teacher' ? 'Professeur' : 
                       user.role === 'student' ? 'Étudiant' : user.role}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600">{user.email}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Supprimé le : {new Date(user.deleted_at).toLocaleDateString('fr-FR', {
                      day: '2-digit',
                      month: 'long',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleRestore(user.id, `${user.first_name} ${user.last_name}`)}
                    variant="outline"
                    className="border-green-500 text-green-600 hover:bg-green-50"
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Restaurer
                  </Button>
                  <Button
                    onClick={() => handlePermanentDelete(user.id, `${user.first_name} ${user.last_name}`)}
                    variant="destructive"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Supprimer définitivement
                  </Button>
                </div>
              </div>
            ))}
            
            {deletedUsers.length > 0 && (
              <div className="mt-6 p-4 bg-yellow-50 border-2 border-yellow-300 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-yellow-800">
                  <p className="font-semibold mb-1">⚠️ Attention</p>
                  <p>
                    La suppression définitive est <strong>irréversible</strong>. 
                    Toutes les données associées seront également supprimées.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AdminTrash;
