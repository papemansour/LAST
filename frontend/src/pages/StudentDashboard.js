import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle 
} from '../components/ui/dialog';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { LogOut, BookOpen, FileText, Link as LinkIcon, Upload, Send, User, Mail, MessageCircle, Heart, Sparkles, Eye, GraduationCap, Gamepad2, Newspaper, Library, UserCircle } from 'lucide-react';
import ConversationChat from '../components/ConversationChat';
import NewsDisplay from '../components/NewsDisplay';
import WelcomeLetter from '../components/WelcomeLetter';
import DonationButton from '../components/DonationButton';
import KalamaClub from '../components/KalamaClub';
// ActivityFeed removed
import StudentOfMonthBadge from '../components/StudentOfMonthBadge';
import ProgressTracker from '../components/ProgressTracker';
import LiveNotifications from '../components/LiveNotifications';
import StudentGames from '../components/StudentGamesAdvanced';

const StudentDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [teacher, setTeacher] = useState(null);
  const [links, setLinks] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [homeworks, setHomeworks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [homeworkData, setHomeworkData] = useState({
    title: '',
    description: '',
    file_url: ''
  });
  const [previewDocument, setPreviewDocument] = useState(null);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [pricing, setPricing] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [userRes, linksRes, documentsRes, homeworksRes, pricingRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/student/my-links'),
        apiClient.get('/student/my-documents'),
        apiClient.get('/student/my-homeworks'),
        apiClient.get('/pricing')
      ]);
      
      setUser(userRes.data);
      setLinks(linksRes.data);
      setDocuments(documentsRes.data);
      setHomeworks(homeworksRes.data);
      setPricing(pricingRes.data);
      
      // Get teacher info if assigned
      if (userRes.data.assigned_teacher) {
        const teacherRes = await apiClient.get(`/student/my-teacher/${userRes.data.assigned_teacher}`);
        setTeacher(teacherRes.data);
      }
      
      setLoading(false);
    } catch (error) {
      toast.error('Erreur de chargement');
      navigate('/login');
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Fichier trop volumineux (max 10MB)');
      return;
    }
    
    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiClient.post('/student/upload-homework', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      
      setHomeworkData({ ...homeworkData, file_url: response.data.file_url });
      toast.success('Fichier téléchargé avec succès!');
    } catch (error) {
      toast.error('Erreur lors du téléchargement');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleSubmitHomework = async (e) => {
    e.preventDefault();
    if (!homeworkData.file_url) {
      toast.error('Veuillez télécharger un fichier ou entrer une URL');
      return;
    }
    
    try {
      await apiClient.post('/student/submit-homework', homeworkData);
      toast.success('Devoir envoyé avec succès!');
      setHomeworkData({ title: '', description: '', file_url: '' });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du devoir');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
    toast.success('Déconnexion réussie');
  };

  // Calculate price dynamically based on level and KALAMA CLUB membership
  const getPackPrice = () => {
    if (!pricing || !user) return '76€';
    
    const level = user.level;
    const hasClub = user.join_kalama_club;
    
    let basePrice = 0;
    let discount = 0;
    
    switch(level) {
      case 'kkid':
        basePrice = pricing.kkid_eur || 30;
        discount = pricing.kkid_discount || 0;
        break;
      case 'beginner':
        basePrice = pricing.beginner_eur || 76;
        discount = pricing.beginner_discount || 0;
        break;
      case 'intermediate':
        basePrice = pricing.intermediate_eur || 90;
        discount = pricing.intermediate_discount || 0;
        break;
      case 'advanced':
        basePrice = pricing.advanced_eur || 102;
        discount = pricing.advanced_discount || 0;
        break;
      default:
        basePrice = 76;
    }
    
    const finalPrice = basePrice - discount;
    return `${finalPrice}€`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-blue-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-2 sm:px-4 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex flex-col">
            <h1 className="text-lg sm:text-2xl font-bold text-teal-600">My KALAMA</h1>
            <span className="text-xs sm:text-sm text-gray-600 font-semibold uppercase tracking-wide">English</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <LiveNotifications />
            <span className="text-xs sm:text-base text-gray-700 hidden sm:inline">{user?.first_name} {user?.last_name}</span>
            <span className="text-xs text-gray-700 sm:hidden">{user?.first_name}</span>
            <Button variant="outline" size="sm" onClick={handleLogout} className="border-teal-600 text-teal-600 hover:bg-teal-50 text-xs sm:text-sm px-2 sm:px-4">
              <LogOut className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" />
              <span className="hidden sm:inline">Déconnexion</span>
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-2 sm:px-4 py-4 sm:py-12 max-w-7xl">
        {/* Student of the Month Badge - Affichage ÉNORME pour célébrer */}
        <div className="mb-4 sm:mb-8 flex justify-center">
          <StudentOfMonthBadge showInProfile={true} />
        </div>

        {/* Header avec info prof */}
        <div className="mb-4 sm:mb-8">
          <h2 className="text-2xl sm:text-4xl font-bold text-gray-900 mb-2 sm:mb-4">Espace Étudiant</h2>
          <div className="grid md:grid-cols-2 gap-4">
            <Card className="border-teal-100 bg-gradient-to-r from-teal-50 to-blue-50">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-teal-600 rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Votre professeur</p>
                    {teacher ? (
                      <p className="text-lg font-bold text-teal-800">
                        {teacher.first_name} {teacher.last_name}
                      </p>
                    ) : (
                      <p className="text-sm text-gray-500">Aucun professeur assigné</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card className="border-blue-100 bg-gradient-to-r from-blue-50 to-purple-50">
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
                    <Mail className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Contact général</p>
                    <p className="text-lg font-bold text-blue-800">
                      mykalamaenglish@gmail.com
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        <Tabs defaultValue="welcome" className="space-y-6">
          {/* Grid Navigation Cards */}
          <TabsList className="grid grid-cols-2 md:grid-cols-4 gap-3 h-auto bg-transparent p-0">
            <TabsTrigger 
              value="welcome" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-teal-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-teal-50 border-2 border-teal-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">💌</span>
              <span className="text-xs font-semibold">Bienvenue</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="club" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-cyan-500 data-[state=active]:to-cyan-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-cyan-50 border-2 border-cyan-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">✨</span>
              <span className="text-xs font-semibold">CLUB</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="mypack" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-purple-500 data-[state=active]:to-pink-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-purple-50 border-2 border-purple-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">🎓</span>
              <span className="text-xs font-semibold">Mon Pack</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="links" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-blue-500 data-[state=active]:to-blue-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-blue-50 border-2 border-blue-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">🔗</span>
              <span className="text-xs font-semibold">Liens</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="documents" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-orange-50 border-2 border-orange-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">📄</span>
              <span className="text-xs font-semibold">Documents</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="games" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-yellow-500 data-[state=active]:to-yellow-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-yellow-50 border-2 border-yellow-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">🎮</span>
              <span className="text-xs font-semibold">Jeu</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="conversations" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-green-500 data-[state=active]:to-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-green-50 border-2 border-green-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">💬</span>
              <span className="text-xs font-semibold">Messages</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="news" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-red-500 data-[state=active]:to-red-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-red-50 border-2 border-red-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">📰</span>
              <span className="text-xs font-semibold">News</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="kalamatheque" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-indigo-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-indigo-50 border-2 border-indigo-200 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">📚</span>
              <span className="text-xs font-semibold">Bibliothèque</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="profile" 
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-gray-700 data-[state=active]:to-gray-800 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white hover:bg-gray-50 border-2 border-gray-300 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <span className="text-3xl">👤</span>
              <span className="text-xs font-semibold">Profil</span>
            </TabsTrigger>
          </TabsList>
          
          {/* Content Area */}
          <div className="flex-1">

          {/* Welcome Letter Tab */}
          <TabsContent value="welcome">
            <div className="space-y-6">
              <WelcomeLetter />
              <ProgressTracker user={user} />
            </div>
          </TabsContent>

          {/* KALAMA CLUB Tab */}
          <TabsContent value="club">
            <KalamaClub userRole="student" />
          </TabsContent>

          {/* Mon Pack Tab - Shows student's pack with payment */}
          <TabsContent value="mypack">
            {!user || !user.level ? (
              <Card>
                <CardContent className="text-center py-12">
                  <p className="text-gray-600">Chargement de votre pack...</p>
                </CardContent>
              </Card>
            ) : (
              <div className="relative overflow-hidden rounded-2xl border-2 bg-white shadow-xl max-w-md mx-auto">
                {/* Pack Header with gradient */}
                <div className={`bg-gradient-to-br p-6 ${
                  user.level === 'kkid' ? 'from-pink-100 to-pink-200' :
                  user.level === 'beginner' ? 'from-teal-100 to-teal-200' :
                  user.level === 'intermediate' ? 'from-teal-100 to-cyan-200' :
                  'from-teal-100 to-blue-200'
                }`}>
                  <h3 className="text-2xl md:text-3xl font-bold mb-2 text-gray-900">
                    {user.level === 'kkid' ? 'Pack K-Kid' :
                     user.level === 'beginner' ? 'Pack K-Débutant' :
                     user.level === 'intermediate' ? 'Pack K-Intermédiaire' :
                     user.level === 'advanced' ? 'Pack K-Professionnel' : 'Votre Pack'}
                  </h3>
                  <p className="text-sm md:text-base text-gray-700">
                    {user.level === 'kkid' ? 'Enfants 3-9 ans' :
                     user.level === 'beginner' ? 'Parfait pour commencer' :
                     user.level === 'intermediate' ? 'Le plus choisi' :
                     'Formation professionnelle'}
                  </p>
                </div>

                {/* Pack Content */}
                <div className="p-6 space-y-6">
                  {/* Price */}
                  <div className="text-center">
                    <div className="text-4xl md:text-5xl font-bold text-teal-600 mb-2">
                      {getPackPrice()}
                    </div>
                    <p className="text-sm text-gray-600">par mois</p>
                    {user.join_kalama_club && (
                      <p className="text-sm text-green-600 mt-2">
                        ✨ KALAMA CLUB inclus
                      </p>
                    )}
                  </div>

                  {/* Features list based on level */}
                  <ul className="space-y-3 text-sm">
                    {user.level === 'kkid' && (
                      <>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-pink-600 rounded-full"></span>
                          <span>Vidéos et jeux interactifs</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-pink-600 rounded-full"></span>
                          <span>Limite le temps d'écran</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-pink-600 rounded-full"></span>
                          <span>Favorise les interactions réelles</span>
                        </li>
                      </>
                    )}
                    {user.level !== 'kkid' && (
                      <>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-teal-600 rounded-full"></span>
                          <span>Cours particuliers en ligne</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-teal-600 rounded-full"></span>
                          <span>Professeurs qualifiés</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-teal-600 rounded-full"></span>
                          <span>Horaires flexibles</span>
                        </li>
                        <li className="flex items-center gap-2">
                          <span className="w-2 h-2 bg-teal-600 rounded-full"></span>
                          <span>Suivi personnalisé</span>
                        </li>
                      </>
                    )}
                  </ul>

                  {/* Payment Button */}
                  <Button
                    className="w-full bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700 text-white py-6 text-lg"
                    onClick={() => {
                      const stripeLinks = {
                        'kkid': 'https://buy.stripe.com/9B64gz8rFaJD7RB4q0',
                        'beginner_with_club': 'https://buy.stripe.com/8x26oH37lcRL2xhbSs',
                        'beginner_without_club': 'https://buy.stripe.com/fZufZheQ304Z5Jtg8IenS00',
                        'intermediate_with_club': 'https://buy.stripe.com/4gMbJ10Zd6tn2xh3lW',
                        'intermediate_without_club': 'https://buy.stripe.com/dRmdR96jx5pjdbVf4EenS01',
                        'advanced_with_club': 'https://buy.stripe.com/28E3cv4bp1938VFf4E',
                        'advanced_without_club': 'https://buy.stripe.com/00w14nazNg3XefZ2hSenS02'
                      };
                      
                      let link;
                      if (user.level === 'kkid') {
                        link = stripeLinks.kkid;
                      } else {
                        const key = `${user.level}_${user.join_kalama_club ? 'with' : 'without'}_club`;
                        link = stripeLinks[key];
                      }
                      
                      if (link) {
                        window.location.href = link;
                      } else {
                        toast.error('Erreur de paiement. Contactez l\'administration.');
                      }
                    }}
                  >
                    💳 Payer ma mensualité
                  </Button>

                  <p className="text-xs text-gray-500 text-center">
                    Paiement sécurisé par Stripe
                  </p>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Liens Tab */}
          <TabsContent value="links">
            <Card className="border-teal-100">
              <CardHeader>
                <CardTitle className="text-teal-800">Liens reçus de votre professeur</CardTitle>
                <CardDescription>Google Meet, ressources en ligne, etc.</CardDescription>
              </CardHeader>
              <CardContent>
                {links.length === 0 ? (
                  <p className="text-gray-500">Aucun lien reçu</p>
                ) : (
                  <div className="space-y-4">
                    {links.map((link) => (
                      <div key={link.id} className="p-4 border border-teal-100 rounded-lg hover:bg-teal-50 transition">
                        <div className="flex items-start gap-3">
                          <LinkIcon className="w-5 h-5 text-teal-600 mt-1 flex-shrink-0" />
                          <div className="flex-1">
                            <h3 className="font-semibold text-teal-800">{link.title}</h3>
                            {link.description && (
                              <p className="text-sm text-gray-600 mt-1">{link.description}</p>
                            )}
                            <a 
                              href={link.url} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="inline-flex items-center gap-1 text-sm text-teal-600 hover:underline mt-2"
                            >
                              <LinkIcon className="w-4 h-4" />
                              Ouvrir le lien
                            </a>
                            <div className="flex gap-2 mt-2">
                              <span className="text-xs bg-teal-100 text-teal-700 px-2 py-1 rounded">
                                De: {link.from_teacher_name}
                              </span>
                              <span className="text-xs text-gray-500">
                                {new Date(link.created_at).toLocaleDateString('fr-FR')}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            <Card className="border-teal-100">
              <CardHeader>
                <CardTitle className="text-teal-800">Documents reçus</CardTitle>
                <CardDescription>Documents partagés par votre professeur</CardDescription>
              </CardHeader>
              <CardContent>
                {documents.length === 0 ? (
                  <p className="text-gray-500">Aucun document reçu</p>
                ) : (
                  <div className="space-y-4">
                    {documents.map((doc) => (
                      <div key={doc.id} className="p-4 border border-teal-100 rounded-lg hover:bg-teal-50 transition">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex items-start gap-3 flex-1">
                            <FileText className="w-5 h-5 text-teal-600 mt-1 flex-shrink-0" />
                            <div className="flex-1">
                              <h3 className="font-semibold text-teal-800">{doc.title}</h3>
                              {doc.description && (
                                <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                              )}
                              <div className="flex gap-2 mt-2">
                                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">
                                  De: {doc.from_teacher_name || doc.from_admin_name || 'Admin'}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {new Date(doc.created_at).toLocaleDateString('fr-FR')}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col gap-2">
                            <Button
                              size="sm"
                              onClick={() => {
                                setPreviewDocument(doc);
                                setShowPreviewDialog(true);
                              }}
                              className="bg-purple-600 hover:bg-purple-700"
                            >
                              <Eye className="w-4 h-4 mr-1" />
                              Visualiser
                            </Button>
                            <Button
                              size="sm"
                              onClick={() => window.open(doc.file_url, '_blank')}
                              className="bg-teal-600 hover:bg-teal-700"
                            >
                              📄 Ouvrir
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                const link = document.createElement('a');
                                link.href = doc.file_url;
                                link.download = doc.title;
                                link.click();
                                toast.success('Téléchargement démarré');
                              }}
                              className="border-blue-500 text-blue-600"
                            >
                              💾 Télécharger
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={async () => {
                                if (window.confirm('Supprimer ce document ?')) {
                                  try {
                                    await apiClient.delete(`/documents/${doc.id}`);
                                    toast.success('Document supprimé');
                                    fetchData();
                                  } catch (error) {
                                    toast.error('Erreur de suppression');
                                  }
                                }
                              }}
                              className="border-red-500 text-red-600"
                            >
                              🗑️ Supprimer
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

          {/* Games Tab */}
          <TabsContent value="games">
            <StudentGames />
          </TabsContent>

          {/* Conversations Tab */}
          <TabsContent value="conversations">
            <Card className="border-teal-100">
              <CardHeader className="bg-teal-50">
                <CardTitle className="text-teal-800">💬 Conversations avec mon professeur</CardTitle>
                <CardDescription>
                  {teacher ? `Échangez avec ${teacher.first_name} ${teacher.last_name}` : 'Aucun professeur assigné'}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {!teacher ? (
                  <div className="text-center py-12">
                    <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-500">Vous n'avez pas encore de professeur assigné</p>
                  </div>
                ) : (
                  <ConversationChat
                    recipientId={teacher.id}
                    recipientName={`${teacher.first_name} ${teacher.last_name}`}
                    currentUserId={user?.id}
                  />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* News Tab */}
          <TabsContent value="news">
            <NewsDisplay />
          </TabsContent>

          {/* Kalamathèque Tab */}
          <TabsContent value="kalamatheque">
            <Card className="border-teal-100">
              <CardHeader className="bg-teal-50">
                <CardTitle className="text-teal-800">📚 Kalamathèque</CardTitle>
                <CardDescription>Accédez à notre bibliothèque numérique</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <div className="mb-6">
                    <div className="w-20 h-20 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-4xl">📚</span>
                    </div>
                    <h3 className="text-xl font-semibold mb-2">Bibliothèque numérique</h3>
                    <p className="text-gray-600 mb-6">
                      Enrichissez votre apprentissage avec notre collection de ressources pédagogiques
                    </p>
                  </div>
                  <Button 
                    onClick={() => navigate('/kalamatheque-access')}
                    className="bg-teal-600 hover:bg-teal-700"
                    size="lg"
                  >
                    🔓 Accéder à Kalamathèque
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Profile Tab - Changement de mot de passe */}
          <TabsContent value="profile">
            <Card className="border-teal-100">
              <CardHeader className="bg-teal-50">
                <CardTitle className="text-teal-800">Mon Profil</CardTitle>
                <CardDescription>Gérez vos informations personnelles et votre mot de passe</CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="space-y-6">
                  {/* Informations personnelles */}
                  <div className="border-b pb-6">
                    <h3 className="font-semibold text-lg mb-4 text-teal-700">Informations personnelles</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Nom complet:</span>
                        <span className="font-semibold">{user?.first_name} {user?.last_name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Email:</span>
                        <span className="font-semibold">{user?.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Niveau:</span>
                        <span className="font-semibold uppercase">{user?.level}</span>
                      </div>
                    </div>
                  </div>

                  {/* Changement de mot de passe */}
                  <div>
                    <h3 className="font-semibold text-lg mb-4 text-teal-700">Changer mon mot de passe</h3>
                    <form onSubmit={async (e) => {
                      e.preventDefault();
                      const formData = new FormData(e.target);
                      const oldPassword = formData.get('old_password');
                      const newPassword = formData.get('new_password');
                      const confirmPassword = formData.get('confirm_password');

                      if (newPassword !== confirmPassword) {
                        toast.error('Les mots de passe ne correspondent pas');
                        return;
                      }

                      if (newPassword.length < 6) {
                        toast.error('Le mot de passe doit contenir au moins 6 caractères');
                        return;
                      }

                      try {
                        await apiClient.post('/auth/change-password', {
                          old_password: oldPassword,
                          new_password: newPassword
                        });
                        toast.success('Mot de passe modifié avec succès!');
                        e.target.reset();
                      } catch (error) {
                        toast.error(error.response?.data?.detail || 'Erreur lors du changement de mot de passe');
                      }
                    }} className="space-y-4">
                      <div>
                        <Label htmlFor="old_password">Ancien mot de passe</Label>
                        <Input
                          id="old_password"
                          name="old_password"
                          type="password"
                          required
                          className="border-teal-200 focus:border-teal-500"
                        />
                      </div>
                      <div>
                        <Label htmlFor="new_password">Nouveau mot de passe</Label>
                        <Input
                          id="new_password"
                          name="new_password"
                          type="password"
                          required
                          minLength={6}
                          className="border-teal-200 focus:border-teal-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">Minimum 6 caractères</p>
                      </div>
                      <div>
                        <Label htmlFor="confirm_password">Confirmer le nouveau mot de passe</Label>
                        <Input
                          id="confirm_password"
                          name="confirm_password"
                          type="password"
                          required
                          minLength={6}
                          className="border-teal-200 focus:border-teal-500"
                        />
                      </div>
                      <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700">
                        🔐 Changer mon mot de passe
                      </Button>
                    </form>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
          </div>
        </Tabs>
      </div>

      {/* Document Preview Dialog */}
      <Dialog open={showPreviewDialog} onOpenChange={setShowPreviewDialog}>
        <DialogContent className="max-w-5xl max-h-[90vh] overflow-hidden">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-teal-600" />
              {previewDocument?.title}
            </DialogTitle>
          </DialogHeader>
          <div className="overflow-auto max-h-[75vh]">
            {previewDocument && (
              <>
                {previewDocument.description && (
                  <p className="text-sm text-gray-600 mb-4 p-3 bg-gray-50 rounded-lg">
                    {previewDocument.description}
                  </p>
                )}
                {previewDocument.file_url?.match(/\.(jpg|jpeg|png|gif|webp|svg)$/i) ? (
                  <img 
                    src={previewDocument.file_url} 
                    alt={previewDocument.title} 
                    className="w-full rounded-lg shadow-lg"
                  />
                ) : previewDocument.file_url?.match(/\.(pdf)$/i) ? (
                  <iframe
                    src={previewDocument.file_url}
                    className="w-full h-[65vh] rounded-lg border"
                    title={previewDocument.title}
                  />
                ) : (
                  <div className="text-center py-12">
                    <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">
                      Aperçu non disponible pour ce type de fichier
                    </p>
                    <Button
                      onClick={() => window.open(previewDocument.file_url, '_blank')}
                      className="bg-teal-600 hover:bg-teal-700"
                    >
                      Ouvrir dans un nouvel onglet
                    </Button>
                  </div>
                )}
                <div className="flex gap-2 mt-4 pt-4 border-t">
                  <Button
                    onClick={() => window.open(previewDocument.file_url, '_blank')}
                    className="flex-1 bg-teal-600 hover:bg-teal-700"
                  >
                    📄 Ouvrir dans un nouvel onglet
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = previewDocument.file_url;
                      link.download = previewDocument.title;
                      link.click();
                      toast.success('Téléchargement démarré');
                    }}
                    className="flex-1 border-blue-500 text-blue-600"
                  >
                    💾 Télécharger
                  </Button>
                </div>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StudentDashboard;
