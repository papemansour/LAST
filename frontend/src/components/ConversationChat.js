import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card } from './ui/card';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Send, Paperclip, X, Download, Eye, Trash2, FileText, Image as ImageIcon, File } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';

const ConversationChat = ({ recipientId, recipientName, currentUserId }) => {
  const [messages, setMessages] = useState([]);
  const [messageContent, setMessageContent] = useState('');
  const [attachedFile, setAttachedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showFileDialog, setShowFileDialog] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    if (recipientId) {
      loadMessages();
    }
  }, [recipientId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const loadMessages = async () => {
    try {
      const res = await apiClient.get(`/messages/conversation/${recipientId}`);
      setMessages(res.data);
    } catch (error) {
      console.error('Error loading messages:', error);
    }
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    // Check file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Fichier trop volumineux (max 10MB)');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await apiClient.post('/messages/upload-attachment', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setAttachedFile({
        file_url: res.data.file_url,
        filename: res.data.filename,
        file_type: res.data.file_type
      });
      toast.success(`Fichier "${file.name}" attaché`);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(error.response?.data?.detail || "Erreur d'upload");
    } finally {
      setUploading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!messageContent.trim() && !attachedFile) {
      toast.error('Écrivez un message ou attachez un fichier');
      return;
    }

    try {
      await apiClient.post('/messages/send', {
        to_user_id: recipientId,
        content: messageContent || '📎 Fichier joint',
        attachment: attachedFile
      });

      setMessageContent('');
      setAttachedFile(null);
      loadMessages();
      toast.success('Message envoyé');
    } catch (error) {
      toast.error("Erreur d'envoi");
    }
  };

  const handleDeleteAttachment = async (messageId) => {
    if (!window.confirm('Supprimer cette pièce jointe ?')) return;

    try {
      await apiClient.delete(`/messages/${messageId}/attachment`);
      toast.success('Pièce jointe supprimée');
      loadMessages();
    } catch (error) {
      toast.error('Erreur de suppression');
    }
  };

  const openFileDialog = (attachment) => {
    setSelectedFile(attachment);
    setShowFileDialog(true);
  };

  const getFileIcon = (fileType) => {
    if (fileType?.startsWith('image/')) return <ImageIcon className="w-5 h-5" />;
    if (fileType?.includes('pdf')) return <FileText className="w-5 h-5 text-red-600" />;
    return <File className="w-5 h-5" />;
  };

  return (
    <div className="flex flex-col h-[600px]">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Aucun message</p>
        ) : (
          messages.map((msg) => {
            const isOwn = msg.from_user_id === currentUserId;
            return (
              <div key={msg.id} className={`flex ${isOwn ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[70%] ${isOwn ? 'bg-teal-600 text-white' : 'bg-white'} rounded-lg p-3 shadow`}>
                  <p className="text-sm">{msg.content}</p>
                  
                  {/* Attachment display */}
                  {msg.attachment && (
                    <div className={`mt-2 p-2 rounded ${isOwn ? 'bg-teal-700' : 'bg-gray-100'} flex items-center justify-between gap-2`}>
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        {getFileIcon(msg.attachment.file_type)}
                        <span className="text-xs truncate">{msg.attachment.filename}</span>
                      </div>
                      <div className="flex gap-1 flex-shrink-0">
                        <button
                          onClick={() => openFileDialog(msg.attachment)}
                          className={`p-1 rounded hover:bg-opacity-80 ${isOwn ? 'hover:bg-teal-800' : 'hover:bg-gray-200'}`}
                          title="Ouvrir"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <a
                          href={msg.attachment.file_url}
                          download={msg.attachment.filename}
                          className={`p-1 rounded hover:bg-opacity-80 ${isOwn ? 'hover:bg-teal-800' : 'hover:bg-gray-200'}`}
                          title="Télécharger"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                        {isOwn && (
                          <button
                            onClick={() => handleDeleteAttachment(msg.id)}
                            className="p-1 rounded hover:bg-teal-800"
                            title="Supprimer"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                  
                  <p className="text-xs mt-1 opacity-70">
                    {new Date(msg.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <form onSubmit={handleSendMessage} className="p-4 bg-white border-t">
        {attachedFile && (
          <div className="mb-2 p-2 bg-teal-50 rounded flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getFileIcon(attachedFile.file_type)}
              <span className="text-sm">{attachedFile.filename}</span>
            </div>
            <button
              type="button"
              onClick={() => setAttachedFile(null)}
              className="text-red-600 hover:text-red-800"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
        
        <div className="flex gap-2">
          <label className="cursor-pointer">
            <input
              type="file"
              className="hidden"
              onChange={handleFileSelect}
              disabled={uploading}
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.gif"
            />
            <div className={`p-2 border rounded-lg ${uploading ? 'opacity-50' : 'hover:bg-gray-50'}`}>
              <Paperclip className="w-5 h-5 text-gray-600" />
            </div>
          </label>
          
          <Input
            value={messageContent}
            onChange={(e) => setMessageContent(e.target.value)}
            placeholder="Écrivez votre message..."
            className="flex-1"
            disabled={uploading}
          />
          
          <Button type="submit" disabled={uploading} className="bg-teal-600 hover:bg-teal-700">
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>

      {/* File preview dialog */}
      <Dialog open={showFileDialog} onOpenChange={setShowFileDialog}>
        <DialogContent className="max-w-4xl max-h-[90vh]">
          <DialogHeader>
            <DialogTitle>{selectedFile?.filename}</DialogTitle>
          </DialogHeader>
          <div className="overflow-auto">
            {selectedFile?.file_type?.startsWith('image/') ? (
              <img src={selectedFile.file_url} alt={selectedFile.filename} className="w-full" />
            ) : (
              <iframe
                src={selectedFile?.file_url}
                className="w-full h-[70vh]"
                title={selectedFile?.filename}
              />
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ConversationChat;
