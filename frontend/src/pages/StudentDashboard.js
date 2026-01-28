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
import { LogOut, BookOpen, FileText, Link as LinkIcon, Upload, Send, User, Mail, MessageCircle, Heart, Sparkles, Eye, GraduationCap, Gamepad2, Newspaper, Library, UserCircle, Video, TrendingUp, Trophy, Gift, Calendar } from 'lucide-react';
import ConversationChat from '../components/ConversationChat';
import NewsDisplay from '../components/NewsDisplay';
import WelcomeLetter from '../components/WelcomeLetter';
import DonationButton from '../components/DonationButton';
import KalamaClub from '../components/KalamaClub';
import StudentDocuments from '../components/StudentDocuments';
import StudentProgression from '../components/StudentProgression';
import WeeklyChallenges from '../components/WeeklyChallenges';
import GiftWelcomeLetter from '../components/GiftWelcomeLetter';
// ActivityFeed removed
import StudentOfMonthBadge from '../components/StudentOfMonthBadge';
import ProgressTracker from '../components/ProgressTracker';
import LiveNotifications from '../components/LiveNotifications';
import StudentGames from '../components/StudentGamesAdvanced';
import WeekendGifts from '../components/WeekendGifts';
import TreasureChest from '../components/TreasureChest';
import KidsWelcomeLetter from '../components/KidsWelcomeLetter';
import KidsFlashcards from '../components/KidsFlashcards';
import KidsVideoPlaylist from '../components/KidsVideoPlaylist';
import StudentCourseSummaries from '../components/StudentCourseSummaries';
import NotificationBell from '../components/NotificationBell';
import StudentCourseLinks from '../components/StudentCourseLinks';
import TrialCountdown from '../components/TrialCountdown';
import RamadanPromoBanner from '../components/RamadanPromoBanner';
import StudentAvailability from '../components/StudentAvailability';
const StudentDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [teacher, setTeacher] = useState(null);
  const [admin, setAdmin] = useState(null);
  const [links, setLinks] = useState([]);
  const [homeworks, setHomeworks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWelcomeGift, setShowWelcomeGift] = useState(false);
  const [activeTab, setActiveTab] = useState(null); // For controlled tab switching
  const [homeworkData, setHomeworkData] = useState({
    title: '',
    description: '',
    file_url: ''
  });
  const [uploadingFile, setUploadingFile] = useState(false);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [pricing, setPricing] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [userRes, linksRes, homeworksRes, pricingRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/student/my-links'),
        apiClient.get('/student/my-homeworks'),
        apiClient.get('/pricing')
      ]);
      
      setUser(userRes.data);
      setLinks(linksRes.data);
      setHomeworks(homeworksRes.data);
      setPricing(pricingRes.data);
      
      // Check if first login to show welcome gift
      if (userRes.data.first_login) {
        setShowWelcomeGift(true);
      }
      
      // Get teacher info if assigned
      if (userRes.data.assigned_teacher) {
        const teacherRes = await apiClient.get(`/student/my-teacher/${userRes.data.assigned_teacher}`);
        setTeacher(teacherRes.data);
      }
      
      // Get admin info for messaging
      try {
        const allUsersRes = await apiClient.get('/admin/all-users');
        const adminUser = allUsersRes.data.find(u => u.role === 'admin');
        if (adminUser) {
          setAdmin(adminUser);
        }
      } catch (error) {
        console.log('Could not fetch admin info:', error);
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
    
    // Vérifier si l'étudiant a un indicatif africain
    const africanCodes = ['+221', '+225', '+226', '+227', '+228', '+229', '+230', '+231', '+232', '+233', '+234', '+235', '+236', '+237', '+238', '+239', '+240', '+241', '+242', '+243', '+244', '+245', '+246', '+248', '+249', '+250', '+251', '+252', '+253', '+254', '+255', '+256', '+257', '+258', '+260', '+261', '+262', '+263', '+264', '+265', '+266', '+267', '+268', '+269', '+290', '+291'];
    const isAfrican = user.phone && africanCodes.some(code => user.phone.startsWith(code));
    
    let basePriceEur = 0;
    let basePriceFcfa = 0;
    let discountEur = 0;
    let discountFcfa = 0;
    
    switch(level) {
      case 'kkid':
        basePriceEur = pricing.kkid_eur || 30;
        basePriceFcfa = pricing.kkid_fcfa || 7000;
        discountEur = pricing.kkid_discount || 0;
        discountFcfa = pricing.kkid_discount_fcfa || 0;
        break;
      case 'beginner':
        basePriceEur = pricing.beginner_eur || 76;
        basePriceFcfa = pricing.beginner_fcfa || 15000;
        discountEur = pricing.beginner_discount || 0;
        discountFcfa = pricing.beginner_discount_fcfa || 0;
        break;
      case 'intermediate':
        basePriceEur = pricing.intermediate_eur || 90;
        basePriceFcfa = pricing.intermediate_fcfa || 25000;
        discountEur = pricing.intermediate_discount || 0;
        discountFcfa = pricing.intermediate_discount_fcfa || 0;
        break;
      case 'advanced':
        basePriceEur = pricing.advanced_eur || 102;
        basePriceFcfa = pricing.advanced_fcfa || 40000;
        discountEur = pricing.advanced_discount || 0;
        discountFcfa = pricing.advanced_discount_fcfa || 0;
        break;
      default:
        basePriceEur = 76;
        basePriceFcfa = 15000;
    }
    
    // Afficher en FCFA pour les indicatifs africains, sinon en EUR
    if (isAfrican) {
      const finalPriceFcfa = basePriceFcfa - discountFcfa;
      return `${finalPriceFcfa.toLocaleString()} FCFA`;
    } else {
      const finalPriceEur = basePriceEur - discountEur;
      return `${finalPriceEur}€`;
    }
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
      {/* Gift Welcome Letter Modal */}
      {showWelcomeGift && (
        <GiftWelcomeLetter 
          user={user} 
          onClose={() => setShowWelcomeGift(false)}
        />
      )}

      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-2 sm:px-4 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex flex-col">
            <h1 className="text-lg sm:text-2xl font-bold text-teal-600">My KALAMA</h1>
            <span className="text-xs sm:text-sm text-gray-600 font-semibold uppercase tracking-wide">English</span>
          </div>
          <div className="flex items-center gap-2 sm:gap-4">
            <NotificationBell userId={user?.id} />
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
        {/* Lettre de bienvenue K-Kids */}
        {user.level === 'kkid' && <KidsWelcomeLetter user={user} />}
        
        {/* Student of the Month Badge - Affichage ÉNORME pour célébrer */}
        <div className="mb-4 sm:mb-8 flex justify-center">
          <StudentOfMonthBadge showInProfile={true} />
        </div>

        {/* Header avec info prof - version K-Kids ou normale */}
        <div className="mb-4 sm:mb-8">
          <h2 className="text-2xl sm:text-4xl font-bold text-gray-900 mb-2 sm:mb-4">
            {user.level === 'kkid' ? '🎨 Espace K-Kids' : 'Espace Étudiant'}
          </h2>
          <div className="grid md:grid-cols-2 gap-4">
            <Card className={user.level === 'kkid' ? 'border-pink-200 bg-gradient-to-r from-pink-50 to-purple-50' : 'border-teal-100 bg-gradient-to-r from-teal-50 to-blue-50'}>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 ${user.level === 'kkid' ? 'bg-pink-500' : 'bg-teal-600'} rounded-full flex items-center justify-center`}>
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">{user.level === 'kkid' ? 'Ton professeur' : 'Votre professeur'}</p>
                    {teacher ? (
                      <p className={`text-lg font-bold ${user.level === 'kkid' ? 'text-pink-700' : 'text-teal-800'}`}>
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

        <Tabs 
          value={activeTab || (user.level === 'kkid' ? 'quiz' : 'welcome')} 
          onValueChange={setActiveTab}
          className="space-y-6"
        >
          {/* Grid Navigation Cards */}
          <TabsList className="grid grid-cols-2 md:grid-cols-4 gap-3 h-auto bg-transparent p-0">
            {/* K-Kid Dashboard : Quiz, Vidéo, Récompense */}
            {user.level === 'kkid' ? (
              <>
                <TabsTrigger 
                  value="quiz" 
                  className="h-24 data-[state=active]:bg-pink-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
                >
                  <Trophy className="w-8 h-8 text-pink-600 data-[state=active]:text-white" />
                  <span className="text-xs font-semibold">🧠 Quiz</span>
                </TabsTrigger>
                
                <TabsTrigger 
                  value="videos" 
                  className="h-24 data-[state=active]:bg-pink-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
                >
                  <Video className="w-8 h-8 text-pink-600 data-[state=active]:text-white" />
                  <span className="text-xs font-semibold">🎥 Vidéo</span>
                </TabsTrigger>
                
                <TabsTrigger 
                  value="rewards" 
                  className="h-24 data-[state=active]:bg-pink-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
                >
                  <Gift className="w-8 h-8 text-pink-600 data-[state=active]:text-white" />
                  <span className="text-xs font-semibold">🎁 Récompense</span>
                </TabsTrigger>
              </>
            ) : (
              /* Dashboard Normal pour les autres étudiants */
              <>
            <TabsTrigger 
              value="welcome" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Mail className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Bienvenue</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="club" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Sparkles className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">CLUB</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="mypack" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <GraduationCap className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Mon Pack</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="links" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <LinkIcon className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Liens</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="availability" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Calendar className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Mes Dispos</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="games" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Gamepad2 className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Jeu</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="conversations" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <MessageCircle className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Messages</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="documents" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Documents</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="summaries" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <BookOpen className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Résumés</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="progression" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <TrendingUp className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Progression & Défis</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="news" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Newspaper className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">News</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="kalamatheque" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Library className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Bibliothèque</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="profile" 
              className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <UserCircle className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Profil</span>
            </TabsTrigger>
            <TabsTrigger 
              value="treasure" 
              className="h-24 data-[state=active]:bg-amber-500 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Gift className="w-8 h-8 text-amber-500 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Coffre</span>
            </TabsTrigger>
              </>
            )}
          </TabsList>
          
          {/* Content Area */}
          <div className="flex-1">

          {/* Welcome Letter Tab */}
          <TabsContent value="welcome">
            <div className="space-y-6">
              {/* Ramadan Promo Banner */}
              <RamadanPromoBanner showButton={false} />
              
              {/* Trial Countdown - shows remaining days of free trial */}
              <TrialCountdown 
                registrationDate={user?.created_at} 
                onUpgradeClick={() => setActiveTab('mypack')}
              />
              
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
                          <span>Limite le temps d&apos;écran</span>
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
                    onClick={async () => {
                      try {
                        toast.info('Redirection vers Stripe...');
                        
                        // Get pack details based on user level
                        const packMapping = {
                          'kkid': { name: 'Pack K-Kid', amount: 15000 },
                          'beginner': { name: user.join_kalama_club ? 'Pack K-Débutant + Club' : 'Pack K-Débutant', amount: user.join_kalama_club ? 20000 : 15000 },
                          'intermediate': { name: user.join_kalama_club ? 'Pack K-Intermédiaire + Club' : 'Pack K-Intermédiaire', amount: user.join_kalama_club ? 25000 : 20000 },
                          'advanced': { name: user.join_kalama_club ? 'Pack K-Avancé + Club' : 'Pack K-Avancé', amount: user.join_kalama_club ? 30000 : 25000 }
                        };
                        
                        const pack = packMapping[user.level];
                        
                        if (!pack) {
                          toast.error('Erreur : Pack non trouvé');
                          return;
                        }
                        
                        // Call backend to create Stripe session with promo code
                        const response = await apiClient.post('/payments/create-checkout', {
                          plan_name: pack.name,
                          plan_level: user.level,
                          amount: pack.amount,
                          currency: 'FCFA',
                          promo_code: 'promo_1SYGM3I4faCc3GWYbdYRPXX8'
                        });
                        
                        // Redirect to Stripe Checkout
                        if (response.data.checkout_url) {
                          window.location.href = response.data.checkout_url;
                        } else {
                          toast.error('Erreur lors de la création de la session de paiement');
                        }
                      } catch (error) {
                        console.error('Payment error:', error);
                        toast.error(error.response?.data?.detail || 'Erreur de paiement. Contactez l\'administration.');
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

          {/* Mes Dispos Tab - Disponibilités de l'étudiant */}
          <TabsContent value="availability">
            <StudentAvailability />
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
          {/* K-Kid Quiz Tab - Jeu de Flashcards */}
          {user.level === 'kkid' && (
            <TabsContent value="quiz">
              <Card className="border-pink-200">
                <CardHeader className="bg-gradient-to-r from-pink-100 to-purple-100">
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="w-6 h-6 text-pink-600" />
                    🧠 Quiz & Flashcards
                  </CardTitle>
                  <CardDescription>Joue aux flashcards pour apprendre en t&apos;amusant !</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <KidsFlashcards />
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* K-Kid Videos Tab - Playlist YouTube + Vidéos Prof */}
          {user.level === 'kkid' && (
            <TabsContent value="videos">
              <Card className="border-pink-200">
                <CardHeader className="bg-gradient-to-r from-pink-100 to-purple-100">
                  <CardTitle className="flex items-center gap-2">
                    <Video className="w-6 h-6 text-pink-600" />
                    🎥 Mes Vidéos
                  </CardTitle>
                  <CardDescription>Regarde des vidéos amusantes pour apprendre l&apos;anglais</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <KidsVideoPlaylist />
                </CardContent>
              </Card>
            </TabsContent>
          )}
          
          {/* Rewards Tab for K-Kids */}
          {user.level === 'kkid' && (
            <TabsContent value="rewards">
              <Card className="border-pink-200">
                <CardHeader className="bg-gradient-to-r from-amber-100 to-yellow-100">
                  <CardTitle className="flex items-center gap-2">
                    <Gift className="w-6 h-6 text-amber-600" />
                    🎁 Mes Récompenses
                  </CardTitle>
                  <CardDescription>Tes cadeaux et récompenses pour ton travail!</CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  <TreasureChest />
                  <div className="mt-6">
                    <h4 className="font-semibold text-lg mb-4 text-pink-700">🎉 Cadeaux du Weekend</h4>
                    <WeekendGifts user={user} />
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          )}

          {/* Games Tab */}
          <TabsContent value="games">
            <StudentGames />
          </TabsContent>

          {/* Conversations Tab */}
          <TabsContent value="conversations">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Conversation avec le professeur */}
              <Card className="border-teal-100">
                <CardHeader className="bg-teal-50">
                  <CardTitle className="text-teal-800">👨‍🏫 Mon Professeur</CardTitle>
                  <CardDescription>
                    {teacher ? `${teacher.first_name} ${teacher.last_name}` : 'Aucun professeur assigné'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  {!teacher ? (
                    <div className="text-center py-12">
                      <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm">Vous n&apos;avez pas encore de professeur assigné</p>
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

              {/* Conversation avec l'admin */}
              <Card className="border-teal-100">
                <CardHeader className="bg-teal-50">
                  <CardTitle className="text-teal-800">👤 Administration</CardTitle>
                  <CardDescription>
                    Contactez l&apos;équipe MyKalama
                  </CardDescription>
                </CardHeader>
                <CardContent className="pt-6">
                  {admin ? (
                    <ConversationChat
                      recipientId={admin.id}
                      recipientName="Admin KALAMA"
                      currentUserId={user?.id}
                    />
                  ) : (
                    <div className="text-center py-12">
                      <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 text-sm">Chargement...</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            <StudentDocuments />
          </TabsContent>

          {/* Résumés de Cours Tab */}
          <TabsContent value="summaries">
            <StudentCourseSummaries />
          </TabsContent>

          {/* Ma Progression & Défis Tab (Fusionné) */}
          <TabsContent value="progression">
            <div className="space-y-6">
              <WeeklyChallenges />
              <StudentProgression />
            </div>
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

          {/* Coffre aux Trésors Tab */}
          <TabsContent value="treasure">
            <TreasureChest />
          </TabsContent>
          </div>
        </Tabs>
      </div>

      {/* Documents removed - use Messages with attachments instead */}
    </div>
  );
};

export default StudentDashboard;
