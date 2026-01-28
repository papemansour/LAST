import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { LogOut, Users, BookOpen, Calendar, MessageCircle, Send, Video, FileText, Upload, Play, Pause, Square, Clock, Heart, Mail, Sparkles, Key, Gamepad2, Timer, Newspaper, Library, UserCircle } from 'lucide-react';
import AvailabilityScheduler from '../components/AvailabilityScheduler';
import ConversationChat from '../components/ConversationChat';
import NewsManager from '../components/NewsManager';
import WelcomeLetter from '../components/WelcomeLetter';
import DonationButton from '../components/DonationButton';
import KalamaClub from '../components/KalamaClub';
import TeacherGames from '../components/TeacherGames';
import TeacherVideos from '../components/TeacherVideos';
import TeacherGroupCodeManager from '../components/TeacherGroupCodeManager';
import DocumentsManager from '../components/DocumentsManager';
import TeacherMeetLinks from '../components/TeacherMeetLinks';
import GiftWelcomeLetter from '../components/GiftWelcomeLetter';
import TeacherCourseSummaries from '../components/TeacherCourseSummaries';
// ActivityFeed removed

const TeacherDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [students, setStudents] = useState([]);
  const [courses, setCourses] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);
  const [studentHomeworks, setStudentHomeworks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showWelcomeGift, setShowWelcomeGift] = useState(false);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [messageContent, setMessageContent] = useState('');
  const [isTimerRunning, setIsTimerRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [sessionStart, setSessionStart] = useState(null);
  const [pauseStart, setPauseStart] = useState(null);
  const [pausedDuration, setPausedDuration] = useState(0);
  
  const [courseData, setCourseData] = useState({
    title: '',
    description: '',
    level: '',
    schedule: '',
    student_id: '',
    student_email: '',
    meet_link: ''
  });

  const [kkidVideos, setKkidVideos] = useState([]);
  const [uploadingFile, setUploadingFile] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    let interval;
    if (isTimerRunning && !isPaused) {
      interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - sessionStart - pausedDuration) / 1000));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isTimerRunning, isPaused, sessionStart, pausedDuration]);

  const fetchData = async () => {
    try {
      const [userRes, studentsRes, coursesRes, conversationsRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/teacher/my-students'),
        apiClient.get('/teacher/my-courses'),
        apiClient.get('/messages/my-conversations')
      ]);
      
      setUser(userRes.data);
      setStudents(studentsRes.data);
      setCourses(coursesRes.data);
      setConversations(conversationsRes.data);
      
      // Check if first login to show welcome gift
      if (userRes.data.first_login) {
        setShowWelcomeGift(true);
      }
      
      setLoading(false);
    } catch (error) {
      toast.error('Erreur de chargement');
      navigate('/login');
    }
  };

  const generateGoogleMeetLink = () => {
    const meetId = Math.random().toString(36).substring(2, 15);
    const meetLink = `https://meet.google.com/${meetId}`;
    setCourseData({ ...courseData, meet_link: meetLink });
    toast.success('Lien Google Meet généré!');
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    if (courseData.student_email && !courseData.student_email.includes('@')) {
      toast.error('Email étudiant invalide');
      return;
    }
    try {
      await apiClient.post('/teacher/create-course', courseData);
      toast.success('Cours créé avec succès! L\'étudiant recevra le lien Google Meet par email.');
      setCourseData({ title: '', description: '', level: '', schedule: '', student_id: '', student_email: '', meet_link: '' });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la création du cours');
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Vérifier la taille (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('Fichier trop volumineux (max 10MB)');
      return;
    }
    
    setUploadingFile(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await apiClient.post('/teacher/upload-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setDocumentData({ ...documentData, file_url: response.data.file_url });
      toast.success('Fichier téléchargé avec succès!');
    } catch (error) {
      toast.error('Erreur lors du téléchargement');
    } finally {
      setUploadingFile(false);
    }
  };

  const handleSendDocument = async (e) => {
    e.preventDefault();
    if (!documentData.file_url) {
      toast.error('Veuillez télécharger un fichier ou entrer une URL');
      return;
    }
    try {
      // Choisir l'endpoint en fonction du destinataire
      if (documentData.recipient_type === 'admin') {
        await apiClient.post('/teacher/send-document-to-admin', {
          title: documentData.title,
          description: documentData.description,
          file_url: documentData.file_url
        });
      } else {
        await apiClient.post('/teacher/send-document', documentData);
      }
      toast.success('Document envoyé avec succès!');
      setDocumentData({ title: '', description: '', recipient_type: 'student', recipient_id: '', file_url: '', file: null });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du document');
    }
  };

  const handleStartSession = async () => {
    setIsTimerRunning(true);
    setIsPaused(false);
    setSessionStart(Date.now());
    setPausedDuration(0);
    setElapsedTime(0);
    
    try {
      await apiClient.post('/teacher/session/start');
      toast.success('Session démarrée!');
    } catch (error) {
      toast.error('Erreur lors du démarrage');
    }
  };

  const handlePauseSession = async () => {
    if (isPaused) {
      // Reprise
      setPausedDuration(pausedDuration + (Date.now() - pauseStart));
      setIsPaused(false);
      try {
        await apiClient.post('/teacher/session/resume');
        toast.info('Session reprise');
      } catch (error) {
        toast.error('Erreur');
      }
    } else {
      // Pause
      setPauseStart(Date.now());
      setIsPaused(true);
      try {
        await apiClient.post('/teacher/session/pause', { elapsed_time: elapsedTime });
        toast.info('Session en pause');
      } catch (error) {
        toast.error('Erreur');
      }
    }
  };

  const handleEndSession = async () => {
    try {
      await apiClient.post('/teacher/session/end', {
        total_time: elapsedTime,
        paused_duration: Math.floor(pausedDuration / 1000)
      });
      toast.success('Session terminée et envoyée à l\'admin!');
      setIsTimerRunning(false);
      setIsPaused(false);
      setElapsedTime(0);
      setSessionStart(null);
      setPauseStart(null);
      setPausedDuration(0);
    } catch (error) {
      toast.error('Erreur lors de la fin de session');
    }
  };

  const handleSelectRecipient = async (recipient) => {
    setSelectedRecipient(recipient);
    try {
      const response = await apiClient.get(`/messages/conversation/${recipient.id}`);
      setMessages(response.data);
    } catch (error) {
      toast.error('Erreur de chargement des messages');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!selectedRecipient || !messageContent.trim()) return;
    
    try {
      await apiClient.post('/messages/send', {
        to_user_id: selectedRecipient.id,
        content: messageContent
      });
      setMessageContent('');
      handleSelectRecipient(selectedRecipient);
      toast.success('Message envoyé!');
    } catch (error) {
      toast.error('Erreur lors de l\'envoi');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
    toast.success('Déconnexion réussie');
  };

  const formatTime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  const adminUser = conversations.find(u => u.role === 'admin');
  const availableRecipients = [adminUser, ...students].filter(Boolean);

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
        <div className="mb-4 sm:mb-8">
          <h2 className="text-2xl sm:text-4xl font-bold text-gray-900 mb-2">Espace Professeur</h2>
          <p className="text-gray-600">Bienvenue {user?.first_name}!</p>
        </div>

        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card className="border-teal-100">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Mes étudiants</CardTitle>
              <Users className="h-4 w-4 text-teal-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-teal-600">{students.length}</div>
            </CardContent>
          </Card>

          <Card className="border-teal-100">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Mes cours</CardTitle>
              <BookOpen className="h-4 w-4 text-teal-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-teal-600">{courses.length}</div>
            </CardContent>
          </Card>

          <Card className="border-teal-100">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Messages</CardTitle>
              <MessageCircle className="h-4 w-4 text-teal-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-teal-600">{availableRecipients.length}</div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="welcome" className="space-y-6">
          <TabsList className="grid grid-cols-2 md:grid-cols-4 gap-3 h-auto bg-transparent p-0">
            <TabsTrigger value="welcome" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Mail className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Bienvenue</span>
            </TabsTrigger>
            <TabsTrigger value="club" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Sparkles className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">CLUB</span>
            </TabsTrigger>
            <TabsTrigger value="students" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Users className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Étudiants</span>
            </TabsTrigger>
            <TabsTrigger value="student-availability" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Calendar className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Dispo Étudiants</span>
            </TabsTrigger>
            <TabsTrigger value="courses" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <BookOpen className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Cours</span>
            </TabsTrigger>
            <TabsTrigger value="games" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Gamepad2 className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Jeu</span>
            </TabsTrigger>
            <TabsTrigger value="videos" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Video className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Vidéos K-Kid</span>
            </TabsTrigger>
            <TabsTrigger value="timer" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Timer className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Pointage</span>
            </TabsTrigger>
            <TabsTrigger value="messages" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <MessageCircle className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Messages</span>
            </TabsTrigger>
            <TabsTrigger value="documents" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <FileText className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Documents</span>
            </TabsTrigger>
            <TabsTrigger value="summaries" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <BookOpen className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Résumés</span>
            </TabsTrigger>
            <TabsTrigger value="schedule" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Calendar className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Horaires</span>
            </TabsTrigger>
            <TabsTrigger value="news" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Newspaper className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">News</span>
            </TabsTrigger>
            <TabsTrigger value="kalamatheque" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <Library className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Bibliothèque</span>
            </TabsTrigger>
            <TabsTrigger value="profile" className="h-24 data-[state=active]:bg-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2">
              <UserCircle className="w-8 h-8 text-green-600 data-[state=active]:text-white" />
              <span className="text-xs font-semibold">Profil</span>
            </TabsTrigger>
          </TabsList>

          {/* Welcome Letter Tab */}
          <TabsContent value="welcome">
            <WelcomeLetter />
          </TabsContent>

          {/* KALAMA CLUB Tab */}
          <TabsContent value="club">
            <KalamaClub userRole="teacher" />
          </TabsContent>

          {/* Students Tab */}
          <TabsContent value="students">
            <Card className="border-teal-100">
              <CardHeader>
                <CardTitle className="text-teal-800">Liste de mes étudiants</CardTitle>
                <CardDescription>Étudiants que vous encadrez</CardDescription>
              </CardHeader>
              <CardContent>
                {students.length === 0 ? (
                  <p className="text-gray-500">Aucun étudiant assigné</p>
                ) : (
                  <div className="space-y-4">
                    {students.map((student) => (
                      <div key={student.id} className="p-4 border border-teal-100 rounded-lg flex justify-between items-center hover:bg-teal-50 transition">
                        <div>
                          <h3 className="font-semibold text-teal-800">{student.first_name} {student.last_name}</h3>
                          <p className="text-sm text-gray-600">{student.email}</p>
                          <p className="text-sm text-gray-500">Niveau: {student.level}</p>
                        </div>
                        <div className="text-sm text-gray-400">
                          {student.phone}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Group Codes Tab */}
          <TabsContent value="group-codes">
            <TeacherGroupCodeManager />
          </TabsContent>


          <TabsContent value="courses">
            <div className="grid md:grid-cols-2 gap-6">
              <Card className="border-teal-100">
                <CardHeader>
                  <CardTitle className="text-teal-800">Créer un cours avec Google Meet</CardTitle>
                  <CardDescription>Ajoutez un nouveau cours et générez un lien Meet</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateCourse} className="space-y-4">
                    <div>
                      <Label htmlFor="title">Titre</Label>
                      <Input
                        id="title"
                        required
                        value={courseData.title}
                        onChange={(e) => setCourseData({ ...courseData, title: e.target.value })}
                        className="border-white/30 focus:border-teal-500"
                      />
                    </div>
                    <div>
                      <Label htmlFor="description">Description</Label>
                      <Textarea
                        id="description"
                        required
                        value={courseData.description}
                        onChange={(e) => setCourseData({ ...courseData, description: e.target.value })}
                        className="border-white/30 focus:border-teal-500"
                      />
                    </div>
                    <div>
                      <Label htmlFor="level">Niveau</Label>
                      <Select
                        value={courseData.level}
                        onValueChange={(value) => setCourseData({ ...courseData, level: value })}
                        required
                      >
                        <SelectTrigger className="border-white/30">
                          <SelectValue placeholder="Sélectionner" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="beginner">Débutant</SelectItem>
                          <SelectItem value="intermediate">Intermédiaire</SelectItem>
                          <SelectItem value="advanced">Pack professionnel</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="student">Étudiant assigné</Label>
                      <Select
                        value={courseData.student_id}
                        onValueChange={(value) => setCourseData({ ...courseData, student_id: value })}
                        required
                      >
                        <SelectTrigger className="border-white/30">
                          <SelectValue placeholder="Sélectionner un étudiant" />
                        </SelectTrigger>
                        <SelectContent>
                          {students.map((student) => (
                            <SelectItem key={student.id} value={student.id}>
                              {student.first_name} {student.last_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="student_email">Email de l'étudiant (pour recevoir le lien Meet)</Label>
                      <Input
                        id="student_email"
                        type="email"
                        value={courseData.student_email}
                        onChange={(e) => setCourseData({ ...courseData, student_email: e.target.value })}
                        placeholder="etudiant@example.com"
                        className="border-white/30 focus:border-teal-500"
                      />
                    </div>
                    <div>
                      <Label htmlFor="schedule">Horaire</Label>
                      <Input
                        id="schedule"
                        required
                        value={courseData.schedule}
                        onChange={(e) => setCourseData({ ...courseData, schedule: e.target.value })}
                        placeholder="Ex: Lundi 18h-20h"
                        className="border-white/30 focus:border-teal-500"
                      />
                    </div>
                    <div>
                      <Label htmlFor="meet_link">Lien Google Meet</Label>
                      <div className="flex gap-2">
                        <Input
                          id="meet_link"
                          value={courseData.meet_link}
                          onChange={(e) => setCourseData({ ...courseData, meet_link: e.target.value })}
                          placeholder="Générer ou coller un lien"
                          className="border-white/30 focus:border-teal-500"
                        />
                        <Button type="button" onClick={generateGoogleMeetLink} className="bg-teal-600 hover:bg-teal-700">
                          <Video className="w-4 h-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">Email: mykalamaenglish@gmail.com</p>
                    </div>
                    <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700">
                      Créer le cours
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="border-teal-100">
                <CardHeader>
                  <CardTitle className="text-teal-800">Mes cours</CardTitle>
                  <CardDescription>Liste de vos cours avec liens Meet</CardDescription>
                </CardHeader>
                <CardContent>
                  {courses.length === 0 ? (
                    <p className="text-gray-500">Aucun cours créé</p>
                  ) : (
                    <div className="space-y-4 max-h-[500px] overflow-y-auto">
                      {courses.map((course) => (
                        <div key={course.id} className="p-4 border border-teal-100 rounded-lg hover:bg-teal-50 transition">
                          <h3 className="font-semibold text-teal-800">{course.title}</h3>
                          <p className="text-sm text-gray-600 mt-1">{course.description}</p>
                          {course.meet_link && (
                            <a href={course.meet_link} target="_blank" rel="noopener noreferrer" className="text-sm text-teal-600 hover:underline flex items-center gap-1 mt-2">
                              <Video className="w-4 h-4" />
                              Rejoindre le cours
                            </a>
                          )}
                          <div className="flex gap-4 mt-2">
                            <span className="text-xs bg-teal-100 text-teal-700 px-2 py-1 rounded">
                              {course.level}
                            </span>
                            <span className="text-xs text-gray-500">{course.schedule}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>


          <TabsContent value="games">
            <TeacherGames students={students} />
          </TabsContent>

          <TabsContent value="videos">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Video className="w-6 h-6 text-pink-600" />
                  🎥 Vidéos pour K-Kids
                </CardTitle>
                <CardDescription>Uploadez et partagez des vidéos éducatives avec tous les K-Kids</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Formulaire d'upload */}
                <Card className="border-white/30 bg-pink-50">
                  <CardHeader>
                    <CardTitle className="text-lg">📤 Envoyer une nouvelle vidéo</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={async (e) => {
                      e.preventDefault();
                      const formData = new FormData(e.target);
                      const videoData = {
                        title: formData.get('video_title'),
                        description: formData.get('video_description'),
                        video_url: formData.get('video_url'),
                        student_id: formData.get('kkid_student_id')
                      };
                      
                      if (!videoData.student_id) {
                        toast.error('Veuillez sélectionner un élève K-Kid');
                        return;
                      }
                      
                      try {
                        await apiClient.post('/teacher/send-kkid-video', videoData);
                        toast.success('Vidéo envoyée à l\'élève K-Kid!');
                        e.target.reset();
                        fetchData();
                      } catch (error) {
                        toast.error(error.response?.data?.detail || 'Erreur lors de l\'envoi');
                      }
                    }} className="space-y-4">
                      <div>
                        <Label htmlFor="kkid_student_id">Sélectionner l'élève K-Kid</Label>
                        <select
                          id="kkid_student_id"
                          name="kkid_student_id"
                          required
                          className="w-full p-2 border rounded-md"
                        >
                          <option value="">-- Choisir un élève K-Kid --</option>
                          {students.filter(s => s.level === 'kkid').map(student => (
                            <option key={student.id} value={student.id}>
                              {student.first_name} {student.last_name}
                            </option>
                          ))}
                        </select>
                      </div>
                      
                      <div>
                        <Label htmlFor="video_title">Titre de la vidéo</Label>
                        <Input
                          id="video_title"
                          name="video_title"
                          placeholder="Ex: Leçon d'anglais - Les couleurs"
                          required
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="video_description">Description</Label>
                        <Textarea
                          id="video_description"
                          name="video_description"
                          placeholder="Courte description de la vidéo..."
                          rows={3}
                        />
                      </div>
                      
                      <div>
                        <Label htmlFor="video_file_upload">📁 Uploader une vidéo</Label>
                        <input
                          type="file"
                          id="video_file_upload"
                          accept="video/mp4,video/webm,video/mov,video/avi"
                          onChange={async (e) => {
                            const file = e.target.files[0];
                            if (file) {
                              try {
                                setUploadingFile(true);
                                const fd = new FormData();
                                fd.append('file', file);
                                const response = await apiClient.post('/upload', fd, {
                                  headers: { 'Content-Type': 'multipart/form-data' }
                                });
                                document.getElementById('video_url').value = response.data.file_url;
                                toast.success('Vidéo uploadée!');
                              } catch (error) {
                                toast.error('Erreur upload');
                              } finally {
                                setUploadingFile(false);
                              }
                            }
                          }}
                          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-pink-50 file:text-pink-700 hover:file:bg-pink-100"
                        />
                        <p className="text-xs text-gray-500 mt-1">🎥 MP4, WebM, MOV, AVI - max 50MB</p>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-px bg-gray-300"></div>
                        <span className="text-xs text-gray-500">OU</span>
                        <div className="flex-1 h-px bg-gray-300"></div>
                      </div>
                      
                      <div>
                        <Label htmlFor="video_url">🔗 Lien vidéo (YouTube, etc.)</Label>
                        <Input
                          id="video_url"
                          name="video_url"
                          placeholder="https://www.youtube.com/watch?v=..."
                          required
                        />
                        <p className="text-xs text-gray-500 mt-1">YouTube, Vimeo, ou fichier uploadé</p>
                      </div>
                      
                      <Button type="submit" className="w-full bg-pink-600 hover:bg-pink-700" disabled={uploadingFile}>
                        {uploadingFile ? '⏳ Upload en cours...' : '📤 Envoyer aux K-Kids'}
                      </Button>
                    </form>
                  </CardContent>
                </Card>
                
                {/* Liste des vidéos existantes */}
                <div>
                  <h3 className="text-lg font-semibold mb-4">📚 Vidéos envoyées</h3>
                  <Button 
                    onClick={async () => {
                      try {
                        const res = await apiClient.get('/kkid/videos');
                        setKkidVideos(res.data);
                        toast.success('Liste actualisée');
                      } catch (error) {
                        toast.error('Erreur de chargement');
                      }
                    }}
                    className="mb-4 bg-pink-600 hover:bg-pink-700"
                  >
                    🔄 Actualiser
                  </Button>
                  
                  {kkidVideos.length === 0 ? (
                    <p className="text-sm text-gray-500">Aucune vidéo envoyée pour le moment</p>
                  ) : (
                    <div className="grid md:grid-cols-2 gap-4 mt-4">
                      {kkidVideos.map(video => (
                        <Card key={video.id} className="border-white/30">
                          <CardContent className="p-4">
                            <h4 className="font-semibold mb-2">{video.title}</h4>
                            <p className="text-sm text-gray-600 mb-2">{video.description}</p>
                            <p className="text-xs text-gray-500">
                              Pour : <strong>{video.student_name}</strong>
                            </p>
                            <p className="text-xs text-gray-400">
                              {new Date(video.created_at).toLocaleDateString('fr-FR')}
                            </p>
                            <div className="flex gap-2 mt-3">
                              <Button
                                size="sm"
                                onClick={() => window.open(video.video_url, '_blank')}
                                className="bg-pink-600 hover:bg-pink-700"
                              >
                                📺 Voir
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={async () => {
                                  if (window.confirm('Supprimer cette vidéo ?')) {
                                    try {
                                      await apiClient.delete(`/teacher/delete-kkid-video/${video.id}`);
                                      toast.success('Vidéo supprimée');
                                      const res = await apiClient.get('/kkid/videos');
                                      setKkidVideos(res.data);
                                    } catch (error) {
                                      toast.error('Erreur de suppression');
                                    }
                                  }
                                }}
                                className="border-red-500 text-red-600"
                              >
                                🗑️
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="timer">
            <Card className="border-teal-100">
              <CardHeader>
                <CardTitle className="text-teal-800">Pointage de session</CardTitle>
                <CardDescription>Chronométrez vos cours et envoyez les données à l'admin</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col items-center justify-center py-12 space-y-8">
                  <div className="relative">
                    <div className="w-64 h-64 rounded-full border-8 border-teal-100 flex items-center justify-center bg-gradient-to-br from-teal-50 to-white shadow-xl">
                      <div className="text-center">
                        <Clock className="w-12 h-12 text-teal-600 mx-auto mb-4" />
                        <div className="text-5xl font-bold text-teal-600 font-mono">
                          {formatTime(elapsedTime)}
                        </div>
                        <div className="text-sm text-gray-500 mt-2">
                          {isPaused ? 'En pause' : isTimerRunning ? 'En cours...' : 'Prêt'}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    {!isTimerRunning ? (
                      <Button
                        onClick={handleStartSession}
                        className="bg-green-600 hover:bg-green-700 px-8 py-6 text-lg"
                      >
                        <Play className="w-6 h-6 mr-2" />
                        Commencer le cours
                      </Button>
                    ) : (
                      <>
                        <Button
                          onClick={handlePauseSession}
                          className="bg-yellow-600 hover:bg-yellow-700 px-8 py-6 text-lg"
                        >
                          {isPaused ? (
                            <>
                              <Play className="w-6 h-6 mr-2" />
                              Reprendre
                            </>
                          ) : (
                            <>
                              <Pause className="w-6 h-6 mr-2" />
                              Pause
                            </>
                          )}
                        </Button>
                        <Button
                          onClick={handleEndSession}
                          className="bg-red-600 hover:bg-red-700 px-8 py-6 text-lg"
                        >
                          <Square className="w-6 h-6 mr-2" />
                          Terminer
                        </Button>
                      </>
                    )}
                  </div>

                  <div className="text-center max-w-md">
                    <p className="text-sm text-gray-600">
                      Les données de temps seront automatiquement envoyées à l'administrateur lorsque vous terminerez la session.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="messages">
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="border-teal-100">
                <CardHeader>
                  <CardTitle className="text-teal-800">Conversations</CardTitle>
                  <CardDescription>Admin et étudiants</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-[500px] overflow-y-auto">
                    {availableRecipients.map((recipient) => (
                      <button
                        key={recipient.id}
                        onClick={() => handleSelectRecipient(recipient)}
                        className={`w-full p-3 rounded-lg text-left transition ${
                          selectedRecipient?.id === recipient.id
                            ? 'bg-teal-100 border-2 border-teal-600'
                            : 'bg-gray-50 hover:bg-teal-50 border-2 border-transparent'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold">
                            {recipient.first_name?.charAt(0)}{recipient.last_name?.charAt(0)}
                          </div>
                          <div>
                            <p className="font-semibold text-sm">{recipient.first_name} {recipient.last_name}</p>
                            <p className="text-xs text-gray-500">{recipient.role === 'admin' ? 'Administrateur' : 'Étudiant'}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card className="md:col-span-2 border-teal-100">
                <CardHeader>
                  <CardTitle className="text-teal-800">
                    {selectedRecipient ? `${selectedRecipient.first_name} ${selectedRecipient.last_name}` : 'Sélectionnez une conversation'}
                  </CardTitle>
                  <CardDescription>
                    {selectedRecipient ? (selectedRecipient.role === 'admin' ? 'Administrateur' : 'Étudiant') : ''}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {!selectedRecipient ? (
                    <div className="text-center py-12">
                      <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500">Sélectionnez un contact pour commencer la conversation</p>
                    </div>
                  ) : (
                    <ConversationChat
                      recipientId={selectedRecipient.id}
                      recipientName={`${selectedRecipient.first_name} ${selectedRecipient.last_name}`}
                      currentUserId={user.id}
                    />
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            <DocumentsManager userRole="teacher" />
          </TabsContent>

          {/* Course Summaries Tab - Résumés de cours */}
          <TabsContent value="summaries">
            <TeacherCourseSummaries />
          </TabsContent>

          {/* Meet Links Tab - Cours en ligne */}
          <TabsContent value="meet-links">
            <TeacherMeetLinks />
          </TabsContent>

          {/* Schedule Tab - Mes horaires */}
          <TabsContent value="schedule">
            <AvailabilityScheduler apiClient={apiClient} />
          </TabsContent>

          {/* News Tab */}
          <TabsContent value="news">
            <NewsManager />
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
                        <span className="text-gray-600">Rôle:</span>
                        <span className="font-semibold">Professeur</span>
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
                          className="border-white/30 focus:border-teal-500"
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
                          className="border-white/30 focus:border-teal-500"
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
                          className="border-white/30 focus:border-teal-500"
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
        </Tabs>
      </div>
      
      {/* Document Preview Dialog */}
    </div>
  );
};

export default TeacherDashboard;
