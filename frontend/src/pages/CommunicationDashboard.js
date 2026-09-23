import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { useAuth } from '../hooks/useAuth';
import { 
  LogOut, 
  Megaphone, 
  Calendar, 
  BarChart3, 
  Plus, 
  Edit, 
  Trash2, 
  Users,
  FileText,
  Clock,
  MessageSquare,
  BookOpen,
  DollarSign,
  Send,
  Check,
  Plane,
  StickyNote
} from 'lucide-react';

// Codes personnels des chargés de com
const COM_CODES = {
  'MBM': { name: 'MBM', fullName: 'Chargé(e) de Com MBM' },
  'FZT': { name: 'FZT', fullName: 'Chargé(e) de Com FZT' }
};

// Time slots for availability
const TIME_SLOTS = [
  '08:00', '09:00', '10:00', '11:00', '12:00',
  '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00'
];

const DAYS = [
  { key: 'monday', label: 'Lundi' },
  { key: 'tuesday', label: 'Mardi' },
  { key: 'wednesday', label: 'Mercredi' },
  { key: 'thursday', label: 'Jeudi' },
  { key: 'friday', label: 'Vendredi' },
  { key: 'saturday', label: 'Samedi' },
  { key: 'sunday', label: 'Dimanche' }
];

const CommunicationDashboard = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('news');
  
  // Code personnel verification
  const [showCodeModal, setShowCodeModal] = useState(true);
  const [personalCode, setPersonalCode] = useState('');
  const [verifiedCode, setVerifiedCode] = useState(null);
  const [codeError, setCodeError] = useState('');
  
  // News state
  const [news, setNews] = useState([]);
  const [showNewsModal, setShowNewsModal] = useState(false);
  const [editingNews, setEditingNews] = useState(null);
  const [newsForm, setNewsForm] = useState({
    title: '',
    content: '',
    category: 'general',
    image_url: '',
    is_published: true
  });
  
  // Stats
  const [stats, setStats] = useState({
    totalStudents: 0,
    totalTeachers: 0,
    totalNews: 0
  });
  
  // Availability state (like teachers)
  const [availability, setAvailability] = useState({});
  const [savingAvailability, setSavingAvailability] = useState(false);
  
  // Payslips/Balance state (like teachers)
  const [balanceInfo, setBalanceInfo] = useState({
    pendingAmount: 0,
    paidAmount: 0,
    totalHours: 0,
    payments: []
  });
  
  // Messages state
  const [messages, setMessages] = useState([]);
  const [showMessageModal, setShowMessageModal] = useState(false);
  const [messageForm, setMessageForm] = useState({
    recipient_code: '',
    content: ''
  });
  const [unreadCount, setUnreadCount] = useState(0);
  const [teachers, setTeachers] = useState([]);
  
  // Notes state
  const [notes, setNotes] = useState([]);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteForm, setNoteForm] = useState({ title: '', content: '' });
  
  // Leave/Congés state
  const [leaves, setLeaves] = useState([]);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveForm, setLeaveForm] = useState({
    start_date: '',
    end_date: '',
    reason: '',
    status: 'pending'
  });

  useEffect(() => {
    // Check if code was already verified in this session
    const savedCode = sessionStorage.getItem('com_code');
    if (savedCode && COM_CODES[savedCode]) {
      setVerifiedCode(savedCode);
      setShowCodeModal(false);
      fetchData(savedCode);
    }
  }, []);

  const verifyCode = () => {
    const code = personalCode.toUpperCase().trim();
    if (COM_CODES[code]) {
      setVerifiedCode(code);
      setShowCodeModal(false);
      setCodeError('');
      sessionStorage.setItem('com_code', code);
      fetchData(code);
      toast.success(`Bienvenue ${COM_CODES[code].fullName} !`);
    } else {
      setCodeError('Code invalide');
    }
  };

  const fetchData = async (code) => {
    try {
      const [userRes, newsRes, statsRes, availRes, balanceRes, messagesRes, unreadRes, teachersRes, notesRes, leavesRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/news/all'),
        apiClient.get('/communication/stats').catch(() => ({ data: {} })),
        apiClient.get(`/communication/my-availability/${code}`).catch(() => ({ data: { availability: {} } })),
        apiClient.get(`/communication/balance/${code}`).catch(() => ({ data: { pendingAmount: 0, paidAmount: 0, payments: [] } })),
        apiClient.get(`/communication/messages/${code}`).catch(() => ({ data: [] })),
        apiClient.get(`/communication/unread-count/${code}`).catch(() => ({ data: { unread_count: 0 } })),
        apiClient.get('/admin/all-teachers-detailed').catch(() => ({ data: [] })),
        apiClient.get(`/communication/notes/${code}`).catch(() => ({ data: [] })),
        apiClient.get(`/communication/leaves/${code}`).catch(() => ({ data: [] }))
      ]);
      
      setUser(userRes.data);
      setNews(newsRes.data || []);
      setStats(statsRes.data || {});
      setAvailability(availRes.data?.availability || {});
      setBalanceInfo(balanceRes.data || { pendingAmount: 0, paidAmount: 0, payments: [] });
      setMessages(messagesRes.data || []);
      setUnreadCount(unreadRes.data?.unread_count || 0);
      setTeachers(teachersRes.data || []);
      setNotes(notesRes.data || []);
      setLeaves(leavesRes.data || []);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur de chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('com_code');
    logout();
    navigate('/login');
  };

  // News handlers
  const handleSaveNews = async () => {
    try {
      if (editingNews) {
        await apiClient.put(`/news/${editingNews.id}`, newsForm);
        toast.success('Actualité mise à jour');
      } else {
        await apiClient.post('/news', {...newsForm, created_by_code: verifiedCode});
        toast.success('Actualité créée');
      }
      setShowNewsModal(false);
      setEditingNews(null);
      setNewsForm({ title: '', content: '', category: 'general', image_url: '', is_published: true });
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  const handleDeleteNews = async (id) => {
    if (!window.confirm('Supprimer cette actualité ?')) return;
    try {
      await apiClient.delete(`/news/${id}`);
      toast.success('Actualité supprimée');
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const openEditNews = (newsItem) => {
    setEditingNews(newsItem);
    setNewsForm({
      title: newsItem.title,
      content: newsItem.content,
      category: newsItem.category || 'general',
      image_url: newsItem.image_url || '',
      is_published: newsItem.is_published !== false
    });
    setShowNewsModal(true);
  };

  // Availability handlers (like teachers)
  const toggleSlot = (day, time) => {
    setAvailability(prev => {
      const daySlots = prev[day] || [];
      if (daySlots.includes(time)) {
        return { ...prev, [day]: daySlots.filter(t => t !== time) };
      } else {
        return { ...prev, [day]: [...daySlots, time].sort() };
      }
    });
  };

  const saveAvailability = async () => {
    setSavingAvailability(true);
    try {
      await apiClient.post('/communication/set-availability', {
        com_code: verifiedCode,
        availability: availability
      });
      toast.success('Disponibilités enregistrées');
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setSavingAvailability(false);
    }
  };

  // Messages handlers
  const handleSendMessage = async () => {
    if (!messageForm.recipient_code || !messageForm.content) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }
    try {
      await apiClient.post('/communication/messages', {
        sender_code: verifiedCode,
        sender_name: COM_CODES[verifiedCode]?.fullName || verifiedCode,
        recipient_code: messageForm.recipient_code,
        content: messageForm.content
      });
      toast.success('Message envoyé');
      setShowMessageModal(false);
      setMessageForm({ recipient_code: '', content: '' });
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de l\'envoi');
    }
  };

  const markAsRead = async (messageId) => {
    try {
      await apiClient.put(`/communication/messages/${messageId}/read`);
      fetchData(verifiedCode);
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  // Notes handlers
  const handleSaveNote = async () => {
    try {
      await apiClient.post('/communication/notes', {
        com_code: verifiedCode,
        ...noteForm
      });
      toast.success('Note enregistrée');
      setShowNoteModal(false);
      setNoteForm({ title: '', content: '' });
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const handleDeleteNote = async (id) => {
    try {
      await apiClient.delete(`/communication/notes/${id}`);
      toast.success('Note supprimée');
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Leave handlers
  const handleSaveLeave = async () => {
    try {
      await apiClient.post('/communication/leaves', {
        com_code: verifiedCode,
        ...leaveForm
      });
      toast.success('Demande de congé envoyée');
      setShowLeaveModal(false);
      setLeaveForm({ start_date: '', end_date: '', reason: '', status: 'pending' });
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de l\'envoi');
    }
  };

  // Code verification modal
  if (showCodeModal) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center">
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Megaphone className="h-8 w-8 text-purple-600" />
            </div>
            <CardTitle className="text-purple-700">Espace Communication</CardTitle>
            <CardDescription>Entrez votre code personnel pour accéder à votre espace</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Code Personnel</Label>
              <Input
                value={personalCode}
                onChange={(e) => {
                  setPersonalCode(e.target.value.toUpperCase());
                  setCodeError('');
                }}
                placeholder=""
                className="text-center text-2xl font-bold tracking-widest"
                maxLength={3}
                onKeyPress={(e) => e.key === 'Enter' && verifyCode()}
              />
              {codeError && (
                <p className="text-red-500 text-sm mt-2 text-center">{codeError}</p>
              )}
            </div>
            <Button 
              onClick={verifyCode}
              className="w-full bg-purple-600 hover:bg-purple-700"
              disabled={personalCode.length < 3}
            >
              Accéder à mon espace
            </Button>
            <Button 
              variant="outline"
              onClick={handleLogout}
              className="w-full"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Déconnexion
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-purple-700">MYKALAMA - Communication</h1>
            <p className="text-sm text-gray-600">
              Espace {COM_CODES[verifiedCode]?.fullName || 'Chargé(e) de Com'}
              <span className="ml-2 px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full text-xs font-bold">
                {verifiedCode}
              </span>
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">
              {user?.first_name} {user?.last_name}
            </span>
            <Button 
              variant="outline" 
              onClick={handleLogout}
              className="border-purple-300 text-purple-600 hover:bg-purple-50"
            >
              <LogOut className="h-4 w-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <Card className="bg-white border-purple-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <FileText className="h-5 w-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-purple-700">{news.length}</p>
                  <p className="text-xs text-gray-500">Actualités</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-green-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <DollarSign className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-700">{balanceInfo.pendingAmount || 0}€</p>
                  <p className="text-xs text-gray-500">Solde à venir</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-blue-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-blue-700">{stats.totalStudents || 0}</p>
                  <p className="text-xs text-gray-500">Étudiants</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-orange-100 cursor-pointer hover:shadow-md" onClick={() => setActiveTab('messages')}>
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg relative">
                  <MessageSquare className="h-5 w-5 text-orange-600" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                      {unreadCount}
                    </span>
                  )}
                </div>
                <div>
                  <p className="text-2xl font-bold text-orange-700">{messages.length}</p>
                  <p className="text-xs text-gray-500">Messages</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-white border-yellow-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Plane className="h-5 w-5 text-yellow-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-yellow-700">{leaves.filter(l => l.status === 'approved').length}</p>
                  <p className="text-xs text-gray-500">Congés</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="bg-white border border-purple-100 p-1 flex-wrap h-auto gap-1">
            <TabsTrigger value="news" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Megaphone className="h-4 w-4 mr-2" />
              Actualités
            </TabsTrigger>
            <TabsTrigger value="availability" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Calendar className="h-4 w-4 mr-2" />
              Disponibilités
            </TabsTrigger>
            <TabsTrigger value="balance" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <DollarSign className="h-4 w-4 mr-2" />
              Soldes
            </TabsTrigger>
            <TabsTrigger value="messages" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white relative">
              <MessageSquare className="h-4 w-4 mr-2" />
              Messages
              {unreadCount > 0 && <span className="ml-1 bg-red-500 text-white text-xs rounded-full px-1.5">{unreadCount}</span>}
            </TabsTrigger>
            <TabsTrigger value="notes" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <StickyNote className="h-4 w-4 mr-2" />
              Notes
            </TabsTrigger>
            <TabsTrigger value="leaves" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Plane className="h-4 w-4 mr-2" />
              Congés
            </TabsTrigger>
            <TabsTrigger value="kalamatheque" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <BookOpen className="h-4 w-4 mr-2" />
              Kalamathèque
            </TabsTrigger>
          </TabsList>

          {/* NEWS TAB */}
          <TabsContent value="news">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Gestion des Actualités</CardTitle>
                  <CardDescription>Créez et gérez les actualités de la plateforme</CardDescription>
                </div>
                <Button onClick={() => { setEditingNews(null); setNewsForm({ title: '', content: '', category: 'general', image_url: '', is_published: true }); setShowNewsModal(true); }} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Nouvelle Actualité
                </Button>
              </CardHeader>
              <CardContent>
                {news.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucune actualité pour le moment</p>
                ) : (
                  <div className="space-y-4">
                    {news.map((item) => (
                      <div key={item.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow bg-white">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold text-lg">{item.title}</h3>
                              <span className={`px-2 py-0.5 text-xs rounded-full ${item.is_published !== false ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                                {item.is_published !== false ? 'Publié' : 'Brouillon'}
                              </span>
                            </div>
                            <p className="text-gray-600 text-sm line-clamp-2">{item.content}</p>
                            <p className="text-xs text-gray-400 mt-2">{new Date(item.created_at).toLocaleDateString('fr-FR')}</p>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button size="sm" variant="outline" onClick={() => openEditNews(item)}><Edit className="h-4 w-4" /></Button>
                            <Button size="sm" variant="outline" className="text-red-600 hover:bg-red-50" onClick={() => handleDeleteNews(item.id)}><Trash2 className="h-4 w-4" /></Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* AVAILABILITY TAB */}
          <TabsContent value="availability">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Mes Disponibilités - {verifiedCode}</CardTitle>
                  <CardDescription>Sélectionnez vos créneaux disponibles pour chaque jour</CardDescription>
                </div>
                <Button onClick={saveAvailability} className="bg-purple-600 hover:bg-purple-700" disabled={savingAvailability}>
                  {savingAvailability ? 'Enregistrement...' : 'Enregistrer'}
                </Button>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        <th className="p-2 border bg-purple-50 text-purple-700 font-semibold">Horaire</th>
                        {DAYS.map(day => (<th key={day.key} className="p-2 border bg-purple-50 text-purple-700 font-semibold">{day.label}</th>))}
                      </tr>
                    </thead>
                    <tbody>
                      {TIME_SLOTS.map(time => (
                        <tr key={time}>
                          <td className="p-2 border text-center font-medium text-gray-600">{time}</td>
                          {DAYS.map(day => {
                            const isSelected = (availability[day.key] || []).includes(time);
                            return (
                              <td key={day.key} className={`p-2 border text-center cursor-pointer transition-colors ${isSelected ? 'bg-purple-500 text-white hover:bg-purple-600' : 'bg-white hover:bg-purple-100'}`} onClick={() => toggleSlot(day.key, time)}>
                                {isSelected && <Check className="h-4 w-4 mx-auto" />}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* BALANCE/PAYSLIPS TAB (like teachers) */}
          <TabsContent value="balance">
            <Card>
              <CardHeader>
                <CardTitle className="text-purple-700">Mes Soldes</CardTitle>
                <CardDescription>Consultez vos paiements et soldes à venir</CardDescription>
              </CardHeader>
              <CardContent>
                {/* Balance Summary */}
                <div className="grid md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-gradient-to-br from-green-100 to-green-50 rounded-lg p-4 text-center">
                    <p className="text-3xl font-bold text-green-700">{balanceInfo.pendingAmount || 0} €</p>
                    <p className="text-sm text-green-600">Solde à venir</p>
                  </div>
                  <div className="bg-gradient-to-br from-blue-100 to-blue-50 rounded-lg p-4 text-center">
                    <p className="text-3xl font-bold text-blue-700">{balanceInfo.paidAmount || 0} €</p>
                    <p className="text-sm text-blue-600">Total payé</p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-100 to-purple-50 rounded-lg p-4 text-center">
                    <p className="text-3xl font-bold text-purple-700">{balanceInfo.totalHours || 0}h</p>
                    <p className="text-sm text-purple-600">Heures totales</p>
                  </div>
                </div>

                {/* Payment History */}
                <h3 className="font-semibold text-purple-700 mb-3">Historique des paiements</h3>
                {balanceInfo.payments && balanceInfo.payments.length > 0 ? (
                  <div className="space-y-3">
                    {balanceInfo.payments.map((payment, idx) => (
                      <div key={idx} className={`flex items-center justify-between p-4 rounded-lg border ${payment.status === 'paid' ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                        <div>
                          <p className="font-semibold">{payment.month} {payment.year}</p>
                          <p className="text-sm text-gray-600">{payment.notes || 'Paiement'}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-lg">{payment.amount} €</p>
                          <span className={`px-2 py-1 text-xs rounded-full ${payment.status === 'paid' ? 'bg-green-200 text-green-800' : 'bg-yellow-200 text-yellow-800'}`}>
                            {payment.status === 'paid' ? 'Payé' : 'En attente'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-gray-500 py-8">Aucun paiement enregistré</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* MESSAGES TAB */}
          <TabsContent value="messages">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Messages Internes</CardTitle>
                  <CardDescription>Communiquez avec l'équipe</CardDescription>
                </div>
                <Button onClick={() => setShowMessageModal(true)} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Nouveau Message
                </Button>
              </CardHeader>
              <CardContent>
                {messages.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucun message</p>
                ) : (
                  <div className="space-y-3">
                    {messages.map(msg => {
                      const isSent = msg.sender_code === verifiedCode;
                      const isUnread = !msg.is_read && !isSent;
                      return (
                        <div key={msg.id} className={`p-4 rounded-lg border ${isSent ? 'bg-purple-50 border-purple-200 ml-8' : isUnread ? 'bg-blue-50 border-blue-300' : 'bg-gray-50 border-gray-200 mr-8'}`} onClick={() => isUnread && markAsRead(msg.id)}>
                          <div className="flex justify-between items-start mb-2">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-0.5 text-xs rounded-full font-bold ${msg.sender_code === 'ADMIN' ? 'bg-red-100 text-red-700' : msg.sender_code === 'SECRETARY' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                                {msg.sender_code}
                              </span>
                              <span className="text-sm text-gray-600">{msg.sender_name}</span>
                              {isUnread && <span className="w-2 h-2 bg-blue-500 rounded-full"></span>}
                            </div>
                            <span className="text-xs text-gray-400">{new Date(msg.created_at).toLocaleString('fr-FR')}</span>
                          </div>
                          <p className="text-gray-700">{msg.content}</p>
                          <p className="text-xs text-gray-400 mt-2">→ {msg.recipient_code}</p>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* NOTES TAB */}
          <TabsContent value="notes">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Mes Notes</CardTitle>
                  <CardDescription>Gérez vos notes personnelles</CardDescription>
                </div>
                <Button onClick={() => setShowNoteModal(true)} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Nouvelle Note
                </Button>
              </CardHeader>
              <CardContent>
                {notes.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucune note</p>
                ) : (
                  <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {notes.map(note => (
                      <div key={note.id} className="border rounded-lg p-4 bg-yellow-50 border-yellow-200 hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-semibold text-yellow-800">{note.title}</h3>
                          <Button size="sm" variant="ghost" className="text-red-600" onClick={() => handleDeleteNote(note.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                        <p className="text-gray-700 text-sm whitespace-pre-wrap">{note.content}</p>
                        <p className="text-xs text-gray-400 mt-2">{new Date(note.created_at).toLocaleDateString('fr-FR')}</p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* LEAVES/CONGÉS TAB */}
          <TabsContent value="leaves">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Mes Congés</CardTitle>
                  <CardDescription>Gérez vos demandes de congés</CardDescription>
                </div>
                <Button onClick={() => setShowLeaveModal(true)} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="h-4 w-4 mr-2" />
                  Demander un congé
                </Button>
              </CardHeader>
              <CardContent>
                {leaves.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucune demande de congé</p>
                ) : (
                  <div className="space-y-3">
                    {leaves.map(leave => (
                      <div key={leave.id} className={`flex items-center justify-between p-4 rounded-lg border ${leave.status === 'approved' ? 'bg-green-50 border-green-200' : leave.status === 'rejected' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}`}>
                        <div>
                          <p className="font-semibold">
                            {new Date(leave.start_date).toLocaleDateString('fr-FR')} - {new Date(leave.end_date).toLocaleDateString('fr-FR')}
                          </p>
                          <p className="text-sm text-gray-600">{leave.reason}</p>
                        </div>
                        <span className={`px-3 py-1 text-sm rounded-full font-medium ${leave.status === 'approved' ? 'bg-green-200 text-green-800' : leave.status === 'rejected' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'}`}>
                          {leave.status === 'approved' ? 'Approuvé' : leave.status === 'rejected' ? 'Refusé' : 'En attente'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* KALAMATHEQUE TAB */}
          <TabsContent value="kalamatheque">
            <Card>
              <CardHeader>
                <CardTitle className="text-purple-700">Kalamathèque</CardTitle>
                <CardDescription>Accédez à la bibliothèque en ligne</CardDescription>
              </CardHeader>
              <CardContent className="text-center py-8">
                <BookOpen className="h-16 w-16 text-purple-300 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">Accédez à la Kalamathèque, notre bibliothèque de livres en anglais</p>
                <p className="text-sm text-gray-500 mb-4">Code d'accès: <span className="font-mono font-bold">Digika</span></p>
                <Button onClick={() => window.open('/kalamatheque-access', '_blank')} className="bg-purple-600 hover:bg-purple-700">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Ouvrir la Kalamathèque
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* News Modal */}
      <Dialog open={showNewsModal} onOpenChange={setShowNewsModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">{editingNews ? 'Modifier l\'actualité' : 'Nouvelle Actualité'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div><Label>Titre *</Label><Input value={newsForm.title} onChange={(e) => setNewsForm({...newsForm, title: e.target.value})} placeholder="Titre" /></div>
            <div><Label>Contenu *</Label><Textarea value={newsForm.content} onChange={(e) => setNewsForm({...newsForm, content: e.target.value})} rows={4} /></div>
            <div><Label>Catégorie</Label>
              <Select value={newsForm.category} onValueChange={(v) => setNewsForm({...newsForm, category: v})}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">Général</SelectItem>
                  <SelectItem value="event">Événement</SelectItem>
                  <SelectItem value="promotion">Promotion</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <input type="checkbox" id="is_published" checked={newsForm.is_published} onChange={(e) => setNewsForm({...newsForm, is_published: e.target.checked})} className="rounded" />
              <Label htmlFor="is_published">Publier immédiatement</Label>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowNewsModal(false)}>Annuler</Button>
            <Button onClick={handleSaveNews} className="bg-purple-600 hover:bg-purple-700" disabled={!newsForm.title || !newsForm.content}>
              {editingNews ? 'Mettre à jour' : 'Créer'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Message Modal */}
      <Dialog open={showMessageModal} onOpenChange={setShowMessageModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">Nouveau Message</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Destinataire *</Label>
              <Select value={messageForm.recipient_code} onValueChange={(v) => setMessageForm({...messageForm, recipient_code: v})}>
                <SelectTrigger><SelectValue placeholder="Choisir..." /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="header-com" disabled className="font-bold text-purple-700">— Chargés de Com —</SelectItem>
                  {verifiedCode !== 'MBM' && <SelectItem value="MBM">MBM</SelectItem>}
                  {verifiedCode !== 'FZT' && <SelectItem value="FZT">FZT</SelectItem>}
                  <SelectItem value="header-staff" disabled className="font-bold text-blue-700">— Staff —</SelectItem>
                  <SelectItem value="SECRETARY">Secrétaire</SelectItem>
                  <SelectItem value="ADMIN">Admin</SelectItem>
                  <SelectItem value="header-levels" disabled className="font-bold text-green-700">— Niveaux Étudiants —</SelectItem>
                  <SelectItem value="LEVEL_KKID">K-Kid (Enfants)</SelectItem>
                  <SelectItem value="LEVEL_BEGINNER">Débutant</SelectItem>
                  <SelectItem value="LEVEL_INTERMEDIATE">Intermédiaire</SelectItem>
                  <SelectItem value="LEVEL_ADVANCED">Avancé/Pro</SelectItem>
                  <SelectItem value="header-teachers" disabled className="font-bold text-orange-700">— Professeurs —</SelectItem>
                  {teachers.map(t => (
                    <SelectItem key={t.id} value={`TEACHER_${t.id}`}>{t.first_name} {t.last_name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div><Label>Message *</Label><Textarea value={messageForm.content} onChange={(e) => setMessageForm({...messageForm, content: e.target.value})} rows={4} /></div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowMessageModal(false)}>Annuler</Button>
            <Button onClick={handleSendMessage} className="bg-purple-600 hover:bg-purple-700" disabled={!messageForm.recipient_code || !messageForm.content}>
              <Send className="h-4 w-4 mr-2" />Envoyer
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Note Modal */}
      <Dialog open={showNoteModal} onOpenChange={setShowNoteModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">Nouvelle Note</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div><Label>Titre</Label><Input value={noteForm.title} onChange={(e) => setNoteForm({...noteForm, title: e.target.value})} /></div>
            <div><Label>Contenu *</Label><Textarea value={noteForm.content} onChange={(e) => setNoteForm({...noteForm, content: e.target.value})} rows={4} /></div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowNoteModal(false)}>Annuler</Button>
            <Button onClick={handleSaveNote} className="bg-purple-600 hover:bg-purple-700" disabled={!noteForm.content}>Enregistrer</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Leave Modal */}
      <Dialog open={showLeaveModal} onOpenChange={setShowLeaveModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">Demande de Congé</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div><Label>Date début *</Label><Input type="date" value={leaveForm.start_date} onChange={(e) => setLeaveForm({...leaveForm, start_date: e.target.value})} /></div>
              <div><Label>Date fin *</Label><Input type="date" value={leaveForm.end_date} onChange={(e) => setLeaveForm({...leaveForm, end_date: e.target.value})} /></div>
            </div>
            <div><Label>Motif *</Label><Textarea value={leaveForm.reason} onChange={(e) => setLeaveForm({...leaveForm, reason: e.target.value})} rows={3} /></div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowLeaveModal(false)}>Annuler</Button>
            <Button onClick={handleSaveLeave} className="bg-purple-600 hover:bg-purple-700" disabled={!leaveForm.start_date || !leaveForm.end_date || !leaveForm.reason}>Envoyer</Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CommunicationDashboard;
