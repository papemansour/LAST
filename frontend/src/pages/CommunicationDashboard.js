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
  TrendingUp,
  FileText,
  Clock,
  Check,
  X
} from 'lucide-react';

// Codes personnels des chargés de com
const COM_CODES = {
  'MBM': { name: 'MBM', fullName: 'Chargé(e) de Com MBM' },
  'FZT': { name: 'FZT', fullName: 'Chargé(e) de Com FZT' }
};

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
  
  // Availability/Calendar state
  const [availability, setAvailability] = useState([]);
  const [showAvailabilityModal, setShowAvailabilityModal] = useState(false);
  const [availabilityForm, setAvailabilityForm] = useState({
    date: '',
    start_time: '09:00',
    end_time: '17:00',
    status: 'available',
    note: ''
  });

  // Days of the week for calendar view
  const weekDays = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
  const [currentMonth, setCurrentMonth] = useState(new Date());

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
      setCodeError('Code invalide. Utilisez MBM ou FZT.');
    }
  };

  const fetchData = async (code) => {
    try {
      const [userRes, newsRes, statsRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/news/all'),
        apiClient.get('/communication/stats').catch(() => ({ data: {} }))
      ]);
      
      setUser(userRes.data);
      setNews(newsRes.data || []);
      
      if (statsRes.data) {
        setStats(statsRes.data);
      }
      
      // Fetch availability for this specific code
      try {
        const availRes = await apiClient.get(`/communication/availability/${code}`);
        setAvailability(availRes.data || []);
      } catch (e) {
        console.log('Availability not available');
      }
      
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

  // Availability handlers
  const handleSaveAvailability = async () => {
    try {
      await apiClient.post('/communication/availability', {
        ...availabilityForm,
        com_code: verifiedCode
      });
      toast.success('Disponibilité enregistrée');
      setShowAvailabilityModal(false);
      setAvailabilityForm({ date: '', start_time: '09:00', end_time: '17:00', status: 'available', note: '' });
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    }
  };

  const handleDeleteAvailability = async (id) => {
    try {
      await apiClient.delete(`/communication/availability/${id}`);
      toast.success('Disponibilité supprimée');
      fetchData(verifiedCode);
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  // Calendar helpers
  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const days = [];
    
    // Add empty slots for days before the first day of month
    const startDay = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
    for (let i = 0; i < startDay; i++) {
      days.push(null);
    }
    
    // Add all days of the month
    for (let i = 1; i <= lastDay.getDate(); i++) {
      days.push(new Date(year, month, i));
    }
    
    return days;
  };

  const getAvailabilityForDate = (date) => {
    if (!date) return null;
    const dateStr = date.toISOString().split('T')[0];
    return availability.find(a => a.date === dateStr);
  };

  const formatMonth = (date) => {
    return date.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
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
                placeholder="MBM ou FZT"
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
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
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
          
          <Card className="bg-white border-green-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <Calendar className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-700">
                    {availability.filter(a => a.status === 'available').length}
                  </p>
                  <p className="text-xs text-gray-500">Jours disponibles</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-white border-orange-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-orange-100 rounded-lg">
                  <Clock className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-orange-700">
                    {availability.filter(a => a.status === 'busy').length}
                  </p>
                  <p className="text-xs text-gray-500">Jours occupés</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="bg-white border border-purple-100 p-1">
            <TabsTrigger 
              value="news" 
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <Megaphone className="h-4 w-4 mr-2" />
              Actualités
            </TabsTrigger>
            <TabsTrigger 
              value="calendar"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <Calendar className="h-4 w-4 mr-2" />
              Mes Disponibilités
            </TabsTrigger>
            <TabsTrigger 
              value="stats"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <BarChart3 className="h-4 w-4 mr-2" />
              Statistiques
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
                <Button 
                  onClick={() => {
                    setEditingNews(null);
                    setNewsForm({ title: '', content: '', category: 'general', image_url: '', is_published: true });
                    setShowNewsModal(true);
                  }}
                  className="bg-purple-600 hover:bg-purple-700"
                >
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
                      <div 
                        key={item.id} 
                        className="border rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <h3 className="font-semibold text-lg">{item.title}</h3>
                              <span className={`px-2 py-0.5 text-xs rounded-full ${
                                item.is_published !== false 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-yellow-100 text-yellow-700'
                              }`}>
                                {item.is_published !== false ? 'Publié' : 'Brouillon'}
                              </span>
                            </div>
                            <p className="text-gray-600 text-sm line-clamp-2">{item.content}</p>
                            <p className="text-xs text-gray-400 mt-2">
                              {new Date(item.created_at).toLocaleDateString('fr-FR')}
                            </p>
                          </div>
                          <div className="flex gap-2 ml-4">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openEditNews(item)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="text-red-600 hover:bg-red-50"
                              onClick={() => handleDeleteNews(item.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CALENDAR/AVAILABILITY TAB */}
          <TabsContent value="calendar">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Mes Disponibilités - {verifiedCode}</CardTitle>
                  <CardDescription>Gérez votre calendrier de disponibilités</CardDescription>
                </div>
                <Button 
                  onClick={() => setShowAvailabilityModal(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Ajouter une disponibilité
                </Button>
              </CardHeader>
              <CardContent>
                {/* Month Navigation */}
                <div className="flex items-center justify-between mb-4">
                  <Button 
                    variant="outline" 
                    onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
                  >
                    ← Mois précédent
                  </Button>
                  <h3 className="text-lg font-semibold text-purple-700 capitalize">
                    {formatMonth(currentMonth)}
                  </h3>
                  <Button 
                    variant="outline" 
                    onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
                  >
                    Mois suivant →
                  </Button>
                </div>

                {/* Calendar Grid */}
                <div className="border rounded-lg overflow-hidden">
                  {/* Header */}
                  <div className="grid grid-cols-7 bg-purple-100">
                    {weekDays.map(day => (
                      <div key={day} className="p-2 text-center font-semibold text-purple-700 text-sm">
                        {day}
                      </div>
                    ))}
                  </div>
                  
                  {/* Days */}
                  <div className="grid grid-cols-7">
                    {getDaysInMonth(currentMonth).map((day, index) => {
                      const avail = day ? getAvailabilityForDate(day) : null;
                      const isToday = day && day.toDateString() === new Date().toDateString();
                      
                      return (
                        <div 
                          key={index} 
                          className={`min-h-[80px] border-t border-r p-1 ${
                            !day ? 'bg-gray-50' : 
                            isToday ? 'bg-purple-50' : 'bg-white'
                          }`}
                        >
                          {day && (
                            <>
                              <div className={`text-sm font-medium ${isToday ? 'text-purple-700' : 'text-gray-700'}`}>
                                {day.getDate()}
                              </div>
                              {avail && (
                                <div 
                                  className={`mt-1 p-1 rounded text-xs cursor-pointer ${
                                    avail.status === 'available' 
                                      ? 'bg-green-100 text-green-700' 
                                      : avail.status === 'busy'
                                      ? 'bg-red-100 text-red-700'
                                      : 'bg-yellow-100 text-yellow-700'
                                  }`}
                                  onClick={() => handleDeleteAvailability(avail.id)}
                                  title="Cliquez pour supprimer"
                                >
                                  {avail.status === 'available' ? '✓ Dispo' : 
                                   avail.status === 'busy' ? '✗ Occupé' : '? Incertain'}
                                  {avail.start_time && (
                                    <div className="text-[10px]">{avail.start_time}-{avail.end_time}</div>
                                  )}
                                </div>
                              )}
                            </>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Legend */}
                <div className="flex gap-4 mt-4 justify-center">
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-green-100 rounded"></div>
                    <span className="text-sm text-gray-600">Disponible</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-red-100 rounded"></div>
                    <span className="text-sm text-gray-600">Occupé</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <div className="w-4 h-4 bg-yellow-100 rounded"></div>
                    <span className="text-sm text-gray-600">Incertain</span>
                  </div>
                </div>

                {/* Upcoming availability list */}
                <div className="mt-6">
                  <h4 className="font-semibold text-purple-700 mb-3">Prochaines disponibilités</h4>
                  {availability.length === 0 ? (
                    <p className="text-gray-500 text-center py-4">Aucune disponibilité enregistrée</p>
                  ) : (
                    <div className="space-y-2">
                      {availability
                        .filter(a => new Date(a.date) >= new Date())
                        .sort((a, b) => new Date(a.date) - new Date(b.date))
                        .slice(0, 5)
                        .map(avail => (
                          <div 
                            key={avail.id}
                            className={`flex items-center justify-between p-3 rounded-lg ${
                              avail.status === 'available' ? 'bg-green-50 border border-green-200' :
                              avail.status === 'busy' ? 'bg-red-50 border border-red-200' :
                              'bg-yellow-50 border border-yellow-200'
                            }`}
                          >
                            <div>
                              <p className="font-medium">
                                {new Date(avail.date).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' })}
                              </p>
                              <p className="text-sm text-gray-600">
                                {avail.start_time} - {avail.end_time}
                                {avail.note && ` • ${avail.note}`}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                avail.status === 'available' ? 'bg-green-200 text-green-800' :
                                avail.status === 'busy' ? 'bg-red-200 text-red-800' :
                                'bg-yellow-200 text-yellow-800'
                              }`}>
                                {avail.status === 'available' ? 'Disponible' : 
                                 avail.status === 'busy' ? 'Occupé' : 'Incertain'}
                              </span>
                              <Button 
                                size="sm" 
                                variant="ghost"
                                className="text-red-600 hover:bg-red-50"
                                onClick={() => handleDeleteAvailability(avail.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STATS TAB */}
          <TabsContent value="stats">
            <Card>
              <CardHeader>
                <CardTitle className="text-purple-700">Statistiques</CardTitle>
                <CardDescription>Vue d'ensemble de vos activités</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-gradient-to-br from-purple-100 to-purple-50 rounded-lg p-6">
                    <h3 className="font-semibold text-purple-700 mb-4 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Activité
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Actualités créées</span>
                        <span className="font-bold text-purple-700">{news.length}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Jours de disponibilité</span>
                        <span className="font-bold text-purple-700">{availability.length}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-blue-100 to-blue-50 rounded-lg p-6">
                    <h3 className="font-semibold text-blue-700 mb-4 flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Audience
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Étudiants actifs</span>
                        <span className="font-bold text-blue-700">{stats.totalStudents || 0}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Professeurs</span>
                        <span className="font-bold text-blue-700">{stats.totalTeachers || 0}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* News Modal */}
      <Dialog open={showNewsModal} onOpenChange={setShowNewsModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">
              {editingNews ? 'Modifier l\'actualité' : 'Nouvelle Actualité'}
            </DialogTitle>
            <DialogDescription>
              {editingNews ? 'Modifiez les informations de l\'actualité' : 'Créez une nouvelle actualité'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Titre *</Label>
              <Input
                value={newsForm.title}
                onChange={(e) => setNewsForm({...newsForm, title: e.target.value})}
                placeholder="Titre de l'actualité"
              />
            </div>
            <div>
              <Label>Contenu *</Label>
              <Textarea
                value={newsForm.content}
                onChange={(e) => setNewsForm({...newsForm, content: e.target.value})}
                placeholder="Contenu de l'actualité..."
                rows={4}
              />
            </div>
            <div>
              <Label>Catégorie</Label>
              <Select
                value={newsForm.category}
                onValueChange={(value) => setNewsForm({...newsForm, category: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="general">Général</SelectItem>
                  <SelectItem value="event">Événement</SelectItem>
                  <SelectItem value="promotion">Promotion</SelectItem>
                  <SelectItem value="update">Mise à jour</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_published"
                checked={newsForm.is_published}
                onChange={(e) => setNewsForm({...newsForm, is_published: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="is_published">Publier immédiatement</Label>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowNewsModal(false)}>
              Annuler
            </Button>
            <Button 
              onClick={handleSaveNews}
              className="bg-purple-600 hover:bg-purple-700"
              disabled={!newsForm.title || !newsForm.content}
            >
              {editingNews ? 'Mettre à jour' : 'Créer'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Availability Modal */}
      <Dialog open={showAvailabilityModal} onOpenChange={setShowAvailabilityModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-purple-700">Ajouter une disponibilité</DialogTitle>
            <DialogDescription>
              Indiquez vos disponibilités pour {verifiedCode}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Date *</Label>
              <Input
                type="date"
                value={availabilityForm.date}
                onChange={(e) => setAvailabilityForm({...availabilityForm, date: e.target.value})}
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Heure début</Label>
                <Input
                  type="time"
                  value={availabilityForm.start_time}
                  onChange={(e) => setAvailabilityForm({...availabilityForm, start_time: e.target.value})}
                />
              </div>
              <div>
                <Label>Heure fin</Label>
                <Input
                  type="time"
                  value={availabilityForm.end_time}
                  onChange={(e) => setAvailabilityForm({...availabilityForm, end_time: e.target.value})}
                />
              </div>
            </div>
            <div>
              <Label>Statut *</Label>
              <Select
                value={availabilityForm.status}
                onValueChange={(value) => setAvailabilityForm({...availabilityForm, status: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="available">✓ Disponible</SelectItem>
                  <SelectItem value="busy">✗ Occupé</SelectItem>
                  <SelectItem value="tentative">? Incertain</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Note (optionnel)</Label>
              <Input
                value={availabilityForm.note}
                onChange={(e) => setAvailabilityForm({...availabilityForm, note: e.target.value})}
                placeholder="Ex: Réunion client, Télétravail..."
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowAvailabilityModal(false)}>
              Annuler
            </Button>
            <Button 
              onClick={handleSaveAvailability}
              className="bg-purple-600 hover:bg-purple-700"
              disabled={!availabilityForm.date}
            >
              Enregistrer
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CommunicationDashboard;
