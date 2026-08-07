import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { CalendarDays, Users, TrendingUp, TrendingDown, Clock, Search } from 'lucide-react';
import { Input } from './ui/input';
import { toast } from 'sonner';
import apiClient from '../utils/api';

const SecretaryHR = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

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

  const filtered = employees.filter(emp =>
    `${emp.first_name} ${emp.last_name} ${emp.email}`.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const teachers = filtered.filter(e => e.role === 'teacher');
  const staff = filtered.filter(e => e.role !== 'teacher');

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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="hr-loading">
        <div className="w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="secretary-hr-container">
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
                  </tr>
                </thead>
                <tbody>
                  {teachers.map((emp) => {
                    const pct = emp.total_earned > 0 ? (emp.remaining / emp.total_earned) * 100 : 0;
                    const barColor = pct > 50 ? 'bg-emerald-500' : pct > 25 ? 'bg-amber-500' : 'bg-red-500';
                    return (
                      <tr key={emp.user_id} className="border-b last:border-0 hover:bg-gray-50" data-testid={`hr-row-${emp.user_id}`}>
                        <td className="py-3 pr-4 font-medium">{emp.first_name} {emp.last_name}</td>
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
                      </tr>
                    );
                  })}
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
                  </tr>
                </thead>
                <tbody>
                  {staff.map((emp) => {
                    const pct = emp.total_earned > 0 ? (emp.remaining / emp.total_earned) * 100 : 0;
                    const barColor = pct > 50 ? 'bg-emerald-500' : pct > 25 ? 'bg-amber-500' : 'bg-red-500';
                    return (
                      <tr key={emp.user_id} className="border-b last:border-0 hover:bg-gray-50" data-testid={`hr-row-${emp.user_id}`}>
                        <td className="py-3 pr-4 font-medium">{emp.first_name} {emp.last_name}</td>
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
                      </tr>
                    );
                  })}
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
    </div>
  );
};

export default SecretaryHR;
