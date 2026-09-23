import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarDays, Users, TrendingUp, Clock, Search, AlertTriangle, History, ChevronDown, ChevronUp, User, Mail, Briefcase, Calendar, Phone, GraduationCap, ChevronLeft, ChevronRight, Edit, Trash2, Save, X } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Label } from './ui/label';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';

const SecretaryHR = () => {
  const [employees, setEmployees] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [calendarData, setCalendarData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedUser, setExpandedUser] = useState(null);
  const [leaveHistory, setLeaveHistory] = useState({});
  const [loadingHistory, setLoadingHistory] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);
  const [activeTab, setActiveTab] = useState('conges');
  const [currentMonth, setCurrentMonth] = useState(new Date());
  
  // Teacher edit/delete state
  const [showEditTeacherModal, setShowEditTeacherModal] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);
  const [teacherForm, setTeacherForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: ''
  });
  const [savingTeacher, setSavingTeacher] = useState(false);

  useEffect(() => {
    fetchLeaveBalances();
    fetchTeachers();
    fetchStudents();
    fetchCalendar();
  }, []);

  const fetchLeaveBalances = async () => {
    try {
      const response = await apiClient.get('/admin/leave-balances');
      setEmployees(response.data);
    } catch (error) {
      console.error('Error fetching leave balances:', error);
      toast.error('Erreur lors du chargement des donnees RH');
    } finally {
      setLoading(false);
    }
  };

  const fetchTeachers = async () => {
    try {
      const response = await apiClient.get('/admin/all-teachers-detailed');
      setTeachers(response.data);
    } catch (error) {
      console.error('Error fetching teachers:', error);
    }
  };

  const fetchStudents = async () => {
    try {
      const response = await apiClient.get('/admin/all-students');
      setStudents(response.data);
    } catch (error) {
      console.error('Error fetching students:', error);
    }
  };

  const fetchCalendar = async () => {
    try {
      const response = await apiClient.get('/admin/availability-calendar');
      setCalendarData(response.data);
    } catch (error) {
      console.error('Error fetching calendar:', error);
    }
  };

  // Teacher edit handlers
  const openEditTeacher = (teacher) => {
    setEditingTeacher(teacher);
    setTeacherForm({
      first_name: teacher.first_name || '',
      last_name: teacher.last_name || '',
      email: teacher.email || '',
      phone: teacher.phone || ''
    });
    setShowEditTeacherModal(true);
  };

  const handleSaveTeacher = async () => {
    if (!editingTeacher) return;
    setSavingTeacher(true);
    try {
      await apiClient.put(`/admin/update-user/${editingTeacher.user_id}`, teacherForm);
      toast.success('Professeur modifié avec succès');
      setShowEditTeacherModal(false);
      setEditingTeacher(null);
      fetchTeachers();
    } catch (error) {
      console.error('Error updating teacher:', error);
      toast.error('Erreur lors de la modification');
    } finally {
      setSavingTeacher(false);
    }
  };

  const handleDeleteTeacher = async (teacher) => {
    if (!window.confirm(`Supprimer ${teacher.first_name} ${teacher.last_name} ?\nCette action déplacera le professeur vers la corbeille.`)) {
      return;
    }
    try {
      await apiClient.delete(`/admin/delete-user/${teacher.user_id}`);
      toast.success('Professeur supprimé (déplacé vers la corbeille)');
      fetchTeachers();
    } catch (error) {
      console.error('Error deleting teacher:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  const fetchLeaveHistory = async (userId) => {
    if (leaveHistory[userId]) {
      setExpandedUser(expandedUser === userId ? null : userId);
      return;
    }
    setLoadingHistory(userId);
    try {
      const response = await apiClient.get(`/admin/leave-balance/${userId}`);
      setLeaveHistory(prev => ({ ...prev, [userId]: response.data }));
      setExpandedUser(userId);
    } catch (error) {
      console.error('Error fetching leave history:', error);
      toast.error('Erreur lors du chargement de l\'historique');
    } finally {
      setLoadingHistory(null);
    }
  };

  const openEmployeeProfile = async (emp) => {
    setSelectedEmployee(emp);
    setShowEmployeeModal(true);
    if (!leaveHistory[emp.user_id]) {
      setLoadingHistory(emp.user_id);
      try {
        const response = await apiClient.get(`/admin/leave-balance/${emp.user_id}`);
        setLeaveHistory(prev => ({ ...prev, [emp.user_id]: response.data }));
      } catch (error) {
        console.error('Error fetching leave history:', error);
      } finally {
        setLoadingHistory(null);
      }
    }
  };

  const roleLabel = (role) => {
    switch (role) {
      case 'teacher': return 'Professeur';
      case 'admin': return 'Admin';
      case 'secretary': return 'Secretaire';
      case 'student': return 'Etudiant';
      default: return role;
    }
  };

  const roleColor = (role) => {
    switch (role) {
      case 'teacher': return 'bg-blue-100 text-blue-800';
      case 'admin': return 'bg-purple-100 text-purple-800';
      case 'secretary': return 'bg-teal-100 text-teal-800';
      case 'student': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const levelLabel = (level) => {
    switch (level) {
      case 'kkid': return 'K-Kid';
      case 'beginner': return 'Debutant';
      case 'intermediate': return 'Intermediaire';
      case 'advanced': return 'Avance';
      default: return level || 'Non defini';
    }
  };

  const levelColor = (level) => {
    switch (level) {
      case 'kkid': return 'bg-pink-100 text-pink-800';
      case 'beginner': return 'bg-teal-100 text-teal-800';
      case 'intermediate': return 'bg-blue-100 text-blue-800';
      case 'advanced': return 'bg-emerald-100 text-emerald-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const leaveStatusLabel = (status) => {
    switch (status) {
      case 'approved': return { text: 'Approuve', cls: 'bg-green-100 text-green-800' };
      case 'rejected': return { text: 'Refuse', cls: 'bg-red-100 text-red-800' };
      case 'cancelled': return { text: 'Annule', cls: 'bg-gray-100 text-gray-800' };
      case 'pending': return { text: 'En attente', cls: 'bg-yellow-100 text-yellow-800' };
      default: return { text: status, cls: 'bg-gray-100 text-gray-800' };
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR');
    } catch { return dateStr; }
  };

  // Filter employees based on search
  const filteredEmployees = employees.filter(e =>
    `${e.first_name} ${e.last_name} ${e.email}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredTeachers = teachers.filter(t =>
    `${t.first_name} ${t.last_name} ${t.email}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredStudents = students.filter(s =>
    `${s.first_name} ${s.last_name} ${s.email}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate stats
  const totalEmployees = employees.length;
  const totalRemaining = employees.reduce((sum, e) => sum + (e.remaining || 0), 0);
  const lowBalanceCount = employees.filter(e => e.remaining <= 5 && e.total_earned > 0).length;

  // Calendar helpers
  const getDaysInMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  const isOnLeave = (empId, day) => {
    const emp = calendarData.find(e => e.user_id === empId);
    if (!emp || !emp.leave_periods) return false;
    
    const checkDate = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    
    return emp.leave_periods.some(period => {
      const start = new Date(period.start);
      const end = new Date(period.end);
      return checkDate >= start && checkDate <= end;
    });
  };

  const prevMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 1));
  };

  const monthNames = ['Janvier', 'Fevrier', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Aout', 'Septembre', 'Octobre', 'Novembre', 'Decembre'];

  // Employee Row Component for Congés Tab
  const EmployeeRow = ({ emp }) => {
    const MAX_LEAVE = 30;
    const pct = MAX_LEAVE > 0 ? (emp.remaining / MAX_LEAVE) * 100 : 0;
    const barColor = pct > 50 ? 'bg-emerald-500' : pct > 25 ? 'bg-amber-500' : 'bg-red-500';
    const isExpanded = expandedUser === emp.user_id;
    const history = leaveHistory[emp.user_id];
    const isAlert = emp.remaining <= 5 && emp.total_earned > 0;

    return (
      <>
        <tr
          className={`border-b last:border-0 hover:bg-gray-50 cursor-pointer transition-colors ${isAlert ? 'bg-red-50/50' : ''}`}
          onClick={() => fetchLeaveHistory(emp.user_id)}
          data-testid={`hr-row-${emp.user_id}`}
        >
          <td className="py-3 pr-4">
            <div className="flex items-center gap-2">
              <span className="font-medium">{emp.first_name} {emp.last_name}</span>
              {isAlert && <AlertTriangle className="w-4 h-4 text-red-500" />}
            </div>
          </td>
          <td className="py-3 pr-4 text-sm text-gray-500">{emp.email}</td>
          <td className="py-3 pr-4 text-center">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${roleColor(emp.role)}`}>
              {roleLabel(emp.role)}
            </span>
          </td>
          <td className="py-3 pr-4 text-center font-medium text-gray-600">{MAX_LEAVE}j</td>
          <td className="py-3 pr-4 text-center font-medium text-amber-600">{emp.total_taken}j</td>
          <td className="py-3 pr-4 text-center font-bold text-blue-600">{emp.remaining}j</td>
          <td className="py-3 w-32">
            <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
              <div className={`h-full rounded-full ${barColor}`} style={{ width: `${Math.min(100, pct)}%` }} />
            </div>
          </td>
          <td className="py-3 pl-2 text-center">
            <Button
              size="sm"
              variant="ghost"
              className="text-teal-600 hover:bg-teal-50 hover:text-teal-700"
              onClick={(e) => { e.stopPropagation(); openEmployeeProfile(emp); }}
              data-testid={`view-profile-${emp.user_id}`}
              aria-label={`Voir le profil de ${emp.first_name} ${emp.last_name}`}
            >
              <User className="w-4 h-4" />
            </Button>
            {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400 inline" /> : <ChevronDown className="w-4 h-4 text-gray-400 inline" />}
          </td>
        </tr>
        {isExpanded && (
          <tr>
            <td colSpan="8" className="bg-gray-50 px-6 py-4">
              {loadingHistory === emp.user_id ? (
                <div className="flex justify-center py-4">
                  <div className="w-5 h-5 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : history ? (
                <div data-testid={`leave-history-${emp.user_id}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <History className="w-4 h-4 text-teal-600" />
                    <h4 className="font-semibold text-sm text-gray-700">Historique des conges</h4>
                    <span className="text-xs text-gray-400">({history.months_worked} mois travailles)</span>
                  </div>
                  {history.approved_leaves && history.approved_leaves.length > 0 ? (
                    <div className="space-y-2">
                      {history.approved_leaves.map((leave, idx) => {
                        const s = leaveStatusLabel(leave.status);
                        return (
                          <div key={leave.id || idx} className="flex items-center gap-4 bg-white p-3 rounded-lg border text-sm">
                            <div className="flex-1">
                              <p className="font-medium">{leave.reason || 'Conge'}</p>
                              <p className="text-xs text-gray-400">
                                Du {formatDate(leave.start_date)} au {formatDate(leave.end_date)}
                              </p>
                            </div>
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>{s.text}</span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-400 italic">Aucun conge pris pour le moment</p>
                  )}
                </div>
              ) : null}
            </td>
          </tr>
        )}
      </>
    );
  };

  // Employee Profile Modal
  const EmployeeProfileModal = () => {
    if (!selectedEmployee) return null;
    
    const emp = selectedEmployee;
    const history = leaveHistory[emp.user_id];
    const MAX_LEAVE = 30;
    const pct = MAX_LEAVE > 0 ? (emp.remaining / MAX_LEAVE) * 100 : 0;
    const usagePct = Math.max(0, Math.min(100, 100 - pct));
    const barColor = pct > 50 ? 'bg-emerald-500' : pct > 25 ? 'bg-amber-500' : 'bg-red-500';
    const isAlert = emp.remaining <= 5;

    return (
      <Dialog open={showEmployeeModal} onOpenChange={setShowEmployeeModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="employee-profile-modal">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center ${roleColor(emp.role)}`}>
                <User className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-xl font-bold">{emp.first_name} {emp.last_name}</h2>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${roleColor(emp.role)}`}>
                  {roleLabel(emp.role)}
                </span>
              </div>
            </DialogTitle>
            <DialogDescription className="sr-only">
              Fiche detaillee de {emp.first_name} {emp.last_name}, {roleLabel(emp.role)}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-6 mt-4">
            {/* Info Section */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Mail className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-xs text-gray-500">Email</p>
                  <p className="font-medium text-sm">{emp.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Phone className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-xs text-gray-500">Telephone</p>
                  <p className="font-medium text-sm">{emp.phone || 'Non renseigné'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                <Briefcase className="w-5 h-5 text-gray-500" />
                <div>
                  <p className="text-xs text-gray-500">Poste</p>
                  <p className="font-medium text-sm">{roleLabel(emp.role)}</p>
                </div>
              </div>
              {history && (
                <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                  <Calendar className="w-5 h-5 text-gray-500" />
                  <div>
                    <p className="text-xs text-gray-500">Ancienneté</p>
                    <p className="font-medium text-sm">{history.months_worked} mois</p>
                  </div>
                </div>
              )}
            </div>

            {/* Leave Balance Section */}
            <Card className={isAlert ? 'border-red-200 bg-red-50/50' : ''}>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <CalendarDays className="w-5 h-5 text-teal-600" />
                  Solde de Congés (30 jours/an)
                  {isAlert && <AlertTriangle className="w-4 h-4 text-red-500" />}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <p className="text-2xl font-bold text-gray-600">{MAX_LEAVE}j</p>
                    <p className="text-xs text-gray-500">Droit annuel</p>
                  </div>
                  <div className="text-center p-3 bg-amber-50 rounded-lg">
                    <p className="text-2xl font-bold text-amber-600">{emp.total_taken}j</p>
                    <p className="text-xs text-amber-700">Pris</p>
                  </div>
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600">{emp.remaining}j</p>
                    <p className="text-xs text-blue-700">Restants</p>
                  </div>
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Utilisation</span>
                    <span>{Math.round(usagePct)}%</span>
                  </div>
                  <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${barColor}`} style={{ width: `${usagePct}%` }} />
                  </div>
                </div>
                {isAlert && (
                  <div className="mt-3 p-2 bg-red-100 border border-red-200 rounded-lg text-center">
                    <p className="text-sm text-red-700 font-medium flex items-center justify-center gap-1">
                      <AlertTriangle className="w-4 h-4" />
                      Solde de conges bas !
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Leave History Section */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <History className="w-5 h-5 text-teal-600" />
                  Historique des Congés
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingHistory === emp.user_id ? (
                  <div className="flex justify-center py-8">
                    <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
                  </div>
                ) : history?.approved_leaves && history.approved_leaves.length > 0 ? (
                  <div className="space-y-3 max-h-60 overflow-y-auto">
                    {history.approved_leaves.map((leave, idx) => {
                      const s = leaveStatusLabel(leave.status);
                      const startDate = new Date(leave.start_date);
                      const endDate = new Date(leave.end_date);
                      const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
                      return (
                        <div key={leave.id || idx} className="p-4 bg-gray-50 rounded-lg border">
                          <div className="flex items-center justify-between mb-2">
                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>{s.text}</span>
                            <span className="text-sm font-semibold text-gray-700">{days} jour{days > 1 ? 's' : ''}</span>
                          </div>
                          <p className="font-medium text-gray-800">{leave.reason || 'Conge'}</p>
                          <p className="text-sm text-gray-500 mt-1">
                            Du {formatDate(leave.start_date)} au {formatDate(leave.end_date)}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    <CalendarDays className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>Aucun conge pris pour le moment</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Legal Info */}
            <div className="text-xs text-gray-400 text-center p-3 bg-gray-50 rounded-lg">
              Droit annuel: <strong>30 jours</strong> | Acquisition: <strong>2,5 jours/mois</strong>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="secretary-hr">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-teal-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Employes</p>
              <p className="text-2xl font-bold text-teal-700">{totalEmployees}</p>
            </div>
            <Users className="w-8 h-8 text-teal-500 opacity-50" />
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Jours restants (total)</p>
              <p className="text-2xl font-bold text-blue-700">{totalRemaining}j</p>
            </div>
            <CalendarDays className="w-8 h-8 text-blue-500 opacity-50" />
          </CardContent>
        </Card>
        <Card className={`border-l-4 ${lowBalanceCount > 0 ? 'border-l-red-500' : 'border-l-emerald-500'}`}>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Alertes Solde Bas</p>
              <p className={`text-2xl font-bold ${lowBalanceCount > 0 ? 'text-red-700' : 'text-emerald-700'}`}>{lowBalanceCount}</p>
            </div>
            <AlertTriangle className={`w-8 h-8 opacity-50 ${lowBalanceCount > 0 ? 'text-red-500' : 'text-emerald-500'}`} />
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Droit annuel</p>
              <p className="text-2xl font-bold text-purple-700">30j</p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-500 opacity-50" />
          </CardContent>
        </Card>
      </div>

      {/* Tabs for different sections */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-white border p-1 rounded-lg overflow-x-auto flex-nowrap">
          <TabsTrigger value="conges" className="data-[state=active]:bg-teal-600 data-[state=active]:text-white whitespace-nowrap">
            <CalendarDays className="w-4 h-4 mr-2" />
            Congés
          </TabsTrigger>
          <TabsTrigger value="calendrier" className="data-[state=active]:bg-teal-600 data-[state=active]:text-white whitespace-nowrap">
            <Calendar className="w-4 h-4 mr-2" />
            Calendrier
          </TabsTrigger>
          <TabsTrigger value="professeurs" className="data-[state=active]:bg-teal-600 data-[state=active]:text-white whitespace-nowrap">
            <Briefcase className="w-4 h-4 mr-2" />
            Professeurs
          </TabsTrigger>
          <TabsTrigger value="etudiants" className="data-[state=active]:bg-teal-600 data-[state=active]:text-white whitespace-nowrap">
            <GraduationCap className="w-4 h-4 mr-2" />
            Étudiants
          </TabsTrigger>
        </TabsList>

        {/* Congés Tab */}
        <TabsContent value="conges" className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Rechercher un employe..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              data-testid="hr-search"
            />
          </div>

          {/* Employees Table */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="w-5 h-5 text-teal-600" />
                Gestion des Congés (30j/an)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-gray-500">
                      <th className="pb-3 pr-4 font-medium">Nom</th>
                      <th className="pb-3 pr-4 font-medium">Email</th>
                      <th className="pb-3 pr-4 font-medium text-center">Role</th>
                      <th className="pb-3 pr-4 font-medium text-center">Droit</th>
                      <th className="pb-3 pr-4 font-medium text-center">Pris</th>
                      <th className="pb-3 pr-4 font-medium text-center">Restant</th>
                      <th className="pb-3 font-medium w-32">Solde</th>
                      <th className="pb-3 pl-2 font-medium text-center">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEmployees.map((emp) => (
                      <EmployeeRow key={emp.user_id} emp={emp} />
                    ))}
                  </tbody>
                </table>
                {filteredEmployees.length === 0 && (
                  <p className="text-center text-gray-400 py-8">Aucun employé trouvé</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Calendar Tab */}
        <TabsContent value="calendrier" className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-teal-600" />
                  Calendrier des Disponibilites
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={prevMonth}>
                    <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="font-semibold min-w-[150px] text-center">
                    {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
                  </span>
                  <Button variant="outline" size="sm" onClick={nextMonth}>
                    <ChevronRight className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-4 text-sm">
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-emerald-100 rounded"></div>
                    Disponible
                  </span>
                  <span className="flex items-center gap-2">
                    <div className="w-4 h-4 bg-red-100 rounded"></div>
                    En conge
                  </span>
                </div>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr>
                      <th className="p-2 text-left border bg-gray-50 sticky left-0 min-w-[150px]">Employe</th>
                      {Array.from({ length: getDaysInMonth(currentMonth) }, (_, i) => {
                        const day = i + 1;
                        const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
                        const isWeekend = date.getDay() === 0 || date.getDay() === 6;
                        return (
                          <th key={day} className={`p-1 border text-center min-w-[30px] ${isWeekend ? 'bg-gray-100' : 'bg-gray-50'}`}>
                            {day}
                          </th>
                        );
                      })}
                    </tr>
                  </thead>
                  <tbody>
                    {calendarData.filter(e => e.role !== 'student').map((emp) => (
                      <tr key={emp.user_id}>
                        <td className="p-2 border bg-white sticky left-0">
                          <div className="flex items-center gap-2">
                            <span className={`px-1.5 py-0.5 rounded text-xs ${roleColor(emp.role)}`}>
                              {emp.role === 'teacher' ? 'P' : emp.role === 'admin' ? 'A' : 'S'}
                            </span>
                            <span className="truncate">{emp.first_name} {emp.last_name}</span>
                          </div>
                        </td>
                        {Array.from({ length: getDaysInMonth(currentMonth) }, (_, i) => {
                          const day = i + 1;
                          const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
                          const isWeekend = date.getDay() === 0 || date.getDay() === 6;
                          const onLeave = isOnLeave(emp.user_id, day);
                          return (
                            <td 
                              key={day} 
                              className={`p-1 border text-center ${
                                isWeekend ? 'bg-gray-50' : onLeave ? 'bg-red-100' : 'bg-emerald-50'
                              }`}
                              title={onLeave ? 'En congé' : 'Disponible'}
                            >
                              {onLeave ? '🏖️' : ''}
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

        {/* Teachers Tab */}
        <TabsContent value="professeurs" className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Rechercher un professeur..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-teal-600" />
                Fiches Professeurs ({filteredTeachers.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredTeachers.map((teacher) => (
                  <Card key={teacher.user_id} className="hover:shadow-md transition-shadow" data-testid={`teacher-card-${teacher.user_id}`}>
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <User className="w-5 h-5 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate">
                            {teacher.first_name} {teacher.last_name}
                          </h3>
                          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium mt-1 ${roleColor('teacher')}`}>
                            Professeur
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                          <Mail className="w-4 h-4" />
                          <span className="truncate">{teacher.email}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Phone className="w-4 h-4" />
                          <span>{teacher.phone || 'Non renseigné'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Clock className="w-4 h-4" />
                          <span>Ancienneté: <strong>{teacher.months_worked} mois</strong></span>
                        </div>
                      </div>
                      {/* Edit/Delete buttons */}
                      <div className="flex gap-2 mt-4 pt-3 border-t">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="flex-1 text-blue-600 hover:bg-blue-50"
                          onClick={() => openEditTeacher(teacher)}
                          data-testid={`edit-teacher-${teacher.user_id}`}
                        >
                          <Edit className="w-4 h-4 mr-1" />
                          Modifier
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="flex-1 text-red-600 hover:bg-red-50"
                          onClick={() => handleDeleteTeacher(teacher)}
                          data-testid={`delete-teacher-${teacher.user_id}`}
                        >
                          <Trash2 className="w-4 h-4 mr-1" />
                          Supprimer
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {filteredTeachers.length === 0 && (
                  <p className="text-center text-gray-400 py-8 col-span-3">Aucun professeur trouvé</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Students Tab */}
        <TabsContent value="etudiants" className="space-y-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Rechercher un etudiant..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-teal-600" />
                Fiches Étudiants ({filteredStudents.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredStudents.map((student) => (
                  <Card key={student.user_id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                          <GraduationCap className="w-5 h-5 text-green-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate">
                            {student.first_name} {student.last_name}
                          </h3>
                          <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium mt-1 ${levelColor(student.level)}`}>
                            {levelLabel(student.level)}
                          </span>
                        </div>
                      </div>
                      <div className="mt-4 space-y-2 text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                          <Mail className="w-4 h-4" />
                          <span className="truncate">{student.email}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Phone className="w-4 h-4" />
                          <span>{student.phone || 'Non renseigné'}</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                {filteredStudents.length === 0 && (
                  <p className="text-center text-gray-400 py-8 col-span-3">Aucun étudiant trouvé</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Employee Profile Modal */}
      <EmployeeProfileModal />

      {/* Edit Teacher Modal */}
      <Dialog open={showEditTeacherModal} onOpenChange={setShowEditTeacherModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-teal-700 flex items-center gap-2">
              <Edit className="w-5 h-5" />
              Modifier le Professeur
            </DialogTitle>
            <DialogDescription>
              Modifiez les informations du professeur
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <Label>Prénom</Label>
              <Input 
                value={teacherForm.first_name} 
                onChange={(e) => setTeacherForm({...teacherForm, first_name: e.target.value})}
                placeholder="Prénom"
              />
            </div>
            <div>
              <Label>Nom</Label>
              <Input 
                value={teacherForm.last_name} 
                onChange={(e) => setTeacherForm({...teacherForm, last_name: e.target.value})}
                placeholder="Nom"
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input 
                type="email"
                value={teacherForm.email} 
                onChange={(e) => setTeacherForm({...teacherForm, email: e.target.value})}
                placeholder="email@example.com"
              />
            </div>
            <div>
              <Label>Téléphone</Label>
              <Input 
                value={teacherForm.phone} 
                onChange={(e) => setTeacherForm({...teacherForm, phone: e.target.value})}
                placeholder="+33 6 00 00 00 00"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 mt-6">
            <Button 
              variant="outline" 
              onClick={() => setShowEditTeacherModal(false)}
            >
              <X className="w-4 h-4 mr-1" />
              Annuler
            </Button>
            <Button 
              onClick={handleSaveTeacher}
              className="bg-teal-600 hover:bg-teal-700"
              disabled={savingTeacher || !teacherForm.first_name || !teacherForm.last_name}
            >
              <Save className="w-4 h-4 mr-1" />
              {savingTeacher ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SecretaryHR;
