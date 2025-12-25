import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { FileText, Download, Eye, File, Image as ImageIcon, Clock } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const StudentDocuments = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [showDocumentDialog, setShowDocumentDialog] = useState(false);

  const getFullFileUrl = (fileUrl) => {
    if (!fileUrl) return '';
    if (fileUrl.startsWith('http')) return fileUrl;
    // Les fichiers sont servis via /api/uploads/ pour passer par l'ingress Kubernetes
    // Remplacer /uploads/ par /api/uploads/ si nécessaire
    const cleanUrl = fileUrl.startsWith('/uploads/') ? fileUrl.replace('/uploads/', '/api/uploads/') : `/api${fileUrl}`;
    return `${BACKEND_URL}${cleanUrl}`;
  };

  // Fonction de téléchargement forcé
  const handleDownload = async (doc) => {
    try {
      const fileUrl = getFullFileUrl(doc.file_url);
      const response = await fetch(fileUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.file_name || 'document';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Téléchargement démarré !');
    } catch (error) {
      console.error('Download error:', error);
      // Fallback: ouvrir dans un nouvel onglet
      window.open(getFullFileUrl(doc.file_url), '_blank');
    }
  };

  // Fonction d'ouverture dans nouvel onglet
  const handleOpenNewTab = (doc) => {
    const fileUrl = getFullFileUrl(doc.file_url);
    window.open(fileUrl, '_blank');
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await apiClient.get('/documents/my-documents');
      setDocuments(res.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error('Erreur lors du chargement des documents');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (documentId) => {
    try {
      await apiClient.put(`/documents/${documentId}/mark-read`);
      // Update local state
      setDocuments(prev => prev.map(doc => 
        doc.id === documentId ? { ...doc, is_read: true } : doc
      ));
    } catch (error) {
      // Silently fail if already marked as read
      console.log('Already marked as read or error:', error);
    }
  };

  const openDocument = (document) => {
    setSelectedDocument(document);
    setShowDocumentDialog(true);
    
    // Mark as read when opened
    if (!document.is_read) {
      markAsRead(document.id);
    }
  };

  const getFileIcon = (fileType) => {
    if (!fileType) return <File className="w-6 h-6 text-gray-600" />;
    
    if (fileType === 'image') return <ImageIcon className="w-6 h-6 text-blue-600" />;
    if (fileType === 'pdf') return <FileText className="w-6 h-6 text-red-600" />;
    if (fileType === 'document') return <FileText className="w-6 h-6 text-blue-600" />;
    if (fileType === 'spreadsheet') return <FileText className="w-6 h-6 text-green-600" />;
    if (fileType === 'presentation') return <FileText className="w-6 h-6 text-orange-600" />;
    
    return <File className="w-6 h-6 text-gray-600" />;
  };

  const unreadCount = documents.filter(doc => !doc.is_read).length;

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12">
          <p className="text-center text-gray-500">Chargement des documents...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="bg-teal-50">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-teal-800">📄 Mes Documents</CardTitle>
              <CardDescription>
                Documents envoyés par votre professeur et l'administration
              </CardDescription>
            </div>
            {unreadCount > 0 && (
              <div className="flex items-center gap-2 bg-red-500 text-white px-3 py-1 rounded-full text-sm font-semibold">
                <span>{unreadCount}</span>
                <span>{unreadCount === 1 ? 'nouveau' : 'nouveaux'}</span>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {documents.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucun document reçu</p>
              <p className="text-sm text-gray-400 mt-2">Les documents partagés par votre professeur apparaîtront ici</p>
            </div>
          ) : (
            <div className="space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className={`p-4 border rounded-lg transition hover:shadow-md cursor-pointer ${
                    !doc.is_read ? 'bg-blue-50 border-blue-200' : 'bg-white'
                  }`}
                  onClick={() => openDocument(doc)}
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {getFileIcon(doc.file_type)}
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <h3 className="font-semibold text-gray-900">{doc.title}</h3>
                            {!doc.is_read && (
                              <span className="px-2 py-0.5 bg-red-500 text-white text-xs font-semibold rounded-full">
                                NOUVEAU
                              </span>
                            )}
                          </div>
                          
                          {doc.description && (
                            <p className="text-sm text-gray-600 mt-1 line-clamp-2">{doc.description}</p>
                          )}
                          
                          <div className="flex items-center gap-4 mt-3 text-xs text-gray-500 flex-wrap">
                            <span className="flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {doc.file_name}
                            </span>
                            <span className="flex items-center gap-1">
                              {doc.sender_role === 'admin' ? '👤 Admin KALAMA' : `👨‍🏫 ${doc.sender_name}`}
                            </span>
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {new Date(doc.created_at).toLocaleDateString('fr-FR', {
                                day: '2-digit',
                                month: 'long',
                                year: 'numeric'
                              })}
                            </span>
                          </div>
                        </div>
                        
                        <div className="flex gap-2 flex-shrink-0">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              openDocument(doc);
                            }}
                            className="hover:bg-teal-50"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Ouvrir
                          </Button>
                          <a
                            href={getFullFileUrl(doc.file_url)}
                            download={doc.file_name}
                            onClick={(e) => e.stopPropagation()}
                          >
                            <Button
                              variant="outline"
                              size="sm"
                              className="hover:bg-blue-50"
                            >
                              <Download className="w-4 h-4 mr-1" />
                              Télécharger
                            </Button>
                          </a>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Document Preview Dialog */}
      <Dialog open={showDocumentDialog} onOpenChange={setShowDocumentDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>{selectedDocument?.title}</DialogTitle>
              <a
                href={getFullFileUrl(selectedDocument?.file_url)}
                download={selectedDocument?.file_name}
                onClick={(e) => e.stopPropagation()}
              >
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Télécharger
                </Button>
              </a>
            </div>
          </DialogHeader>
          
          <div className="overflow-auto">
            {selectedDocument?.file_type === 'image' ? (
              <img 
                src={getFullFileUrl(selectedDocument.file_url)} 
                alt={selectedDocument.file_name} 
                className="w-full rounded-lg"
              />
            ) : selectedDocument?.file_type === 'pdf' ? (
              <div className="space-y-4">
                {/* Actions principales bien visibles */}
                <div className="bg-gradient-to-r from-blue-50 to-teal-50 border border-blue-200 rounded-xl p-5">
                  <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="p-3 bg-blue-100 rounded-lg">
                        <FileText className="w-8 h-8 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-bold text-blue-900 text-lg">{selectedDocument?.file_name}</p>
                        <p className="text-sm text-blue-600">Document PDF</p>
                      </div>
                    </div>
                    <div className="flex gap-3 w-full sm:w-auto">
                      <Button 
                        onClick={() => handleOpenNewTab(selectedDocument)}
                        className="flex-1 sm:flex-none bg-teal-600 hover:bg-teal-700 text-white"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Ouvrir
                      </Button>
                      <Button 
                        onClick={() => handleDownload(selectedDocument)}
                        className="flex-1 sm:flex-none bg-blue-600 hover:bg-blue-700 text-white"
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Télécharger
                      </Button>
                    </div>
                  </div>
                </div>
                
                {/* Aperçu du PDF avec iframe - fonctionne dans la plupart des navigateurs modernes */}
                <div className="relative rounded-xl overflow-hidden border-2 border-gray-200 bg-gray-100">
                  <iframe
                    src={getFullFileUrl(selectedDocument?.file_url)}
                    className="w-full h-[55vh]"
                    title={selectedDocument?.file_name}
                    style={{ border: 'none' }}
                  />
                  {/* Message d'aide si le PDF ne s'affiche pas */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-gray-900/80 to-transparent p-4 text-white text-center text-sm">
                    Si le PDF ne s&apos;affiche pas, utilisez les boutons ci-dessus pour l&apos;ouvrir ou le télécharger
                  </div>
                </div>
              </div>
            ) : selectedDocument?.file_type === 'video' ? (
              <video controls className="w-full rounded-lg">
                <source src={getFullFileUrl(selectedDocument.file_url)} />
                Votre navigateur ne supporte pas la lecture vidéo.
              </video>
            ) : selectedDocument?.file_type === 'audio' ? (
              <audio controls className="w-full">
                <source src={getFullFileUrl(selectedDocument.file_url)} />
                Votre navigateur ne supporte pas la lecture audio.
              </audio>
            ) : (
              <div className="p-8">
                <div className="bg-gray-50 rounded-lg p-6 text-center mb-4">
                  <div className="text-6xl mb-4">📄</div>
                  <p className="text-lg font-semibold text-gray-700 mb-2">{selectedDocument?.file_name}</p>
                  <p className="text-sm text-gray-500 mb-4">
                    Envoyé par {selectedDocument?.sender_role === 'admin' ? 'Admin KALAMA' : selectedDocument?.sender_name}
                  </p>
                  {selectedDocument?.description && (
                    <p className="text-sm text-gray-600 mb-4 max-w-xl mx-auto">
                      {selectedDocument.description}
                    </p>
                  )}
                </div>
                <div className="flex justify-center">
                  <a 
                    href={getFullFileUrl(selectedDocument?.file_url)} 
                    download={selectedDocument?.file_name}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 font-semibold"
                  >
                    <Download className="w-5 h-5" />
                    Télécharger le fichier
                  </a>
                </div>
              </div>
            )}
          </div>
          
          {selectedDocument?.description && selectedDocument?.file_type !== 'other' && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">Description :</span> {selectedDocument.description}
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StudentDocuments;
