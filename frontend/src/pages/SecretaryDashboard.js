import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { LogOut, Calendar, FileText, MessageCircle, Plus, Trash2, Edit, Save, X } from 'lucide-react';

const SecretaryDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Meetings state
  const [meetings, setMeetings] = useState([]);
  const [newMeeting, setNewMeeting] = useState({
    title: '',
    date: '',
    time: '',
    attendees: '',
    notes: '',
    meetingLink: '',
    notifyProfs: [],
    notifyAdmin: false
  });
  
  // Notes state
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({
    title: '',
    content: ''
  });
  const [editingNote, setEditingNote] = useState(null);
  
  // Messages state
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState({
    recipient: '',
    subject: '',
    content: ''
  });
  
  // Comptes rendus prof state
  const [profReports, setProfReports] = useState([]);
  const [newReport, setNewReport] = useState({
    profName: '',
    date: '',
    content: '',
    notes: ''
  });

  useEffect(() => {
    fetchUserData();
    loadLocalData();
  }, []);

  const fetchUserData = async () => {
    try {
      const res = await apiClient.get('/auth/me');
      if (res.data.role !== 'secretary') {
        toast.error('Accès non autorisé');
        navigate('/');
        return;
      }
      setUser(res.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      toast.error('Session expirée');
      navigate('/secretary-login');
    } finally {
      setLoading(false);
    }
  };

  // Charger données depuis localStorage
  const loadLocalData = () => {
    const savedMeetings = localStorage.getItem('secretary_meetings');
    const savedNotes = localStorage.getItem('secretary_notes');
    const savedMessages = localStorage.getItem('secretary_messages');
    
    if (savedMeetings) setMeetings(JSON.parse(savedMeetings));
    if (savedNotes) setNotes(JSON.parse(savedNotes));
    if (savedMessages) setMessages(JSON.parse(savedMessages));
  };

  // Sauvegarder dans localStorage
  const saveMeetings = (data) => {
    localStorage.setItem('secretary_meetings', JSON.stringify(data));
    setMeetings(data);
  };

  const saveNotes = (data) => {
    localStorage.setItem('secretary_notes', JSON.stringify(data));
    setNotes(data);
  };

  const saveMessages = (data) => {
    localStorage.setItem('secretary_messages', JSON.stringify(data));
    setMessages(data);
  };

  // Meetings handlers
  const handleAddMeeting = () => {
    if (!newMeeting.title || !newMeeting.date || !newMeeting.time) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    const meeting = {
      id: Date.now(),
      ...newMeeting,
      createdAt: new Date().toISOString()
    };

    saveMeetings([...meetings, meeting]);
    setNewMeeting({ title: '', date: '', time: '', attendees: '', notes: '' });
    toast.success('Réunion ajoutée !');
  };

  const handleDeleteMeeting = (id) => {
    if (window.confirm('Supprimer cette réunion ?')) {
      saveMeetings(meetings.filter(m => m.id !== id));
      toast.success('Réunion supprimée');
    }
  };

  // Notes handlers
  const handleAddNote = () => {
    if (!newNote.title || !newNote.content) {
      toast.error('Veuillez remplir le titre et le contenu');
      return;
    }

    const note = {
      id: Date.now(),
      ...newNote,
      createdAt: new Date().toISOString()
    };

    saveNotes([...notes, note]);
    setNewNote({ title: '', content: '' });
    toast.success('Note ajoutée !');
  };

  const handleUpdateNote = () => {
    if (!editingNote.title || !editingNote.content) {
      toast.error('Veuillez remplir le titre et le contenu');
      return;
    }

    saveNotes(notes.map(n => n.id === editingNote.id ? editingNote : n));
    setEditingNote(null);
    toast.success('Note mise à jour !');
  };

  const handleDeleteNote = (id) => {
    if (window.confirm('Supprimer cette note ?')) {
      saveNotes(notes.filter(n => n.id !== id));
      toast.success('Note supprimée');
    }
  };

  // Messages handler
  const handleSendMessage = async () => {
    if (!newMessage.recipient || !newMessage.subject || !newMessage.content) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }

    const message = {
      id: Date.now(),
      ...newMessage,
      sentAt: new Date().toISOString(),
      status: 'envoyé'
    };

    saveMessages([...messages, message]);
    setNewMessage({ recipient: '', subject: '', content: '' });
    toast.success('Message envoyé !');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    toast.success('Déconnexion réussie');
    navigate('/secretary-login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      {/* Header */}
      <header className="bg-white border-b border-purple-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-purple-600">Espace Secrétaire</h1>
            <p className="text-sm text-gray-600">
              Bienvenue, {user?.first_name}
            </p>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="border-purple-200 hover:bg-purple-50"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Déconnexion
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs defaultValue="meetings" className="space-y-6">
          <TabsList className="bg-white border border-purple-100 p-1 rounded-lg">
            <TabsTrigger value="meetings" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Calendar className="w-4 h-4 mr-2" />
              Réunions
            </TabsTrigger>
            <TabsTrigger value="notes" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Notes
            </TabsTrigger>
            <TabsTrigger value="messages" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <MessageCircle className="w-4 h-4 mr-2" />
              Messages
            </TabsTrigger>
          </TabsList>

          {/* Meetings Tab */}
          <TabsContent value="meetings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Planifier une réunion
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre *</label>
                    <Input
                      value={newMeeting.title}
                      onChange={(e) => setNewMeeting({...newMeeting, title: e.target.value})}
                      placeholder="Ex: Réunion équipe pédagogique"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Participants</label>
                    <Input
                      value={newMeeting.attendees}
                      onChange={(e) => setNewMeeting({...newMeeting, attendees: e.target.value})}
                      placeholder="Ex: Admin, Prof1, Prof2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Date *</label>
                    <Input
                      type="date"
                      value={newMeeting.date}
                      onChange={(e) => setNewMeeting({...newMeeting, date: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Heure *</label>
                    <Input
                      type="time"
                      value={newMeeting.time}
                      onChange={(e) => setNewMeeting({...newMeeting, time: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Notes</label>
                  <Textarea
                    value={newMeeting.notes}
                    onChange={(e) => setNewMeeting({...newMeeting, notes: e.target.value})}
                    placeholder="Ordre du jour, points à discuter..."
                    rows={3}
                  />
                </div>
                <Button onClick={handleAddMeeting} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter la réunion
                </Button>
              </CardContent>
            </Card>

            {/* Meetings List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Réunions planifiées ({meetings.length})</h3>
              {meetings.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucune réunion planifiée
                  </CardContent>
                </Card>
              ) : (
                meetings.map(meeting => (
                  <Card key={meeting.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg mb-2">{meeting.title}</h4>
                          <div className="space-y-1 text-sm text-gray-600">
                            <p>📅 {new Date(meeting.date).toLocaleDateString('fr-FR')} à {meeting.time}</p>
                            {meeting.attendees && <p>👥 {meeting.attendees}</p>}
                            {meeting.notes && <p className="mt-2 text-gray-700">📝 {meeting.notes}</p>}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteMeeting(meeting.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Notes Tab */}
          <TabsContent value="notes" className="space-y-6">
            {!editingNote ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    Nouvelle note
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre *</label>
                    <Input
                      value={newNote.title}
                      onChange={(e) => setNewNote({...newNote, title: e.target.value})}
                      placeholder="Titre de la note"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Contenu *</label>
                    <Textarea
                      value={newNote.content}
                      onChange={(e) => setNewNote({...newNote, content: e.target.value})}
                      placeholder="Contenu de la note..."
                      rows={5}
                    />
                  </div>
                  <Button onClick={handleAddNote} className="bg-purple-600 hover:bg-purple-700">
                    <Plus className="w-4 h-4 mr-2" />
                    Ajouter la note
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Edit className="w-5 h-5" />
                    Modifier la note
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre *</label>
                    <Input
                      value={editingNote.title}
                      onChange={(e) => setEditingNote({...editingNote, title: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Contenu *</label>
                    <Textarea
                      value={editingNote.content}
                      onChange={(e) => setEditingNote({...editingNote, content: e.target.value})}
                      rows={5}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleUpdateNote} className="bg-purple-600 hover:bg-purple-700">
                      <Save className="w-4 h-4 mr-2" />
                      Enregistrer
                    </Button>
                    <Button onClick={() => setEditingNote(null)} variant="outline">
                      <X className="w-4 h-4 mr-2" />
                      Annuler
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Notes List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Mes notes ({notes.length})</h3>
              {notes.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucune note enregistrée
                  </CardContent>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {notes.map(note => (
                    <Card key={note.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="pt-6">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-semibold text-lg">{note.title}</h4>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingNote(note)}
                              className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteNote(note.id)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{note.content}</p>
                        <p className="text-xs text-gray-400 mt-3">
                          {new Date(note.createdAt).toLocaleDateString('fr-FR')}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Messages Tab */}
          <TabsContent value="messages" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5" />
                  Envoyer un message
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Destinataire *</label>
                  <Input
                    value={newMessage.recipient}
                    onChange={(e) => setNewMessage({...newMessage, recipient: e.target.value})}
                    placeholder="Email ou nom du destinataire"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Sujet *</label>
                  <Input
                    value={newMessage.subject}
                    onChange={(e) => setNewMessage({...newMessage, subject: e.target.value})}
                    placeholder="Sujet du message"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Message *</label>
                  <Textarea
                    value={newMessage.content}
                    onChange={(e) => setNewMessage({...newMessage, content: e.target.value})}
                    placeholder="Votre message..."
                    rows={5}
                  />
                </div>
                <Button onClick={handleSendMessage} className="bg-purple-600 hover:bg-purple-700">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Envoyer le message
                </Button>
              </CardContent>
            </Card>

            {/* Messages History */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Messages envoyés ({messages.length})</h3>
              {messages.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucun message envoyé
                  </CardContent>
                </Card>
              ) : (
                messages.map(message => (
                  <Card key={message.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold">À: {message.recipient}</p>
                          <p className="text-sm text-gray-600 font-medium">{message.subject}</p>
                        </div>
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                          {message.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-3 whitespace-pre-wrap">{message.content}</p>
                      <p className="text-xs text-gray-400 mt-3">
                        {new Date(message.sentAt).toLocaleString('fr-FR')}
                      </p>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SecretaryDashboard;
