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
  MessageSquare, 
  Image, 
  Calendar, 
  BarChart3, 
  Send, 
  Plus, 
  Edit, 
  Trash2, 
  Eye,
  Users,
  TrendingUp,
  FileText,
  Star,
  Globe
} from 'lucide-react';

const CommunicationDashboard = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('news');
  
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
  
  // Testimonials state
  const [testimonials, setTestimonials] = useState([]);
  const [showTestimonialModal, setShowTestimonialModal] = useState(false);
  const [testimonialForm, setTestimonialForm] = useState({
    name: '',
    role: '',
    content: '',
    rating: 5,
    image_url: ''
  });
  
  // Stats
  const [stats, setStats] = useState({
    totalStudents: 0,
    totalTeachers: 0,
    totalNews: 0,
    totalTestimonials: 0
  });
  
  // Social posts state
  const [socialPosts, setSocialPosts] = useState([]);
  const [showSocialModal, setShowSocialModal] = useState(false);
  const [socialForm, setSocialForm] = useState({
    platform: 'facebook',
    content: '',
    scheduled_date: '',
    status: 'draft'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
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
      
      // Fetch testimonials
      try {
        const testimonialsRes = await apiClient.get('/communication/testimonials');
        setTestimonials(testimonialsRes.data || []);
      } catch (e) {
        console.log('Testimonials not available');
      }
      
      // Fetch social posts
      try {
        const socialRes = await apiClient.get('/communication/social-posts');
        setSocialPosts(socialRes.data || []);
      } catch (e) {
        console.log('Social posts not available');
      }
      
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur de chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
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
        await apiClient.post('/news', newsForm);
        toast.success('Actualité créée');
      }
      setShowNewsModal(false);
      setEditingNews(null);
      setNewsForm({ title: '', content: '', category: 'general', image_url: '', is_published: true });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    }
  };

  const handleDeleteNews = async (id) => {
    if (!window.confirm('Supprimer cette actualité ?')) return;
    try {
      await apiClient.delete(`/news/${id}`);
      toast.success('Actualité supprimée');
      fetchData();
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

  // Testimonial handlers
  const handleSaveTestimonial = async () => {
    try {
      await apiClient.post('/communication/testimonials', testimonialForm);
      toast.success('Témoignage ajouté');
      setShowTestimonialModal(false);
      setTestimonialForm({ name: '', role: '', content: '', rating: 5, image_url: '' });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  // Social post handlers
  const handleSaveSocialPost = async () => {
    try {
      await apiClient.post('/communication/social-posts', socialForm);
      toast.success('Post planifié');
      setShowSocialModal(false);
      setSocialForm({ platform: 'facebook', content: '', scheduled_date: '', status: 'draft' });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la planification');
    }
  };

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
            <p className="text-sm text-gray-600">Espace Chargé(e) de Communication</p>
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
          
          <Card className="bg-white border-pink-100">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-pink-100 rounded-lg">
                  <Star className="h-5 w-5 text-pink-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-pink-700">{testimonials.length}</p>
                  <p className="text-xs text-gray-500">Témoignages</p>
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
                  <Globe className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold text-green-700">{socialPosts.length}</p>
                  <p className="text-xs text-gray-500">Posts Sociaux</p>
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
              value="testimonials"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <Star className="h-4 w-4 mr-2" />
              Témoignages
            </TabsTrigger>
            <TabsTrigger 
              value="social"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <MessageSquare className="h-4 w-4 mr-2" />
              Réseaux Sociaux
            </TabsTrigger>
            <TabsTrigger 
              value="calendar"
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white"
            >
              <Calendar className="h-4 w-4 mr-2" />
              Calendrier
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

          {/* TESTIMONIALS TAB */}
          <TabsContent value="testimonials">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Témoignages Clients</CardTitle>
                  <CardDescription>Gérez les témoignages affichés sur le site</CardDescription>
                </div>
                <Button 
                  onClick={() => setShowTestimonialModal(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Ajouter un Témoignage
                </Button>
              </CardHeader>
              <CardContent>
                {testimonials.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucun témoignage pour le moment</p>
                ) : (
                  <div className="grid md:grid-cols-2 gap-4">
                    {testimonials.map((item) => (
                      <div 
                        key={item.id} 
                        className="border rounded-lg p-4 bg-gradient-to-br from-purple-50 to-pink-50"
                      >
                        <div className="flex items-center gap-3 mb-3">
                          <div className="w-10 h-10 bg-purple-200 rounded-full flex items-center justify-center">
                            <span className="text-purple-700 font-bold">
                              {item.name?.charAt(0) || '?'}
                            </span>
                          </div>
                          <div>
                            <p className="font-semibold">{item.name}</p>
                            <p className="text-xs text-gray-500">{item.role}</p>
                          </div>
                        </div>
                        <p className="text-gray-600 text-sm italic">"{item.content}"</p>
                        <div className="flex mt-2">
                          {[...Array(item.rating || 5)].map((_, i) => (
                            <Star key={i} className="h-4 w-4 text-yellow-400 fill-yellow-400" />
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* SOCIAL MEDIA TAB */}
          <TabsContent value="social">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-purple-700">Réseaux Sociaux</CardTitle>
                  <CardDescription>Planifiez vos publications sur les réseaux sociaux</CardDescription>
                </div>
                <Button 
                  onClick={() => setShowSocialModal(true)}
                  className="bg-purple-600 hover:bg-purple-700"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Nouveau Post
                </Button>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4 mb-6">
                  <Card className="border-blue-200 bg-blue-50">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl mb-2">📘</div>
                      <p className="font-semibold text-blue-700">Facebook</p>
                      <p className="text-xs text-gray-500">Connecté</p>
                    </CardContent>
                  </Card>
                  <Card className="border-pink-200 bg-pink-50">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl mb-2">📸</div>
                      <p className="font-semibold text-pink-700">Instagram</p>
                      <p className="text-xs text-gray-500">Connecté</p>
                    </CardContent>
                  </Card>
                  <Card className="border-sky-200 bg-sky-50">
                    <CardContent className="p-4 text-center">
                      <div className="text-3xl mb-2">🐦</div>
                      <p className="font-semibold text-sky-700">Twitter/X</p>
                      <p className="text-xs text-gray-500">Non connecté</p>
                    </CardContent>
                  </Card>
                </div>
                
                {socialPosts.length === 0 ? (
                  <p className="text-center text-gray-500 py-8">Aucun post planifié</p>
                ) : (
                  <div className="space-y-4">
                    {socialPosts.map((post) => (
                      <div key={post.id} className="border rounded-lg p-4 bg-white">
                        <div className="flex justify-between items-start">
                          <div>
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              post.platform === 'facebook' ? 'bg-blue-100 text-blue-700' :
                              post.platform === 'instagram' ? 'bg-pink-100 text-pink-700' :
                              'bg-sky-100 text-sky-700'
                            }`}>
                              {post.platform}
                            </span>
                            <p className="mt-2 text-gray-700">{post.content}</p>
                            <p className="text-xs text-gray-400 mt-2">
                              Prévu: {post.scheduled_date || 'Non planifié'}
                            </p>
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            post.status === 'published' ? 'bg-green-100 text-green-700' :
                            post.status === 'scheduled' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-gray-100 text-gray-700'
                          }`}>
                            {post.status === 'published' ? 'Publié' : 
                             post.status === 'scheduled' ? 'Planifié' : 'Brouillon'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* CALENDAR TAB */}
          <TabsContent value="calendar">
            <Card>
              <CardHeader>
                <CardTitle className="text-purple-700">Calendrier Éditorial</CardTitle>
                <CardDescription>Planifiez vos communications à venir</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-8 text-center">
                  <Calendar className="h-16 w-16 text-purple-300 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-purple-700 mb-2">
                    Calendrier Éditorial
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Organisez vos publications et événements de communication
                  </p>
                  <div className="grid md:grid-cols-3 gap-4 mt-6">
                    <div className="bg-white rounded-lg p-4 border">
                      <p className="text-2xl font-bold text-purple-600">{news.filter(n => n.is_published).length}</p>
                      <p className="text-sm text-gray-500">Publiés ce mois</p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border">
                      <p className="text-2xl font-bold text-yellow-600">{news.filter(n => !n.is_published).length}</p>
                      <p className="text-sm text-gray-500">En attente</p>
                    </div>
                    <div className="bg-white rounded-lg p-4 border">
                      <p className="text-2xl font-bold text-green-600">{socialPosts.filter(p => p.status === 'scheduled').length}</p>
                      <p className="text-sm text-gray-500">Posts planifiés</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* STATS TAB */}
          <TabsContent value="stats">
            <Card>
              <CardHeader>
                <CardTitle className="text-purple-700">Statistiques de Communication</CardTitle>
                <CardDescription>Suivez les performances de vos communications</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-gradient-to-br from-purple-100 to-purple-50 rounded-lg p-6">
                    <h3 className="font-semibold text-purple-700 mb-4 flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Engagement
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Actualités publiées</span>
                        <span className="font-bold text-purple-700">{news.length}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Témoignages collectés</span>
                        <span className="font-bold text-purple-700">{testimonials.length}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Posts réseaux sociaux</span>
                        <span className="font-bold text-purple-700">{socialPosts.length}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="bg-gradient-to-br from-pink-100 to-pink-50 rounded-lg p-6">
                    <h3 className="font-semibold text-pink-700 mb-4 flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      Audience
                    </h3>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Étudiants actifs</span>
                        <span className="font-bold text-pink-700">{stats.totalStudents || 0}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Professeurs</span>
                        <span className="font-bold text-pink-700">{stats.totalTeachers || 0}</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Visiteurs estimés</span>
                        <span className="font-bold text-pink-700">~{(stats.totalStudents || 0) * 3}</span>
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
              {editingNews ? 'Modifiez les informations de l\'actualité' : 'Créez une nouvelle actualité pour la plateforme'}
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
            <div>
              <Label>URL Image (optionnel)</Label>
              <Input
                value={newsForm.image_url}
                onChange={(e) => setNewsForm({...newsForm, image_url: e.target.value})}
                placeholder="https://..."
              />
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

      {/* Testimonial Modal */}
      <Dialog open={showTestimonialModal} onOpenChange={setShowTestimonialModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">Ajouter un Témoignage</DialogTitle>
            <DialogDescription>
              Ajoutez un témoignage client à afficher sur le site
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Nom *</Label>
              <Input
                value={testimonialForm.name}
                onChange={(e) => setTestimonialForm({...testimonialForm, name: e.target.value})}
                placeholder="Nom du client"
              />
            </div>
            <div>
              <Label>Rôle/Profession</Label>
              <Input
                value={testimonialForm.role}
                onChange={(e) => setTestimonialForm({...testimonialForm, role: e.target.value})}
                placeholder="Ex: Étudiant, Professionnel..."
              />
            </div>
            <div>
              <Label>Témoignage *</Label>
              <Textarea
                value={testimonialForm.content}
                onChange={(e) => setTestimonialForm({...testimonialForm, content: e.target.value})}
                placeholder="Le témoignage du client..."
                rows={3}
              />
            </div>
            <div>
              <Label>Note (1-5)</Label>
              <Select
                value={String(testimonialForm.rating)}
                onValueChange={(value) => setTestimonialForm({...testimonialForm, rating: parseInt(value)})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">⭐⭐⭐⭐⭐ (5)</SelectItem>
                  <SelectItem value="4">⭐⭐⭐⭐ (4)</SelectItem>
                  <SelectItem value="3">⭐⭐⭐ (3)</SelectItem>
                  <SelectItem value="2">⭐⭐ (2)</SelectItem>
                  <SelectItem value="1">⭐ (1)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowTestimonialModal(false)}>
              Annuler
            </Button>
            <Button 
              onClick={handleSaveTestimonial}
              className="bg-purple-600 hover:bg-purple-700"
              disabled={!testimonialForm.name || !testimonialForm.content}
            >
              Ajouter
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Social Post Modal */}
      <Dialog open={showSocialModal} onOpenChange={setShowSocialModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-purple-700">Nouveau Post Social</DialogTitle>
            <DialogDescription>
              Planifiez une publication sur les réseaux sociaux
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Plateforme *</Label>
              <Select
                value={socialForm.platform}
                onValueChange={(value) => setSocialForm({...socialForm, platform: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="facebook">📘 Facebook</SelectItem>
                  <SelectItem value="instagram">📸 Instagram</SelectItem>
                  <SelectItem value="twitter">🐦 Twitter/X</SelectItem>
                  <SelectItem value="linkedin">💼 LinkedIn</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Contenu *</Label>
              <Textarea
                value={socialForm.content}
                onChange={(e) => setSocialForm({...socialForm, content: e.target.value})}
                placeholder="Votre message..."
                rows={4}
              />
            </div>
            <div>
              <Label>Date de publication</Label>
              <Input
                type="datetime-local"
                value={socialForm.scheduled_date}
                onChange={(e) => setSocialForm({...socialForm, scheduled_date: e.target.value})}
              />
            </div>
            <div>
              <Label>Statut</Label>
              <Select
                value={socialForm.status}
                onValueChange={(value) => setSocialForm({...socialForm, status: value})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Brouillon</SelectItem>
                  <SelectItem value="scheduled">Planifié</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-4">
            <Button variant="outline" onClick={() => setShowSocialModal(false)}>
              Annuler
            </Button>
            <Button 
              onClick={handleSaveSocialPost}
              className="bg-purple-600 hover:bg-purple-700"
              disabled={!socialForm.content}
            >
              Planifier
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CommunicationDashboard;
