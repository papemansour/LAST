import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
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
import { LogOut, Users, UserCheck, UserPlus, Award, BookOpen, Clock, Send, FileText, DollarSign, Lock, Trash2, Phone, CalendarDays, BarChart3, TrendingUp, Plane, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import KalamathequeAdmin from '../components/KalamathequeAdmin';
import NewsManager from '../components/NewsManager';
import ConversationChat from '../components/ConversationChat';
import KalamaClub from '../components/KalamaClub';
import TestQuestionsManager from '../components/TestQuestionsManager';
import AdminTrash from '../components/AdminTrash';
import DocumentsManager from '../components/DocumentsManager';
import BadgesManager from '../components/BadgesManager';
import AdminStudentsAvailability from '../components/AdminStudentsAvailability';
import AdminMonthlyHours from '../components/AdminMonthlyHours';
import AdminAnalytics from '../components/AdminAnalytics';
import CreateStudentForm from '../components/CreateStudentForm';
import ImportStudentsCSV from '../components/ImportStudentsCSV';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [user, setUser] = useState(null);
  const [pendingRegistrations, setPendingRegistrations] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [testResults, setTestResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [teacherData, setTeacherData] = useState({
    first_name: '',
    last_name: ''
  });
  const [selectedStudent, setSelectedStudent] = useState('');
  const [selectedTeacher, setSelectedTeacher] = useState('');
  const [showChangeTeacherDialog, setShowChangeTeacherDialog] = useState(false);
  const [studentToChangeTeacher, setStudentToChangeTeacher] = useState(null);
  const [newTeacherForStudent, setNewTeacherForStudent] = useState('');
  const [sessions, setSessions] = useState([]);
  const [teacherSessions, setTeacherSessions] = useState([]);
  const [teacherAvailability, setTeacherAvailability] = useState([]);
  const [selectedStudents, setSelectedStudents] = useState([]);
  const [levelFilter, setLevelFilter] = useState('all');
  const [prices, setPrices] = useState({
    kkid_eur: 30,
    kkid_fcfa: 10000,
    kkid_discount: 0,
    kkid_discount_fcfa: 0,
    beginner_eur: 76,
    beginner_discount: 0,
    beginner_fcfa: 50000,
    beginner_discount_fcfa: 0,
    intermediate_eur: 90,
    intermediate_discount: 0,
    intermediate_fcfa: 59000,
    intermediate_discount_fcfa: 0,
    advanced_eur: 102,
    advanced_discount: 0,
    advanced_fcfa: 67000,
    advanced_discount_fcfa: 0
  });
  const [messages, setMessages] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [selectedRecipient, setSelectedRecipient] = useState(null);
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [messageContent, setMessageContent] = useState('');
  const [documentToSend, setDocumentToSend] = useState({
    title: '',
    description: '',
    file_url: '',
    recipient_id: ''
  });
  const [activeConversation, setActiveConversation] = useState(null);
  const [conversationMode, setConversationMode] = useState('individual'); // 'individual' ou 'group'
  
  // Leave requests state
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [leaveComment, setLeaveComment] = useState('');

  useEffect(() => {
    fetchData();
    fetchLeaveRequests();
  }, []);

  const fetchLeaveRequests = async () => {
    try {
      const response = await apiClient.get('/admin/leave-requests');
      setLeaveRequests(response.data || []);
    } catch (error) {
      console.error('Error fetching leave requests:', error);
    }
  };

  const handleApproveLeave = async (leaveId) => {
    try {
      await apiClient.post(`/admin/leave-request/${leaveId}/approve`, { comment: leaveComment });
      toast.success('✅ Congé approuvé');
      setLeaveComment('');
      fetchLeaveRequests();
    } catch (error) {
      toast.error('Erreur lors de l\'approbation');
    }
  };

  const handleRejectLeave = async (leaveId) => {
    try {
      await apiClient.post(`/admin/leave-request/${leaveId}/reject`, { comment: leaveComment });
      toast.success('❌ Congé refusé');
      setLeaveComment('');
      fetchLeaveRequests();
    } catch (error) {
      toast.error('Erreur lors du refus');
    }
  };

  const fetchData = async () => {
    try {
      const [userRes, pendingRes, usersRes, resultsRes, sessionsRes, conversationsRes, availabilityRes, teacherSessionsRes, pricingRes] = await Promise.all([
        apiClient.get('/auth/me'),
        apiClient.get('/admin/pending-registrations'),
        apiClient.get('/admin/all-users'),
        apiClient.get('/tests/results/all'),
        apiClient.get('/admin/session-notifications'),
        apiClient.get('/messages/my-conversations'),
        apiClient.get('/admin/all-teacher-availability'),
        apiClient.get('/admin/teacher-sessions'),
        apiClient.get('/pricing')
      ]);
      
      setUser(userRes.data);
      setPendingRegistrations(pendingRes.data);
      setAllUsers(usersRes.data);
      setTestResults(resultsRes.data);
      setSessions(sessionsRes.data || []);
      setConversations(conversationsRes.data || []);
      setTeacherAvailability(availabilityRes.data || []);
      setTeacherSessions(teacherSessionsRes.data || []);
      setPrices(pricingRes.data || prices);
      setLoading(false);
    } catch (error) {
      toast.error('Erreur de chargement');
      navigate('/login');
    }
  };

  // Filtrer les étudiants par niveau
  const students = allUsers.filter(u => u.role === 'student');
  const filteredStudents = levelFilter === 'all' 
    ? students 
    : students.filter(s => s.level === levelFilter);

  // Gestion de la sélection multiple
  const toggleStudentSelection = (studentId) => {
    setSelectedStudents(prev => 
      prev.includes(studentId) 
        ? prev.filter(id => id !== studentId)
        : [...prev, studentId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedStudents.length === filteredStudents.length) {
      setSelectedStudents([]);
    } else {
      setSelectedStudents(filteredStudents.map(s => s.id));
    }
  };

  const deleteSelectedStudents = async () => {
    if (selectedStudents.length === 0) {
      toast.error('Aucun étudiant sélectionné');
      return;
    }

    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir supprimer ${selectedStudents.length} étudiant(s) ?`
    );

    if (!confirmed) return;

    try {
      // Supprimer chaque étudiant sélectionné
      await Promise.all(
        selectedStudents.map(id => 
          apiClient.delete(`/admin/delete-user/${id}`)
        )
      );
      
      toast.success(`${selectedStudents.length} étudiant(s) supprimé(s)`);
      setSelectedStudents([]);
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleChangeTeacher = async (studentId, newTeacherId) => {
    try {
      await apiClient.post(`/admin/change-student-teacher`, {
        student_id: studentId,
        new_teacher_id: newTeacherId
      });
      toast.success('Professeur changé avec succès !');
      fetchData();
    } catch (error) {
      console.error('Error changing teacher:', error);
      toast.error('Erreur lors du changement de professeur');
    }
  };

  const handleApprove = async (userId) => {
    try {
      const response = await apiClient.post(`/admin/approve-registration/${userId}`);
      toast.success(`Inscription approuvée! Email: ${response.data.email}, Mot de passe: ${response.data.temporary_password}`);
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'approbation');
    }
  };

  const handleCreateTeacher = async (e) => {
    e.preventDefault();
    try {
      const response = await apiClient.post('/admin/create-teacher', teacherData);
      toast.success(`Professeur créé! Email: ${response.data.email}, Mot de passe: ${response.data.temporary_password}`);
      setTeacherData({ first_name: '', last_name: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    }
  };

  const handleAssignTeacher = async () => {
    if (!selectedStudent || !selectedTeacher) {
      toast.error('Veuillez sélectionner un étudiant et un professeur');
      return;
    }
    try {
      await apiClient.post(`/admin/assign-teacher/${selectedStudent}/${selectedTeacher}`);
      toast.success('Professeur assigné avec succès!');
      setSelectedStudent('');
      setSelectedTeacher('');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'assignation');
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
    toast.success('Déconnexion réussie');
  };

  const handleResetPassword = async (userId, userEmail) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir réinitialiser le mot de passe de ${userEmail}?\n\nUn nouveau mot de passe temporaire sera généré et envoyé à l'utilisateur par email.`)) {
      return;
    }
    
    try {
      const response = await apiClient.post(`/admin/reset-user-password/${userId}`);
      toast.success(
        `Mot de passe réinitialisé avec succès!\n\nMot de passe temporaire: ${response.data.temporary_password}\n\n${response.data.email_sent ? '✅ Email envoyé à l\'utilisateur' : '⚠️ Email non envoyé (vérifier la configuration AWS SES)'}`,
        { duration: 8000 }
      );
      fetchData(); // Refresh data to show temporary password
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la réinitialisation du mot de passe');
    }
  };

  const handleUpdatePrices = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/admin/update-prices', prices);
      toast.success('Prix mis à jour avec succès!');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour des prix');
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

  const handleToggleRecipient = (recipient) => {
    const isSelected = selectedRecipients.find(r => r.id === recipient.id);
    if (isSelected) {
      setSelectedRecipients(selectedRecipients.filter(r => r.id !== recipient.id));
    } else {
      setSelectedRecipients([...selectedRecipients, recipient]);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (selectedRecipients.length === 0 || !messageContent.trim()) {
      toast.error('Sélectionnez au moins un destinataire');
      return;
    }
    
    try {
      // Send message to all selected recipients
      await Promise.all(
        selectedRecipients.map(recipient => 
          apiClient.post('/messages/send', {
            to_user_id: recipient.id,
            content: messageContent
          })
        )
      );
      setMessageContent('');
      toast.success(`Message envoyé à ${selectedRecipients.length} personne(s)!`);
    } catch (error) {
      toast.error('Erreur lors de l\'envoi');
    }
  };

  const handleSendDocument = async (e) => {
    e.preventDefault();
    if (selectedRecipients.length === 0) {
      toast.error('Sélectionnez au moins un destinataire');
      return;
    }
    
    try {
      // Send document to all selected recipients
      await Promise.all(
        selectedRecipients.map(recipient =>
          apiClient.post('/admin/send-document', {
            ...documentToSend,
            recipient_id: recipient.id,
            recipient_type: recipient.role
          })
        )
      );
      toast.success(`Document envoyé à ${selectedRecipients.length} personne(s)!`);
      setDocumentToSend({ title: '', description: '', file_url: '', recipient_id: '' });
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du document');
    }
  };

  // Document management removed - use Messages with attachments instead


  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const teachers = allUsers.filter(u => u.role === 'teacher');

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-green-600">KALAMAENGLISH - Admin</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">{user?.first_name} {user?.last_name}</span>
            <Button variant="outline" onClick={handleLogout} data-testid="admin-logout-button">
              <LogOut className="w-4 h-4 mr-2" />
              Déconnexion
            </Button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto px-4 py-12 max-w-7xl">
        <div className="mb-8">
          <h2 className="text-4xl font-bold text-gray-900 mb-2">Tableau de bord Admin</h2>
          <p className="text-gray-600">Gérez votre plateforme KALAMAENGLISH</p>
        </div>

        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">En attente</CardTitle>
              <UserCheck className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{pendingRegistrations.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Étudiants</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{students.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Professeurs</CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{teachers.length}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Tests passés</CardTitle>
              <Award className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{testResults.length}</div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="pending" className="space-y-6">
          {/* Grid Navigation Cards */}
          <TabsList className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 h-auto bg-transparent p-0">
            <TabsTrigger 
              value="pending" 
              data-testid="admin-tab-pending"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-red-500 data-[state=active]:to-red-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <UserCheck className="w-6 h-6" />
              <span className="text-xs font-semibold">En attente</span>
            </TabsTrigger>


            <TabsTrigger 
              value="students" 
              data-testid="admin-tab-students"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-teal-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Users className="w-6 h-6" />
              <span className="text-xs font-semibold">Étudiants</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="teachers" 
              data-testid="admin-tab-teachers"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-blue-500 data-[state=active]:to-blue-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <BookOpen className="w-6 h-6" />
              <span className="text-xs font-semibold">Professeurs</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="analytics" 
              data-testid="admin-tab-analytics"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-indigo-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <TrendingUp className="w-6 h-6" />
              <span className="text-xs font-semibold">📊 Analytics</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="assign" 
              data-testid="admin-tab-assign"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-purple-500 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <UserPlus className="w-6 h-6" />
              <span className="text-xs font-semibold">Assigner</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="attendance" 
              data-testid="admin-tab-attendance"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-orange-500 data-[state=active]:to-orange-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Clock className="w-6 h-6" />
              <span className="text-xs font-semibold">Assiduité</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="student-availability" 
              data-testid="admin-tab-student-availability"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-teal-500 data-[state=active]:to-teal-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <CalendarDays className="w-6 h-6" />
              <span className="text-xs font-semibold">Dispo Étudiants</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="monthly-hours" 
              data-testid="admin-tab-monthly-hours"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-cyan-500 data-[state=active]:to-cyan-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <BarChart3 className="w-6 h-6" />
              <span className="text-xs font-semibold">Récap Heures</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="results" 
              data-testid="admin-tab-results"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-yellow-500 data-[state=active]:to-yellow-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Award className="w-6 h-6" />
              <span className="text-xs font-semibold">Résultats</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="pricing" 
              data-testid="admin-tab-pricing"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-green-500 data-[state=active]:to-green-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <DollarSign className="w-6 h-6" />
              <span className="text-xs font-semibold">Prix</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="availability" 
              data-testid="admin-tab-availability"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-pink-500 data-[state=active]:to-pink-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Clock className="w-6 h-6" />
              <span className="text-xs font-semibold">Horaires</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="news" 
              data-testid="admin-tab-news"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-indigo-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-6 h-6" />
              <span className="text-xs font-semibold">📰 News</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="kalamatheque" 
              data-testid="admin-tab-kalamatheque"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-cyan-500 data-[state=active]:to-cyan-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <BookOpen className="w-6 h-6" />
              <span className="text-xs font-semibold">Kalamathèque</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="club" 
              data-testid="admin-tab-club"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-amber-500 data-[state=active]:to-amber-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Award className="w-6 h-6" />
              <span className="text-xs font-semibold">🏆 CLUB</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="conversations" 
              data-testid="admin-tab-conversations"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-rose-500 data-[state=active]:to-rose-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Send className="w-6 h-6" />
              <span className="text-xs font-semibold">💬 Messages</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="trash"
              data-testid="admin-tab-trash"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-gray-500 data-[state=active]:to-gray-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Trash2 className="w-6 h-6" />
              <span className="text-xs font-semibold">🗑️ Poubelle</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="documents" 
              data-testid="admin-tab-documents"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-purple-500 data-[state=active]:to-purple-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-6 h-6" />
              <span className="text-xs font-semibold">📄 Documents</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="test-questions" 
              data-testid="admin-tab-test-questions"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-blue-500 data-[state=active]:to-sky-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <FileText className="w-6 h-6" />
              <span className="text-xs font-semibold">📝 Questions Test</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="badges" 
              data-testid="admin-tab-badges"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-purple-500 data-[state=active]:to-pink-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Award className="w-6 h-6" />
              <span className="text-xs font-semibold">🏆 Badges</span>
            </TabsTrigger>
            
            <TabsTrigger 
              value="leave-requests" 
              data-testid="admin-tab-leave-requests"
              className="h-24 data-[state=active]:bg-gradient-to-br data-[state=active]:from-blue-500 data-[state=active]:to-indigo-600 data-[state=active]:text-white data-[state=active]:shadow-xl data-[state=active]:scale-105 bg-white/40 backdrop-blur-md hover:bg-white/60 border-2 border-white/30 rounded-xl transition-all duration-300 flex flex-col items-center justify-center gap-2 cursor-pointer"
            >
              <Plane className="w-6 h-6" />
              <span className="text-xs font-semibold">🏖️ Congés</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="pending">
            <Card>
              <CardHeader>
                <CardTitle>Inscriptions en attente</CardTitle>
                <CardDescription>Approuvez les nouvelles inscriptions</CardDescription>
              </CardHeader>
              <CardContent>
                {pendingRegistrations.length === 0 ? (
                  <p className="text-gray-500">Aucune inscription en attente</p>
                ) : (
                  <div className="space-y-4">
                    {pendingRegistrations.map((registration) => (
                      <div key={registration.id} className="p-4 border rounded-lg flex justify-between items-center">
                        <div>
                          <h3 className="font-semibold">{registration.first_name} {registration.last_name}</h3>
                          <p className="text-sm text-gray-600">{registration.email}</p>
                          <p className="text-sm text-gray-500">Téléphone: {registration.phone}</p>
                          <p className="text-sm text-gray-500">Niveau: {registration.level}</p>
                          {registration.preferred_slots && (
                            <p className="text-xs text-gray-400">Créneaux: {registration.preferred_slots}</p>
                          )}
                        </div>
                        <Button
                          onClick={() => handleApprove(registration.id)}
                          data-testid={`admin-approve-${registration.id}`}
                        >
                          Approuver
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="students">
            <Card>
              <CardHeader>
                <div className="flex justify-between items-center">
                  <CardTitle>Liste des étudiants</CardTitle>
                  <div className="flex gap-3 items-center">
                    {/* Bouton créer étudiant */}
                    <CreateStudentForm onStudentCreated={() => fetchStudents()} />
                    
                    {/* Bouton import CSV */}
                    <ImportStudentsCSV onImportComplete={() => fetchStudents()} />
                    
                    {/* Filtre par niveau */}
                    <select
                      value={levelFilter}
                      onChange={(e) => setLevelFilter(e.target.value)}
                      className="px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="all">Tous les niveaux</option>
                      <option value="beginner">Débutant</option>
                      <option value="intermediate">Intermédiaire</option>
                      <option value="advanced">Professionnel</option>
                    </select>

                    {/* Bouton suppression multiple */}
                    {selectedStudents.length > 0 && (
                      <Button
                        onClick={deleteSelectedStudents}
                        variant="destructive"
                        size="sm"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Supprimer ({selectedStudents.length})
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {filteredStudents.length === 0 ? (
                  <p className="text-gray-500">
                    {levelFilter === 'all' 
                      ? 'Aucun étudiant inscrit' 
                      : `Aucun étudiant de niveau ${levelFilter}`}
                  </p>
                ) : (
                  <React.Fragment>
                    {/* Checkbox "Tout sélectionner" */}
                    <div className="mb-4 pb-3 border-b flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={selectedStudents.length === filteredStudents.length && filteredStudents.length > 0}
                        onChange={toggleSelectAll}
                        className="h-4 w-4 text-teal-600 rounded border-gray-300 focus:ring-teal-500"
                      />
                      <label className="text-sm font-medium text-gray-700">
                        Tout sélectionner ({filteredStudents.length})
                      </label>
                    </div>

                    <div className="space-y-4">
                      {filteredStudents.map((student) => (
                      <div key={student.id} className="p-4 border rounded-lg">
                        <div className="flex justify-between items-start">
                          <div className="flex items-start gap-3 flex-1">
                            {/* Checkbox individuel */}
                            <input
                              type="checkbox"
                              checked={selectedStudents.includes(student.id)}
                              onChange={() => toggleStudentSelection(student.id)}
                              className="h-4 w-4 text-teal-600 rounded border-gray-300 focus:ring-teal-500 mt-1"
                            />
                            <div className="flex-1">
                            <h3 className="font-semibold">{student.first_name} {student.last_name}</h3>
                            <p className="text-sm text-gray-600">{student.email}</p>
                            {student.phone && (
                              <p className="text-sm text-gray-600 flex items-center gap-1">
                                <Phone className="h-3 w-3" />
                                {student.phone}
                              </p>
                            )}
                            <p className="text-sm text-gray-500">Niveau: {student.level}</p>
                            <p className="text-sm text-gray-600 flex items-center gap-2 mt-1">
                              👨‍🏫 Professeur: {student.assigned_teacher ? (teachers.find(t => t.id === student.assigned_teacher)?.first_name || 'Non assigné') : 'Non assigné'}
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => {
                                  setStudentToChangeTeacher(student);
                                  setNewTeacherForStudent(student.assigned_teacher || '');
                                  setShowChangeTeacherDialog(true);
                                }}
                                className="text-blue-600 hover:text-blue-700 p-1 h-6"
                              >
                                🔄 Changer
                              </Button>
                            </p>
                            {student.temporary_password && (
                              <p className="text-xs text-orange-600 font-semibold mt-1">
                                Mot de passe provisoire: {student.temporary_password}
                              </p>
                            )}
                            {student.current_password_plain && (
                              <p className="text-xs text-blue-600 font-semibold mt-1">
                                Mot de passe actuel: {student.current_password_plain}
                              </p>
                            )}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 rounded text-sm ${
                              student.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'
                            }`}>
                              {student.is_active ? 'Actif' : 'Inactif'}
                            </span>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={async () => {
                                try {
                                  await apiClient.post(`/admin/restrict-user/${student.id}`);
                                  toast.success(student.is_restricted ? 'Accès rétabli' : 'Accès restreint');
                                  fetchData();
                                } catch (error) {
                                  toast.error('Erreur');
                                }
                              }}
                              className={student.is_restricted ? 'border-green-500 text-green-600' : 'border-orange-500 text-orange-600'}
                            >
                              <Lock className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={async () => {
                                if (window.confirm(`Supprimer ${student.first_name} ${student.last_name} ?`)) {
                                  try {
                                    await apiClient.delete(`/admin/delete-user/${student.id}`);
                                    toast.success('Utilisateur supprimé');
                                    fetchData();
                                  } catch (error) {
                                    toast.error('Erreur de suppression');
                                  }
                                }
                              }}
                              className="border-red-500 text-red-600"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                    </div>
                  </React.Fragment>
                )}
              </CardContent>
            </Card>
          </TabsContent>


          <TabsContent value="teachers">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Créer un professeur</CardTitle>
                  <CardDescription>Ajoutez un nouveau professeur</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateTeacher} className="space-y-4">
                    <div>
                      <Label htmlFor="first_name">Prénom</Label>
                      <Input
                        id="first_name"
                        data-testid="admin-teacher-first-name"
                        required
                        value={teacherData.first_name}
                        onChange={(e) => setTeacherData({ ...teacherData, first_name: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="last_name">Nom</Label>
                      <Input
                        id="last_name"
                        data-testid="admin-teacher-last-name"
                        required
                        value={teacherData.last_name}
                        onChange={(e) => setTeacherData({ ...teacherData, last_name: e.target.value })}
                      />
                    </div>
                    <Button type="submit" className="w-full" data-testid="admin-create-teacher-button">
                      <UserPlus className="w-4 h-4 mr-2" />
                      Créer le professeur
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Liste des professeurs</CardTitle>
                  <CardDescription>Tous les professeurs</CardDescription>
                </CardHeader>
                <CardContent>
                  {teachers.length === 0 ? (
                    <p className="text-gray-500">Aucun professeur</p>
                  ) : (
                    <div className="space-y-4">
                      {teachers.map((teacher) => (
                        <div key={teacher.id} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <h3 className="font-semibold">{teacher.first_name} {teacher.last_name}</h3>
                              <p className="text-sm text-gray-600">{teacher.email}</p>
                              {teacher.temporary_password && (
                                <p className="text-xs text-orange-600 font-semibold mt-1">
                                  Mot de passe provisoire: {teacher.temporary_password}
                                </p>
                              )}
                              {teacher.current_password_plain && (
                                <p className="text-xs text-blue-600 font-semibold mt-1">
                                  Mot de passe actuel: {teacher.current_password_plain}
                                </p>
                              )}
                            </div>
                            <div className="flex items-center gap-2">
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={async () => {
                                  try {
                                    await apiClient.post(`/admin/restrict-user/${teacher.id}`);
                                    toast.success(teacher.is_restricted ? 'Accès rétabli' : 'Accès restreint');
                                    fetchData();
                                  } catch (error) {
                                    toast.error('Erreur');
                                  }
                                }}
                                className={teacher.is_restricted ? 'border-green-500 text-green-600' : 'border-orange-500 text-orange-600'}
                              >
                                <Lock className="h-4 w-4" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={async () => {
                                  if (window.confirm(`Supprimer ${teacher.first_name} ${teacher.last_name} ?`)) {
                                    try {
                                      await apiClient.delete(`/admin/delete-user/${teacher.id}`);
                                      toast.success('Utilisateur supprimé');
                                      fetchData();
                                    } catch (error) {
                                      toast.error('Erreur de suppression');
                                    }
                                  }
                                }}
                                className="border-red-500 text-red-600"
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
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <AdminAnalytics />
          </TabsContent>

          <TabsContent value="assign">
            <Card>
              <CardHeader>
                <CardTitle>Assigner un professeur à un étudiant</CardTitle>
                <CardDescription>Gérez les affectations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="student">Sélectionner un étudiant</Label>
                    <Select value={selectedStudent} onValueChange={setSelectedStudent}>
                      <SelectTrigger data-testid="admin-select-student">
                        <SelectValue placeholder="Choisir un étudiant" />
                      </SelectTrigger>
                      <SelectContent>
                        {students.map((student) => (
                          <SelectItem key={student.id} value={student.id}>
                            {student.first_name} {student.last_name} - {student.level}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="teacher">Sélectionner un professeur</Label>
                    <Select value={selectedTeacher} onValueChange={setSelectedTeacher}>
                      <SelectTrigger data-testid="admin-select-teacher">
                        <SelectValue placeholder="Choisir un professeur" />
                      </SelectTrigger>
                      <SelectContent>
                        {teachers.map((teacher) => (
                          <SelectItem key={teacher.id} value={teacher.id}>
                            {teacher.first_name} {teacher.last_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <Button onClick={handleAssignTeacher} className="w-full" data-testid="admin-assign-button">
                    Assigner le professeur
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="results">
            <Card>
              <CardHeader>
                <CardTitle>Résultats des tests</CardTitle>
                <CardDescription>Tous les résultats des tests de niveau</CardDescription>
              </CardHeader>
              <CardContent>
                {testResults.length === 0 ? (
                  <p className="text-gray-500">Aucun résultat de test</p>
                ) : (
                  <div className="space-y-4">
                    {testResults.map((result) => (
                      <div key={result.id} className="p-4 border rounded-lg flex justify-between items-center">
                        <div className="flex-1">
                          <h3 className="font-bold text-lg text-purple-600 mb-1">
                            👤 {result.candidate_name || 'Candidat anonyme'}
                          </h3>
                          {result.candidate_email && (
                            <p className="text-xs text-gray-500 mb-2">
                              📧 {result.candidate_email}
                            </p>
                          )}
                          <p className="text-sm font-semibold text-gray-700">
                            Niveau: {result.level === 'beginner' ? 'Débutant' : result.level === 'intermediate' ? 'Intermédiaire' : 'Pack professionnel'}
                          </p>
                          <p className="text-sm text-gray-600">
                            Score: {result.score} / {result.total_questions}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(result.created_at).toLocaleDateString('fr-FR')} à {new Date(result.created_at).toLocaleTimeString('fr-FR')}
                          </p>
                        </div>
                        <div className="text-3xl font-bold text-blue-600">
                          {Math.round((result.score / result.total_questions) * 100)}%
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>


          {/* Assiduité Tab */}
          <TabsContent value="attendance">
            {/* Tableau récapitulatif mensuel */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>📊 Récapitulatif Mensuel - Total des Heures par Professeur</CardTitle>
                <CardDescription>Total des heures effectuées ce mois-ci par chaque professeur</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr className="bg-teal-50 border-b-2 border-white/30">
                        <th className="text-left p-3 font-semibold text-teal-900">Professeur</th>
                        <th className="text-left p-3 font-semibold text-teal-900">Email</th>
                        <th className="text-center p-3 font-semibold text-teal-900">Nombre de Sessions</th>
                        <th className="text-center p-3 font-semibold text-teal-900">Total Heures</th>
                        <th className="text-center p-3 font-semibold text-teal-900">Temps de Pause</th>
                        <th className="text-center p-3 font-semibold text-teal-900">Heures Effectives</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(() => {
                        const currentMonth = new Date().getMonth();
                        const currentYear = new Date().getFullYear();
                        
                        // Group sessions by teacher for current month
                        const teacherStats = teacherSessions
                          .filter(session => {
                            const sessionDate = new Date(session.created_at);
                            return sessionDate.getMonth() === currentMonth && sessionDate.getFullYear() === currentYear;
                          })
                          .reduce((acc, session) => {
                            const key = session.teacher_id || session.teacher_email;
                            if (!acc[key]) {
                              acc[key] = {
                                name: session.teacher_name || 'Inconnu',
                                email: session.teacher_email || 'N/A',
                                sessions: 0,
                                totalSeconds: 0,
                                pausedSeconds: 0
                              };
                            }
                            acc[key].sessions += 1;
                            acc[key].totalSeconds += session.total_time_seconds || 0;
                            acc[key].pausedSeconds += session.paused_duration_seconds || 0;
                            return acc;
                          }, {});
                        
                        const teachers = Object.values(teacherStats);
                        
                        if (teachers.length === 0) {
                          return (
                            <tr>
                              <td colSpan="6" className="text-center p-6 text-gray-500">
                                Aucune session enregistrée ce mois-ci
                              </td>
                            </tr>
                          );
                        }
                        
                        return teachers.map((teacher, index) => {
                          const effectiveSeconds = teacher.totalSeconds - teacher.pausedSeconds;
                          const totalHours = Math.floor(teacher.totalSeconds / 3600);
                          const totalMinutes = Math.floor((teacher.totalSeconds % 3600) / 60);
                          const pausedHours = Math.floor(teacher.pausedSeconds / 3600);
                          const pausedMinutes = Math.floor((teacher.pausedSeconds % 3600) / 60);
                          const effectiveHours = Math.floor(effectiveSeconds / 3600);
                          const effectiveMinutes = Math.floor((effectiveSeconds % 3600) / 60);
                          
                          return (
                            <tr key={index} className="border-b hover:bg-gray-50">
                              <td className="p-3 font-medium">{teacher.name}</td>
                              <td className="p-3 text-sm text-gray-600">{teacher.email}</td>
                              <td className="p-3 text-center">{teacher.sessions}</td>
                              <td className="p-3 text-center font-semibold text-blue-600">
                                {totalHours}h {totalMinutes}m
                              </td>
                              <td className="p-3 text-center text-orange-600">
                                {pausedHours}h {pausedMinutes}m
                              </td>
                              <td className="p-3 text-center font-bold text-green-600">
                                {effectiveHours}h {effectiveMinutes}m
                              </td>
                            </tr>
                          );
                        });
                      })()}
                    </tbody>
                  </table>
                </div>
                <div className="mt-4 p-3 bg-blue-50 rounded-lg border border-white/30">
                  <p className="text-sm text-blue-800">
                    <strong>💡 Info :</strong> Le tableau affiche les statistiques du mois en cours. 
                    Les "Heures Effectives" correspondent au total des heures moins le temps de pause.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Sessions détaillées */}
            <Card>
              <CardHeader>
                <CardTitle>Assiduité des professeurs</CardTitle>
                <CardDescription>Pointages des cours terminés avec statistiques complètes</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 mb-4">
                  <Button 
                    onClick={async () => {
                      try {
                        const res = await apiClient.get('/admin/teacher-sessions');
                        setTeacherSessions(res.data);
                        toast.success('Statistiques actualisées');
                      } catch (error) {
                        toast.error('Erreur de chargement');
                      }
                    }}
                  >
                    🔄 Actualiser
                  </Button>
                  <Button 
                    variant="destructive"
                    onClick={async () => {
                      if (window.confirm('⚠️ Supprimer TOUTES les assiduités passées ?\n\nCette action est irréversible.')) {
                        try {
                          await apiClient.delete('/admin/teacher-sessions');
                          setTeacherSessions([]);
                          toast.success('✅ Toutes les assiduités ont été supprimées');
                        } catch (error) {
                          toast.error('Erreur lors de la suppression');
                        }
                      }
                    }}
                  >
                    🗑️ Supprimer tout
                  </Button>
                </div>
                {teacherSessions.length === 0 ? (
                  <p className="text-gray-500">Aucune session enregistrée</p>
                ) : (
                  <div className="space-y-4">
                    {teacherSessions.map((session) => (
                      <div key={session.id} className="p-4 border rounded-lg bg-white shadow-sm">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <h3 className="font-semibold text-lg">{session.teacher_name}</h3>
                            <p className="text-sm text-gray-600">{session.teacher_email}</p>
                            <p className="text-xs text-gray-500">Session ID: {session.id}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
                              ✓ Terminé
                            </span>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-500 hover:text-red-700 hover:bg-red-50"
                              onClick={async () => {
                                if (window.confirm('Supprimer cette session ?')) {
                                  try {
                                    await apiClient.delete(`/admin/teacher-sessions/${session.id}`);
                                    setTeacherSessions(teacherSessions.filter(s => s.id !== session.id));
                                    toast.success('Session supprimée');
                                  } catch (error) {
                                    toast.error('Erreur lors de la suppression');
                                  }
                                }
                              }}
                            >
                              🗑️
                            </Button>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3">
                          <div>
                            <p className="text-xs text-gray-500">Début</p>
                            <p className="font-medium">{session.start_time ? new Date(session.start_time).toLocaleString('fr-FR') : 'Non disponible'}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Fin</p>
                            <p className="font-medium">{session.end_time ? new Date(session.end_time).toLocaleString('fr-FR') : 'En cours'}</p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Durée totale</p>
                            <p className="font-medium text-blue-600">
                              {Math.floor(session.total_time_seconds / 3600)}h {Math.floor((session.total_time_seconds % 3600) / 60)}m {session.total_time_seconds % 60}s
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-500">Temps de pause</p>
                            <p className="font-medium text-orange-600">
                              {Math.floor(session.paused_duration_seconds / 3600)}h {Math.floor((session.paused_duration_seconds % 3600) / 60)}m {session.paused_duration_seconds % 60}s
                            </p>
                          </div>
                        </div>
                        
                        <div className="mt-3 pt-3 border-t">
                          <p className="text-xs text-gray-500">
                            Enregistré le {session.created_at ? new Date(session.created_at).toLocaleString('fr-FR') : 'Date non disponible'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Student Availability Tab */}
          <TabsContent value="student-availability">
            <AdminStudentsAvailability />
          </TabsContent>

          {/* Monthly Hours Tab */}
          <TabsContent value="monthly-hours">
            <AdminMonthlyHours />
          </TabsContent>

          {/* Prix Tab */}
          <TabsContent value="pricing">
            <Card>
              <CardHeader>
                <CardTitle>💰 Gestion des prix des packs</CardTitle>
                <CardDescription>Modifier les prix et remises - Changements automatiques sur le site</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleUpdatePrices} className="space-y-6">
                  {/* Pack K-Kid - Enfants */}
                  <div className="mb-6">
                    <h3 className="text-lg font-bold text-pink-600 mb-4 flex items-center gap-2">
                      <span className="text-2xl">👶</span>
                      Pack K-Kid - Spécial Enfants (3-10 ans)
                    </h3>
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="space-y-4 p-6 bg-gradient-to-br from-pink-50 to-pink-100 rounded-xl border-2 border-pink-300 shadow-sm">
                        <div className="flex items-center gap-2 mb-3">
                          <span className="text-2xl">🎨</span>
                          <h4 className="text-md font-bold text-pink-800">Prix K-Kid</h4>
                        </div>
                        
                        {/* EUR */}
                        <div className="space-y-3 pb-3 border-b border-white/30">
                          <p className="text-sm font-semibold text-pink-700">💶 Prix en EURO</p>
                          <div>
                            <Label htmlFor="kkid_eur" className="text-pink-700 text-xs">Prix de base (€)</Label>
                            <Input
                              id="kkid_eur"
                              type="number"
                              value={prices.kkid_eur}
                              onChange={(e) => setPrices({ ...prices, kkid_eur: parseInt(e.target.value) })}
                              className="mt-1 border-pink-300 focus:border-pink-500"
                            />
                          </div>
                          <div>
                            <Label htmlFor="kkid_discount" className="text-pink-700 text-xs">Remise (€)</Label>
                            <Input
                              id="kkid_discount"
                              type="number"
                              value={prices.kkid_discount || 0}
                              onChange={(e) => setPrices({ ...prices, kkid_discount: parseInt(e.target.value) || 0 })}
                              className="mt-1 border-pink-300 focus:border-pink-500"
                              placeholder="0"
                            />
                          </div>
                          <div className="bg-pink-100 p-2 rounded">
                            <p className="text-xs font-semibold text-pink-700">Prix final EUR:</p>
                            <p className="text-2xl font-bold text-pink-800">
                              {(prices.kkid_eur - (prices.kkid_discount || 0))}€
                            </p>
                          </div>
                        </div>

                        {/* FCFA */}
                        <div className="space-y-3">
                          <p className="text-sm font-semibold text-pink-700">🇸🇳 Prix en FCFA</p>
                          <div>
                            <Label htmlFor="kkid_fcfa" className="text-pink-700 text-xs">Prix de base (FCFA)</Label>
                            <Input
                              id="kkid_fcfa"
                              type="number"
                              value={prices.kkid_fcfa || 0}
                              onChange={(e) => setPrices({ ...prices, kkid_fcfa: parseInt(e.target.value) || 0 })}
                              className="mt-1 border-pink-300 focus:border-pink-500"
                            />
                          </div>
                          <div>
                            <Label htmlFor="kkid_discount_fcfa" className="text-pink-700 text-xs">Remise (FCFA)</Label>
                            <Input
                              id="kkid_discount_fcfa"
                              type="number"
                              value={prices.kkid_discount_fcfa || 0}
                              onChange={(e) => setPrices({ ...prices, kkid_discount_fcfa: parseInt(e.target.value) || 0 })}
                              className="mt-1 border-pink-300 focus:border-pink-500"
                              placeholder="0"
                            />
                          </div>
                          <div className="bg-pink-100 p-2 rounded">
                            <p className="text-xs font-semibold text-pink-700">Prix final FCFA:</p>
                            <p className="text-2xl font-bold text-pink-800">
                              {((prices.kkid_fcfa || 0) - (prices.kkid_discount_fcfa || 0)).toLocaleString('fr-FR')} FCFA
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Info sur K-Kid */}
                      <div className="space-y-4 p-6 bg-gradient-to-br from-yellow-50 to-orange-100 rounded-xl border-2 border-yellow-300">
                        <div className="text-center">
                          <span className="text-6xl mb-4 block">🎈</span>
                          <h4 className="text-xl font-bold text-orange-800 mb-2">Pack K-Kid</h4>
                          <p className="text-sm text-orange-700">Pour les enfants de 3 à 9 ans</p>
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center gap-2 text-sm text-orange-800">
                            <span>🎨</span>
                            <span>Cours ludiques et interactifs</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-orange-800">
                            <span>🎵</span>
                            <span>Chansons et jeux éducatifs</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-orange-800">
                            <span>🧸</span>
                            <span>Apprentissage par le jeu</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-orange-800">
                            <span>📚</span>
                            <span>Histoires adaptées aux enfants</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-orange-800">
                            <span>👨‍👩‍👧</span>
                            <span>Suivi parental personnalisé</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-3 gap-6">
                    {/* Pack Débutant */}
                    <div className="space-y-4 p-6 bg-gradient-to-br from-teal-50 to-teal-100 rounded-xl border-2 border-white/30 shadow-sm">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">🌱</span>
                        <h3 className="text-lg font-bold text-teal-800">Pack K-Débutant</h3>
                      </div>
                      
                      {/* EUR */}
                      <div className="space-y-3 pb-3 border-b border-white/30">
                        <p className="text-sm font-semibold text-teal-700">💶 Prix en EURO</p>
                        <div>
                          <Label htmlFor="beginner_eur" className="text-teal-700 text-xs">Prix de base (€)</Label>
                          <Input
                            id="beginner_eur"
                            type="number"
                            value={prices.beginner_eur}
                            onChange={(e) => setPrices({ ...prices, beginner_eur: parseInt(e.target.value) })}
                            className="mt-1 border-teal-300 focus:border-teal-500"
                          />
                        </div>
                        <div>
                          <Label htmlFor="beginner_discount" className="text-teal-700 text-xs">Remise (€)</Label>
                          <Input
                            id="beginner_discount"
                            type="number"
                            value={prices.beginner_discount || 0}
                            onChange={(e) => setPrices({ ...prices, beginner_discount: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-teal-300 focus:border-teal-500"
                            placeholder="0"
                          />
                        </div>
                        <div className="bg-teal-100 p-2 rounded">
                          <p className="text-xs font-semibold text-teal-700">Prix final EUR:</p>
                          <p className="text-2xl font-bold text-teal-800">
                            {(prices.beginner_eur - (prices.beginner_discount || 0))}€
                          </p>
                        </div>
                      </div>

                      {/* FCFA */}
                      <div className="space-y-3">
                        <p className="text-sm font-semibold text-teal-700">🇸🇳 Prix en FCFA</p>
                        <div>
                          <Label htmlFor="beginner_fcfa" className="text-teal-700 text-xs">Prix de base (FCFA)</Label>
                          <Input
                            id="beginner_fcfa"
                            type="number"
                            value={prices.beginner_fcfa || 0}
                            onChange={(e) => setPrices({ ...prices, beginner_fcfa: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-teal-300 focus:border-teal-500"
                          />
                        </div>
                        <div>
                          <Label htmlFor="beginner_discount_fcfa" className="text-teal-700 text-xs">Remise (FCFA)</Label>
                          <Input
                            id="beginner_discount_fcfa"
                            type="number"
                            value={prices.beginner_discount_fcfa || 0}
                            onChange={(e) => setPrices({ ...prices, beginner_discount_fcfa: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-teal-300 focus:border-teal-500"
                            placeholder="0"
                          />
                        </div>
                        <div className="bg-teal-100 p-2 rounded">
                          <p className="text-xs font-semibold text-teal-700">Prix final FCFA:</p>
                          <p className="text-2xl font-bold text-teal-800">
                            {((prices.beginner_fcfa || 0) - (prices.beginner_discount_fcfa || 0)).toLocaleString('fr-FR')} FCFA
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Pack Intermédiaire */}
                    <div className="space-y-4 p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl border-2 border-white/30 shadow-sm">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">🚀</span>
                        <h3 className="text-lg font-bold text-blue-800">Pack K-Intermédiaire</h3>
                      </div>
                      
                      {/* EUR */}
                      <div className="space-y-3 pb-3 border-b border-white/30">
                        <p className="text-sm font-semibold text-blue-700">💶 Prix en EURO</p>
                        <div>
                          <Label htmlFor="intermediate_eur" className="text-blue-700 text-xs">Prix de base (€)</Label>
                          <Input
                            id="intermediate_eur"
                            type="number"
                            value={prices.intermediate_eur}
                            onChange={(e) => setPrices({ ...prices, intermediate_eur: parseInt(e.target.value) })}
                            className="mt-1 border-blue-300 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <Label htmlFor="intermediate_discount" className="text-blue-700 text-xs">Remise (€)</Label>
                          <Input
                            id="intermediate_discount"
                            type="number"
                            value={prices.intermediate_discount || 0}
                            onChange={(e) => setPrices({ ...prices, intermediate_discount: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-blue-300 focus:border-blue-500"
                            placeholder="0"
                          />
                        </div>
                        <div className="bg-blue-100 p-2 rounded">
                          <p className="text-xs font-semibold text-blue-700">Prix final EUR:</p>
                          <p className="text-2xl font-bold text-blue-800">
                            {(prices.intermediate_eur - (prices.intermediate_discount || 0))}€
                          </p>
                        </div>
                      </div>

                      {/* FCFA */}
                      <div className="space-y-3">
                        <p className="text-sm font-semibold text-blue-700">🇸🇳 Prix en FCFA</p>
                        <div>
                          <Label htmlFor="intermediate_fcfa" className="text-blue-700 text-xs">Prix de base (FCFA)</Label>
                          <Input
                            id="intermediate_fcfa"
                            type="number"
                            value={prices.intermediate_fcfa || 0}
                            onChange={(e) => setPrices({ ...prices, intermediate_fcfa: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-blue-300 focus:border-blue-500"
                          />
                        </div>
                        <div>
                          <Label htmlFor="intermediate_discount_fcfa" className="text-blue-700 text-xs">Remise (FCFA)</Label>
                          <Input
                            id="intermediate_discount_fcfa"
                            type="number"
                            value={prices.intermediate_discount_fcfa || 0}
                            onChange={(e) => setPrices({ ...prices, intermediate_discount_fcfa: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-blue-300 focus:border-blue-500"
                            placeholder="0"
                          />
                        </div>
                        <div className="bg-blue-100 p-2 rounded">
                          <p className="text-xs font-semibold text-blue-700">Prix final FCFA:</p>
                          <p className="text-2xl font-bold text-blue-800">
                            {((prices.intermediate_fcfa || 0) - (prices.intermediate_discount_fcfa || 0)).toLocaleString('fr-FR')} FCFA
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Pack Professionnel */}
                    <div className="space-y-4 p-6 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border-2 border-white/30 shadow-sm">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-2xl">👔</span>
                        <h3 className="text-lg font-bold text-purple-800">Pack K-Professionnel</h3>
                      </div>
                      
                      {/* EUR */}
                      <div className="space-y-3 pb-3 border-b border-white/30">
                        <p className="text-sm font-semibold text-purple-700">💶 Prix en EURO</p>
                        <div>
                          <Label htmlFor="advanced_eur" className="text-purple-700 text-xs">Prix de base (€)</Label>
                          <Input
                            id="advanced_eur"
                            type="number"
                            value={prices.advanced_eur}
                            onChange={(e) => setPrices({ ...prices, advanced_eur: parseInt(e.target.value) })}
                            className="mt-1 border-purple-300 focus:border-purple-500"
                          />
                        </div>
                        <div>
                          <Label htmlFor="advanced_discount" className="text-purple-700 text-xs">Remise (€)</Label>
                          <Input
                            id="advanced_discount"
                            type="number"
                            value={prices.advanced_discount || 0}
                            onChange={(e) => setPrices({ ...prices, advanced_discount: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-purple-300 focus:border-purple-500"
                            placeholder="0"
                          />
                        </div>
                        <div className="bg-purple-100 p-2 rounded">
                          <p className="text-xs font-semibold text-purple-700">Prix final EUR:</p>
                          <p className="text-2xl font-bold text-purple-800">
                            {(prices.advanced_eur - (prices.advanced_discount || 0))}€
                          </p>
                        </div>
                      </div>

                      {/* FCFA */}
                      <div className="space-y-3">
                        <p className="text-sm font-semibold text-purple-700">🇸🇳 Prix en FCFA</p>
                        <div>
                          <Label htmlFor="advanced_fcfa" className="text-purple-700 text-xs">Prix de base (FCFA)</Label>
                          <Input
                            id="advanced_fcfa"
                            type="number"
                            value={prices.advanced_fcfa || 0}
                            onChange={(e) => setPrices({ ...prices, advanced_fcfa: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-purple-300 focus:border-purple-500"
                          />
                        </div>
                        <div>
                          <Label htmlFor="advanced_discount_fcfa" className="text-purple-700 text-xs">Remise (FCFA)</Label>
                          <Input
                            id="advanced_discount_fcfa"
                            type="number"
                            value={prices.advanced_discount_fcfa || 0}
                            onChange={(e) => setPrices({ ...prices, advanced_discount_fcfa: parseInt(e.target.value) || 0 })}
                            className="mt-1 border-purple-300 focus:border-purple-500"
                            placeholder="0"
                          />
                        </div>
                        <div className="bg-purple-100 p-2 rounded">
                          <p className="text-xs font-semibold text-purple-700">Prix final FCFA:</p>
                          <p className="text-2xl font-bold text-purple-800">
                            {((prices.advanced_fcfa || 0) - (prices.advanced_discount_fcfa || 0)).toLocaleString('fr-FR')} FCFA
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Button type="submit" className="w-full bg-gradient-to-r from-green-600 to-teal-600 hover:from-green-700 hover:to-teal-700 text-white text-lg py-6 shadow-lg">
                    💾 Enregistrer et mettre à jour le site
                  </Button>
                </form>

                <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-teal-50 border-2 border-white/30 rounded-lg">
                  <p className="text-sm text-green-800 flex items-center gap-2">
                    <span className="text-xl">✨</span>
                    <strong>Mise à jour automatique :</strong> Les prix et remises seront immédiatement visibles sur la page d'accueil après enregistrement.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Teacher Availability Tab */}
          <TabsContent value="availability">
            <Card>
              <CardHeader>
                <CardTitle>📅 Disponibilités des professeurs</CardTitle>
                <CardDescription>Consultez les horaires disponibles de tous les professeurs</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  onClick={async () => {
                    try {
                      const res = await apiClient.get('/admin/all-teacher-availability');
                      setTeacherAvailability(res.data);
                      toast.success('Disponibilités actualisées');
                    } catch (error) {
                      toast.error('Erreur de chargement');
                    }
                  }}
                  className="mb-4"
                >
                  🔄 Actualiser les disponibilités
                </Button>

                {teacherAvailability.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Aucune disponibilité enregistrée</p>
                ) : (
                  <div className="space-y-6">
                    {teacherAvailability.map((item) => (
                      <div key={item.teacher_id} className="border rounded-lg p-4">
                        <div className="mb-4">
                          <h3 className="font-semibold text-lg">
                            {item.teacher_name}
                          </h3>
                          <p className="text-sm text-gray-600">{item.email}</p>
                        </div>

                        {item.availability && Object.keys(item.availability).length > 0 ? (
                          <div className="grid grid-cols-7 gap-2">
                            {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map((day, idx) => {
                              const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
                              const daySlots = item.availability[dayKeys[idx]] || [];
                              
                              return (
                                <div key={idx} className="border rounded p-2">
                                  <p className="font-semibold text-center mb-2 text-sm">{day}</p>
                                  <div className="space-y-1">
                                    {daySlots.length > 0 ? (
                                      daySlots.map((slot, slotIdx) => (
                                        <div key={slotIdx} className="bg-green-100 text-green-800 text-xs px-2 py-1 rounded text-center">
                                          {slot}
                                        </div>
                                      ))
                                    ) : (
                                      <div className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded text-center">
                                        Indispo
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <p className="text-gray-500 italic">Aucune disponibilité définie</p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* News Tab */}
          <TabsContent value="news">
            <NewsManager />
          </TabsContent>

          {/* Kalamathèque Tab */}
          <TabsContent value="kalamatheque">
            <KalamathequeAdmin />
          </TabsContent>

          {/* Discussion Tab */}
          <TabsContent value="conversations">
            <Card className="mb-4">
              <CardContent className="pt-6">
                <div className="flex gap-4 mb-4">
                  <Button
                    variant={conversationMode === 'individual' ? 'default' : 'outline'}
                    onClick={() => {
                      setConversationMode('individual');
                      setSelectedRecipients([]);
                      setActiveConversation(null);
                    }}
                    className={conversationMode === 'individual' ? 'bg-teal-600 hover:bg-teal-700' : ''}
                  >
                    💬 Discussion individuelle
                  </Button>
                  <Button
                    variant={conversationMode === 'group' ? 'default' : 'outline'}
                    onClick={() => {
                      setConversationMode('group');
                      setActiveConversation(null);
                    }}
                    className={conversationMode === 'group' ? 'bg-teal-600 hover:bg-teal-700' : ''}
                  >
                    👥 Message groupé
                  </Button>
                </div>
              </CardContent>
            </Card>

            {conversationMode === 'individual' ? (
              <div className="grid md:grid-cols-3 gap-6">
                {/* Liste des contacts */}
                <Card>
                  <CardHeader>
                    <CardTitle>Tous les contacts</CardTitle>
                    <CardDescription>
                      {allUsers.filter(u => u.role === 'teacher' || u.role === 'student' || u.role === 'secretary').length} contact(s) - Secrétaire, Professeurs & Étudiants
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 max-h-[600px] overflow-y-auto">
                      {allUsers
                        .filter(u => u.role === 'teacher' || u.role === 'student' || u.role === 'secretary')
                        .sort((a, b) => {
                          // Tri par rôle (secrétaire d'abord, puis profs, puis étudiants) puis par nom
                          const roleOrder = { secretary: 0, teacher: 1, student: 2 };
                          if (a.role !== b.role) {
                            return (roleOrder[a.role] || 3) - (roleOrder[b.role] || 3);
                          }
                          return (a.first_name + ' ' + a.last_name).localeCompare(b.first_name + ' ' + b.last_name);
                        })
                        .map((contact) => (
                          <button
                            key={contact.id}
                            onClick={() => setActiveConversation(contact)}
                            className={`w-full p-3 rounded-lg text-left transition ${
                              activeConversation?.id === contact.id
                                ? 'bg-teal-100 border-2 border-teal-600'
                                : 'bg-gray-50 hover:bg-teal-50 border-2 border-transparent'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-full ${contact.role === 'secretary' ? 'bg-purple-600' : contact.role === 'teacher' ? 'bg-blue-600' : 'bg-teal-600'} text-white flex items-center justify-center font-bold`}>
                                {contact.first_name?.charAt(0)}{contact.last_name?.charAt(0)}
                              </div>
                              <div className="flex-1">
                                <p className="font-semibold text-sm">{contact.first_name} {contact.last_name}</p>
                                <p className="text-xs text-gray-500">
                                  {contact.role === 'secretary' ? '📋 Secrétaire' : contact.role === 'teacher' ? '👨‍🏫 Professeur' : '🎓 Étudiant'}
                                </p>
                              </div>
                            </div>
                          </button>
                        ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Zone de conversation */}
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle>
                      {activeConversation 
                        ? `${activeConversation.first_name} ${activeConversation.last_name}` 
                        : 'Discussion'}
                    </CardTitle>
                    <CardDescription>
                      {activeConversation 
                        ? `${activeConversation.role === 'teacher' ? 'Professeur' : 'Étudiant'} - Messages avec pièces jointes`
                        : 'Sélectionnez un contact pour commencer'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {activeConversation ? (
                      <ConversationChat
                        recipientId={activeConversation.id}
                        recipientName={`${activeConversation.first_name} ${activeConversation.last_name}`}
                        currentUserId={user?.id}
                      />
                    ) : (
                      <div className="text-center py-12">
                        <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500">Sélectionnez un contact pour démarrer une conversation</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <div className="grid md:grid-cols-3 gap-6">
                {/* Liste des contacts pour sélection multiple */}
                <Card>
                  <CardHeader>
                    <CardTitle>Tous les contacts</CardTitle>
                    <CardDescription>
                      Sélection multiple - {allUsers.filter(u => u.role === 'teacher' || u.role === 'student' || u.role === 'secretary').length} contact(s)
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedRecipients.length > 0 && (
                      <div className="mb-3 p-2 bg-teal-50 rounded-lg">
                        <p className="text-sm font-semibold text-teal-700">
                          {selectedRecipients.length} personne(s) sélectionnée(s)
                        </p>
                      </div>
                    )}
                    <div className="space-y-2 max-h-[600px] overflow-y-auto">
                      {allUsers
                        .filter(u => u.role === 'teacher' || u.role === 'student' || u.role === 'secretary')
                        .sort((a, b) => {
                          const roleOrder = { secretary: 0, teacher: 1, student: 2 };
                          if (a.role !== b.role) {
                            return (roleOrder[a.role] || 3) - (roleOrder[b.role] || 3);
                          }
                          return (a.first_name + ' ' + a.last_name).localeCompare(b.first_name + ' ' + b.last_name);
                        })
                        .map((contact) => (
                          <button
                            key={contact.id}
                            onClick={() => handleToggleRecipient(contact)}
                            className={`w-full p-3 rounded-lg text-left transition relative ${
                              selectedRecipients.find(r => r.id === contact.id)
                                ? 'bg-teal-100 border-2 border-teal-600'
                                : 'bg-gray-50 hover:bg-teal-50 border-2 border-transparent'
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-full ${contact.role === 'secretary' ? 'bg-purple-600' : contact.role === 'teacher' ? 'bg-blue-600' : 'bg-teal-600'} text-white flex items-center justify-center font-bold`}>
                                {contact.first_name?.charAt(0)}{contact.last_name?.charAt(0)}
                              </div>
                              <div className="flex-1">
                                <p className="font-semibold text-sm">{contact.first_name} {contact.last_name}</p>
                                <p className="text-xs text-gray-500">
                                  {contact.role === 'secretary' ? '📋 Secrétaire' : contact.role === 'teacher' ? '👨‍🏫 Professeur' : '🎓 Étudiant'}
                                </p>
                              </div>
                              {selectedRecipients.find(r => r.id === contact.id) && (
                                <div className="w-6 h-6 bg-teal-600 rounded-full flex items-center justify-center">
                                  <span className="text-white text-sm">✓</span>
                                </div>
                              )}
                            </div>
                          </button>
                        ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Zone d'envoi groupé */}
                <Card className="md:col-span-2">
                  <CardHeader>
                    <CardTitle>
                      {selectedRecipients.length > 0 
                        ? `${selectedRecipients.length} personne(s) sélectionnée(s)` 
                        : 'Envoi de messages groupés'}
                    </CardTitle>
                    <CardDescription>
                      {selectedRecipients.length > 0 
                        ? selectedRecipients.map(r => `${r.first_name} ${r.last_name}`).join(', ')
                        : 'Sélectionnez un ou plusieurs contacts'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedRecipients.length === 0 ? (
                      <div className="text-center py-12">
                        <Users className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-500">Sélectionnez un ou plusieurs contacts pour envoyer un message</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {/* Info sélection */}
                        <div className="border rounded-lg p-4 bg-teal-50">
                          <p className="font-semibold mb-2">Destinataires:</p>
                          <div className="flex flex-wrap gap-2">
                            {selectedRecipients.map(r => (
                              <span key={r.id} className="px-3 py-1 bg-teal-600 text-white rounded-full text-sm">
                                {r.first_name} {r.last_name}
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* Formulaire message */}
                        <form onSubmit={handleSendMessage} className="flex gap-2">
                          <Input
                            value={messageContent}
                            onChange={(e) => setMessageContent(e.target.value)}
                            placeholder="Écrivez votre message..."
                            className="flex-1"
                          />
                          <Button type="submit" className="bg-teal-600 hover:bg-teal-700">
                            Envoyer
                          </Button>
                        </form>

                        {/* Formulaire document/vidéo */}
                        <div className="mt-4 pt-4 border-t">
                          <h4 className="font-semibold mb-3">📤 Envoyer un document ou une vidéo</h4>
                          <form onSubmit={handleSendDocument} className="space-y-3">
                            <div>
                              <Label htmlFor="doc_title">Titre</Label>
                              <Input
                                id="doc_title"
                                value={documentToSend.title}
                                onChange={(e) => setDocumentToSend({ ...documentToSend, title: e.target.value })}
                                required
                                placeholder="Titre du document/vidéo"
                              />
                            </div>
                            <div>
                              <Label htmlFor="doc_description">Description</Label>
                              <Input
                                id="doc_description"
                                value={documentToSend.description}
                                onChange={(e) => setDocumentToSend({ ...documentToSend, description: e.target.value })}
                                placeholder="Description (optionnelle)"
                              />
                            </div>
                            <div>
                              <Label htmlFor="admin_file_upload">📁 Télécharger un fichier</Label>
                              <div className="mt-2">
                                <input
                                  type="file"
                                  id="admin_file_upload"
                                  onChange={async (e) => {
                                    const file = e.target.files[0];
                                    if (file) {
                                      try {
                                        const formData = new FormData();
                                        formData.append('file', file);
                                        const response = await apiClient.post('/upload', formData, {
                                          headers: { 'Content-Type': 'multipart/form-data' }
                                        });
                                        setDocumentToSend({ ...documentToSend, file_url: response.data.file_url });
                                        toast.success('Fichier téléchargé avec succès!');
                                      } catch (error) {
                                        toast.error('Erreur lors du téléchargement du fichier');
                                      }
                                    }
                                  }}
                                  className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                                  accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.jpg,.jpeg,.png,.mp3,.mp4,.mov,.avi,.webm"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                  📄 Documents, 🖼️ Images, 🎵 Audio, 🎥 Vidéo (MP4, MOV, AVI, WebM) - max 10MB
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 h-px bg-gray-300"></div>
                              <span className="text-xs text-gray-500">OU</span>
                              <div className="flex-1 h-px bg-gray-300"></div>
                            </div>
                            <div>
                              <Label htmlFor="doc_url">🔗 Lien du document/vidéo (URL)</Label>
                              <Input
                                id="doc_url"
                                value={documentToSend.file_url}
                                onChange={(e) => setDocumentToSend({ ...documentToSend, file_url: e.target.value })}
                                placeholder="https://... (YouTube, Google Drive, Dropbox, etc.)"
                              />
                              <p className="text-xs text-gray-500 mt-1">YouTube, Vimeo, Google Drive, Dropbox, etc.</p>
                            </div>
                            <div className="bg-blue-50 p-3 rounded-lg border border-white/30">
                              <p className="text-xs text-blue-800">
                                💡 <strong>Destinataires sélectionnés :</strong> {selectedRecipients.length > 0 ? selectedRecipients.map(r => `${r.first_name} ${r.last_name}`).join(', ') : 'Aucun'}
                              </p>
                            </div>
                            <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700" disabled={!documentToSend.file_url || selectedRecipients.length === 0}>
                              📤 Envoyer à {selectedRecipients.length} personne(s)
                            </Button>
                          </form>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>

          {/* KALAMA CLUB Tab */}
          <TabsContent value="club">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <span className="text-2xl">🏆</span>
                  KALAMA CLUB - Espace Communauté
                </CardTitle>
                <CardDescription>
                  Créez des posts, organisez des événements et animez la communauté My KALAMA English
                </CardDescription>
              </CardHeader>
              <CardContent>
                <KalamaClub userRole="admin" />
              </CardContent>
            </Card>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            <DocumentsManager userRole="admin" />
          </TabsContent>

          {/* Test Questions Tab */}
          <TabsContent value="test-questions">
            <TestQuestionsManager />
          </TabsContent>

          {/* Badges Tab */}
          <TabsContent value="badges">
            <BadgesManager />
          </TabsContent>

          {/* Leave Requests Tab */}
          <TabsContent value="leave-requests">
            <Card className="border-blue-200">
              <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                <CardTitle className="flex items-center gap-2 text-blue-800">
                  <Plane className="w-6 h-6" />
                  🏖️ Demandes de Congé
                </CardTitle>
                <CardDescription>
                  Gérez les demandes de congé des professeurs
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {leaveRequests.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Aucune demande de congé</p>
                ) : (
                  <div className="space-y-4">
                    {/* Pending requests first */}
                    {leaveRequests.filter(l => l.status === 'pending').length > 0 && (
                      <div className="mb-6">
                        <h3 className="text-lg font-semibold text-amber-700 mb-3 flex items-center gap-2">
                          <AlertCircle className="w-5 h-5" />
                          En attente de validation ({leaveRequests.filter(l => l.status === 'pending').length})
                        </h3>
                        <div className="space-y-3">
                          {leaveRequests.filter(l => l.status === 'pending').map((leave) => (
                            <div key={leave.id} className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                              <div className="flex items-start justify-between">
                                <div>
                                  <p className="font-semibold text-gray-800">{leave.teacher_name}</p>
                                  <p className="text-sm text-gray-600">{leave.teacher_email}</p>
                                  <p className="text-blue-700 font-medium mt-2">
                                    📅 {new Date(leave.start_date).toLocaleDateString('fr-FR')} → {new Date(leave.end_date).toLocaleDateString('fr-FR')}
                                  </p>
                                  {leave.reason && <p className="text-sm text-gray-500 mt-1">Motif: {leave.reason}</p>}
                                </div>
                                <div className="flex flex-col gap-2">
                                  <Input
                                    placeholder="Commentaire (optionnel)"
                                    className="w-48 text-sm"
                                    value={leaveComment}
                                    onChange={(e) => setLeaveComment(e.target.value)}
                                  />
                                  <div className="flex gap-2">
                                    <Button 
                                      size="sm" 
                                      onClick={() => handleApproveLeave(leave.id)}
                                      className="bg-green-600 hover:bg-green-700"
                                    >
                                      <CheckCircle className="w-4 h-4 mr-1" />
                                      Approuver
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      variant="destructive"
                                      onClick={() => handleRejectLeave(leave.id)}
                                    >
                                      <XCircle className="w-4 h-4 mr-1" />
                                      Refuser
                                    </Button>
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Processed requests */}
                    {leaveRequests.filter(l => l.status !== 'pending').length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold text-gray-700 mb-3">Historique</h3>
                        <div className="space-y-2">
                          {leaveRequests.filter(l => l.status !== 'pending').slice(0, 10).map((leave) => (
                            <div 
                              key={leave.id} 
                              className={`p-3 rounded-lg border flex items-center justify-between ${
                                leave.status === 'approved' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
                              }`}
                            >
                              <div>
                                <p className="font-medium text-gray-800">{leave.teacher_name}</p>
                                <p className="text-sm text-gray-600">
                                  {new Date(leave.start_date).toLocaleDateString('fr-FR')} → {new Date(leave.end_date).toLocaleDateString('fr-FR')}
                                </p>
                                {leave.admin_comment && (
                                  <p className="text-xs text-gray-500 mt-1">💬 {leave.admin_comment}</p>
                                )}
                              </div>
                              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium ${
                                leave.status === 'approved' 
                                  ? 'bg-green-100 text-green-700' 
                                  : 'bg-red-100 text-red-700'
                              }`}>
                                {leave.status === 'approved' ? (
                                  <><CheckCircle className="w-4 h-4" /> Approuvé</>
                                ) : (
                                  <><XCircle className="w-4 h-4" /> Refusé</>
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Trash Tab */}
          <TabsContent value="trash">
            <AdminTrash />
          </TabsContent>

        </Tabs>
      </div>
      
      {/* Document Preview Dialog */}
      
      {/* Change Teacher Dialog */}
      <Dialog open={showChangeTeacherDialog} onOpenChange={setShowChangeTeacherDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>🔄 Changer de Professeur</DialogTitle>
            <DialogDescription>
              Étudiant: {studentToChangeTeacher?.first_name} {studentToChangeTeacher?.last_name}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Sélectionner un professeur</Label>
              <Select 
                value={newTeacherForStudent} 
                onValueChange={setNewTeacherForStudent}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Choisir un professeur..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">❌ Retirer le professeur</SelectItem>
                  {teachers.map(teacher => (
                    <SelectItem key={teacher.id} value={teacher.id}>
                      👨‍🏫 {teacher.first_name} {teacher.last_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button 
                variant="outline" 
                onClick={() => setShowChangeTeacherDialog(false)}
              >
                Annuler
              </Button>
              <Button 
                onClick={async () => {
                  if (studentToChangeTeacher) {
                    const teacherId = newTeacherForStudent === 'none' ? null : newTeacherForStudent;
                    await handleChangeTeacher(studentToChangeTeacher.id, teacherId);
                    setShowChangeTeacherDialog(false);
                    setStudentToChangeTeacher(null);
                  }
                }}
                className="bg-teal-600 hover:bg-teal-700"
              >
                Confirmer
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboard;
