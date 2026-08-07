import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarDays, Users, TrendingUp, TrendingDown, Clock, Search, AlertTriangle, History, ChevronDown, ChevronUp, X, User, Mail, Briefcase, Calendar } from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
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
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedUser, setExpandedUser] = useState(null);
  const [leaveHistory, setLeaveHistory] = useState({});
  const [loadingHistory, setLoadingHistory] = useState(null);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showEmployeeModal, setShowEmployeeModal] = useState(false);

  useEffect(() => {
    fetchLeaveBalances();
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
    // Fetch leave history if not already loaded
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

  const filtered = employees.filter(emp =>
    `${emp.first_name} ${emp.last_name} ${emp.email}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const teachers = filtered.filter(e => e.role === 'teacher');
  const staff = filtered.filter(e => e.role !== 'teacher');
  const alerts = employees.filter(e => e.remaining <= 5 && e.total_earned > 0);

  const totalRemaining = employees.reduce((sum, e) => sum + (e.remaining || 0), 0);
  const totalTaken = employees.reduce((sum, e) => sum + (e.total_taken || 0), 0);

  const roleLabel = (role) => {
    switch(role) {
      case 'teacher': return 'Professeur';
      case 'secretary': return 'Secretaire';
      case 'admin': return 'Admin';
      default: return role;
    }
  };

  const roleColor = (role) => {
    switch(role) {
      case 'teacher': return 'bg-blue-100 text-blue-800';
      case 'secretary': return 'bg-purple-100 text-purple-800';
      case 'admin': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch { return dateStr; }
  };

  const leaveStatusLabel = (status) => {
    switch(status) {
      case 'approved': return { text: 'Approuve', cls: 'bg-green-100 text-green-700' };
      case 'pending': return { text: 'En attente', cls: 'bg-amber-100 text-amber-700' };
      case 'rejected': return { text: 'Refuse', cls: 'bg-red-100 text-red-700' };
      default: return { text: status, cls: 'bg-gray-100 text-gray-700' };
    }
  };

  const EmployeeRow = ({ emp }) => {
    const pct = emp.total_earned > 0 ? (emp.remaining / emp.total_earned) * 100 : 0;
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
          <td className="py-3 pr-4 text-center font-medium text-emerald-600">{emp.total_earned}j</td>
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

  // Employee Profile Modal Component
  const EmployeeProfileModal = () => {
    if (!selectedEmployee) return null;
    
    const emp = selectedEmployee;
    const history = leaveHistory[emp.user_id];
    const pct = emp.total_earned > 0 ? (emp.remaining / emp.total_earned) * 100 : 0;
    const barColor = pct > 50 ? 'bg-emerald-500' : pct > 25 ? 'bg-amber-500' : 'bg-red-500';
    const isAlert = emp.remaining <= 5 && emp.total_earned > 0;

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
                    <p className="text-xs text-gray-500">Anciennete</p>
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
                  Solde de Conges
                  {isAlert && <AlertTriangle className="w-4 h-4 text-red-500" />}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-3 bg-emerald-50 rounded-lg">
                    <p className="text-2xl font-bold text-emerald-600">{emp.total_earned}j</p>
                    <p className="text-xs text-emerald-700">Acquis</p>
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
                    <span>{Math.round(100 - pct)}%</span>
                  </div>
                  <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full ${barColor}`} style={{ width: `${Math.min(100, 100 - pct)}%` }} />
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
                  Historique des Conges
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
              Acquisition legale: <strong>2,5 jours/mois</strong> | Maximum annuel: <strong>30 jours</strong>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="hr-loading">
        <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="secretary-hr-container">
      {/* Alerts */}
      {alerts.length > 0 && (
        <Card className="border-red-200 bg-red-50" data-testid="leave-alerts">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              <h3 className="font-semibold text-red-700">Alertes Solde Conges</h3>
            </div>
            <div className="space-y-2">
              {alerts.map(emp => (
                <div key={emp.user_id} className="flex items-center justify-between bg-white p-3 rounded-lg border border-red-200">
                  <div className="flex items-center gap-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${roleColor(emp.role)}`}>{roleLabel(emp.role)}</span>
                    <span className="font-medium">{emp.first_name} {emp.last_name}</span>
                  </div>
                  <span className="text-red-600 font-bold">{emp.remaining}j restants</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500 rounded-lg">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-blue-600">Employes</p>
                <p className="text-2xl font-bold text-blue-800" data-testid="hr-total-employees">{employees.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-500 rounded-lg">
                <TrendingUp className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-emerald-600">Jours Restants (total)</p>
                <p className="text-2xl font-bold text-emerald-800">{totalRemaining}j</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-500 rounded-lg">
                <TrendingDown className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-amber-600">Jours Pris (total)</p>
                <p className="text-2xl font-bold text-amber-800">{totalTaken}j</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500 rounded-lg">
                <CalendarDays className="w-5 h-5 text-white" />
              </div>
              <div>
                <p className="text-xs text-purple-600">Taux acquisition</p>
                <p className="text-2xl font-bold text-purple-800">2.5j/mois</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
        <Input
          placeholder="Rechercher un employe..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
          data-testid="hr-search"
        />
      </div>

      {/* Professors Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Users className="w-5 h-5 text-blue-600" />
            Professeurs ({teachers.length})
          </CardTitle>
          <p className="text-xs text-gray-400">Cliquez sur un employe pour voir son historique de conges</p>
        </CardHeader>
        <CardContent>
          {teachers.length === 0 ? (
            <p className="text-center text-gray-400 py-4">Aucun professeur trouve</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 pr-4">Nom</th>
                    <th className="pb-3 pr-4">Email</th>
                    <th className="pb-3 pr-4 text-center">Role</th>
                    <th className="pb-3 pr-4 text-center">Acquis</th>
                    <th className="pb-3 pr-4 text-center">Pris</th>
                    <th className="pb-3 pr-4 text-center">Restants</th>
                    <th className="pb-3 text-center">Jauge</th>
                    <th className="pb-3 w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {teachers.map(emp => <EmployeeRow key={emp.user_id} emp={emp} />)}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Staff Section */}
      {staff.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="w-5 h-5 text-purple-600" />
              Administration ({staff.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b text-left text-sm text-gray-500">
                    <th className="pb-3 pr-4">Nom</th>
                    <th className="pb-3 pr-4">Email</th>
                    <th className="pb-3 pr-4 text-center">Role</th>
                    <th className="pb-3 pr-4 text-center">Acquis</th>
                    <th className="pb-3 pr-4 text-center">Pris</th>
                    <th className="pb-3 pr-4 text-center">Restants</th>
                    <th className="pb-3 text-center">Jauge</th>
                    <th className="pb-3 w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {staff.map(emp => <EmployeeRow key={emp.user_id} emp={emp} />)}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Legal Info */}
      <Card className="bg-gray-50 border-dashed">
        <CardContent className="p-4">
          <p className="text-xs text-gray-500 text-center">
            Chaque employe acquiert legalement <strong>2,5 jours ouvrables</strong> de conges payes par mois de travail effectif.
            Sur une annee complete, cela represente <strong>30 jours ouvrables</strong> (5 semaines), soit 25 jours ouvres.
          </p>
        </CardContent>
      </Card>

      {/* Employee Profile Modal */}
      <EmployeeProfileModal />
    </div>
  );
};

export default SecretaryHR;
