import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { getFileUrl } from '../utils/fileUrl';
import { Upload, FileText, Trash2, Users, CheckCircle2, Send, X, Download, Eye } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';

const DocumentsManager = ({ userRole }) => {
  const [documents, setDocuments] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [showSendModal, setShowSendModal] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    recipient_ids: []
  });

  useEffect(() => {
    fetchDocuments();
    fetchStudents();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await apiClient.get('/documents/my-documents');
      setDocuments(res.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      // For teachers, get their students; for admin, get all students
      if (userRole === 'teacher') {
        const res = await apiClient.get('/auth/me');
        const myStudents = res.data.students || [];
        
        // Fetch student details
        const allUsersRes = await apiClient.get('/admin/all-users');
        const studentDetails = allUsersRes.data.filter(u => 
          u.role === 'student' && myStudents.includes(u.id)
        );
        setStudents(studentDetails);
      } else {
        // Admin gets all students
        const res = await apiClient.get('/admin/all-users');
        const allStudents = res.data.filter(u => u.role === 'student');
        setStudents(allStudents);
      }
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Fichier trop volumineux (max 50MB)');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setUploadedFile({
        file_url: res.data.file_url,
        file_name: res.data.file_name,
        file_type: res.data.file_type
      });
      toast.success(`Fichier "${file.name}" chargé`);
      setShowSendModal(true);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || "Erreur d'upload");
    } finally {
      setUploading(false);
    }
  };

  const toggleStudent = (studentId) => {
    setFormData(prev => ({
      ...prev,
      recipient_ids: prev.recipient_ids.includes(studentId)
        ? prev.recipient_ids.filter(id => id !== studentId)
        : [...prev.recipient_ids, studentId]
    }));
  };

  const selectAllStudents = () => {
    if (formData.recipient_ids.length === students.length) {
      setFormData(prev => ({ ...prev, recipient_ids: [] }));
    } else {
      setFormData(prev => ({ ...prev, recipient_ids: students.map(s => s.id) }));
    }
  };

  const handleSendDocument = async () => {
    if (!formData.title.trim()) {
      toast.error('Veuillez saisir un titre');
      return;
    }

    if (formData.recipient_ids.length === 0) {
      toast.error('Veuillez sélectionner au moins un étudiant');
      return;
    }

    if (!uploadedFile) {
      toast.error('Aucun fichier chargé');
      return;
    }

    setLoading(true);
    try {
      await apiClient.post('/documents/send', {
        title: formData.title,
        description: formData.description,
        file_url: uploadedFile.file_url,
        file_name: uploadedFile.file_name,
        file_type: uploadedFile.file_type,
        recipient_ids: formData.recipient_ids
      });

      toast.success(`Document envoyé à ${formData.recipient_ids.length} étudiant(s)`);
      setShowSendModal(false);
      setFormData({ title: '', description: '', recipient_ids: [] });
      setUploadedFile(null);
      fetchDocuments();
    } catch (error) {
      toast.error("Erreur lors de l'envoi du document");
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteDocument = async (documentId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce document ?')) return;

    try {
      await apiClient.delete(`/documents/${documentId}`);
      toast.success('Document supprimé');
      fetchDocuments();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const getFileIcon = (fileType) => {
    return <FileText className="w-5 h-5 text-teal-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>📤 Envoyer un document</CardTitle>
          <CardDescription>
            Partagez des documents avec vos étudiants (PDF, Word, Excel, PowerPoint, images, etc.)
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-gray-300 rounded-lg hover:border-teal-500 transition">
            <Upload className="w-12 h-12 text-gray-400 mb-4" />
            <label className="cursor-pointer">
              <input
                type="file"
                className="hidden"
                onChange={handleFileUpload}
                disabled={uploading}
                accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.jpg,.jpeg,.png,.gif,.webp,.mp4,.mp3,.txt,.zip"
              />
              <Button disabled={uploading} variant="outline" className="pointer-events-none">
                {uploading ? 'Upload en cours...' : 'Sélectionner un fichier'}
              </Button>
            </label>
            <p className="text-sm text-gray-500 mt-2">Max 50MB</p>
          </div>
        </CardContent>
      </Card>

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>📄 Documents envoyés</CardTitle>
          <CardDescription>
            {documents.length} document(s) partagé(s)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {documents.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Aucun document envoyé</p>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div key={doc.id} className="p-4 border rounded-lg flex items-start justify-between hover:bg-gray-50">
                  <div className="flex items-start gap-3 flex-1">
                    {getFileIcon(doc.file_type)}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-gray-900">{doc.title}</h3>
                      {doc.description && (
                        <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>📎 {doc.file_name}</span>
                        <span>👥 {doc.recipient_ids.length} étudiant(s)</span>
                        <span>✓ {doc.read_by?.length || 0} lu(s)</span>
                        <span>{new Date(doc.created_at).toLocaleDateString('fr-FR')}</span>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteDocument(doc.id)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Send Document Modal */}
      <Dialog open={showSendModal} onOpenChange={setShowSendModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Envoyer un document</DialogTitle>
            <DialogDescription>
              Fichier : {uploadedFile?.file_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Titre du document *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Ex: Devoirs pour la semaine 10"
              />
            </div>

            <div>
              <Label htmlFor="description">Description (optionnel)</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Ajoutez des détails sur ce document..."
                rows={3}
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <Label>Destinataires * ({formData.recipient_ids.length} sélectionné(s))</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={selectAllStudents}
                >
                  {formData.recipient_ids.length === students.length ? 'Tout désélectionner' : 'Tout sélectionner'}
                </Button>
              </div>
              
              <div className="border rounded-lg p-3 max-h-[300px] overflow-y-auto">
                {students.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">Aucun étudiant disponible</p>
                ) : (
                  <div className="space-y-2">
                    {students.map((student) => (
                      <div
                        key={student.id}
                        className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded cursor-pointer"
                        onClick={() => toggleStudent(student.id)}
                      >
                        <input
                          type="checkbox"
                          checked={formData.recipient_ids.includes(student.id)}
                          onChange={() => toggleStudent(student.id)}
                          className="h-4 w-4 text-teal-600 rounded border-gray-300"
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{student.first_name} {student.last_name}</p>
                          <p className="text-xs text-gray-500">{student.email}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-3 pt-4">
              <Button
                onClick={() => setShowSendModal(false)}
                variant="outline"
                className="flex-1"
              >
                Annuler
              </Button>
              <Button
                onClick={handleSendDocument}
                disabled={loading}
                className="flex-1 bg-teal-600 hover:bg-teal-700"
              >
                <Send className="w-4 h-4 mr-2" />
                {loading ? 'Envoi...' : 'Envoyer le document'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DocumentsManager;
