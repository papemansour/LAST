import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { TrendingUp, Users, Clock, DollarSign, RefreshCw, Calendar, Award, Pencil, Save, X } from 'lucide-react';

const COLORS = ['#0d9488', '#0891b2', '#7c3aed', '#db2777', '#ea580c', '#16a34a'];

const AdminAnalytics = () => {
  const [loading, setLoading] = useState(true);
  const [analytics, setAnalytics] = useState(null);
  const [period, setPeriod] = useState('month'); // week, month, year
  const [currency, setCurrency] = useState('EUR'); // EUR, FCFA
  
  // États pour l'édition des revenus
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingMonth, setEditingMonth] = useState(null);
  const [editForm, setEditForm] = useState({
    incoming_eur: 0,
    incoming_fcfa: 0,
    outgoing_eur: 0,
    outgoing_fcfa: 0
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, [period]);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/admin/analytics?period=${period}`);
      setAnalytics(res.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Erreur lors du chargement des statistiques');
      // Use mock data if API fails
      setAnalytics(getMockData());
    } finally {
      setLoading(false);
    }
  };

  const getMockData = () => ({
    summary: {
      total_students: 40,
      active_students: 35,
      total_teachers: 4,
      total_hours_this_month: 120,
      incoming_eur: 2500,
      incoming_fcfa: 850000,
      outgoing_eur: 1200,
      outgoing_fcfa: 400000,
      net_eur: 1300,
      net_fcfa: 450000,
      growth_rate: 12.5
    },
    students_by_month: [
      { month: 'Août', count: 25 },
      { month: 'Sept', count: 28 },
      { month: 'Oct', count: 32 },
      { month: 'Nov', count: 36 },
      { month: 'Déc', count: 38 },
      { month: 'Jan', count: 40 }
    ],
    hours_by_semester: [
      { semester: 'Jan-Mar 2025', hours: 320, label: 'T1 2025' },
      { semester: 'Avr-Juin 2025', hours: 380, label: 'T2 2025' },
      { semester: 'Juil-Sept 2025', hours: 290, label: 'T3 2025' },
      { semester: 'Oct-Déc 2025', hours: 410, label: 'T4 2025' },
      { semester: 'Jan-Mar 2026', hours: 180, label: 'T1 2026' }
    ],
    revenue_by_month: [
      { month: 'Août', incoming_eur: 1800, incoming_fcfa: 600000, outgoing_eur: 900, outgoing_fcfa: 300000 },
      { month: 'Sept', incoming_eur: 2000, incoming_fcfa: 680000, outgoing_eur: 950, outgoing_fcfa: 320000 },
      { month: 'Oct', incoming_eur: 2200, incoming_fcfa: 720000, outgoing_eur: 1000, outgoing_fcfa: 350000 },
      { month: 'Nov', incoming_eur: 2350, incoming_fcfa: 780000, outgoing_eur: 1100, outgoing_fcfa: 380000 },
      { month: 'Déc', incoming_eur: 2400, incoming_fcfa: 820000, outgoing_eur: 1150, outgoing_fcfa: 390000 },
      { month: 'Jan', incoming_eur: 2500, incoming_fcfa: 850000, outgoing_eur: 1200, outgoing_fcfa: 400000 }
    ],
    students_by_level: [
      { name: 'Débutant', value: 15 },
      { name: 'Intermédiaire', value: 12 },
      { name: 'Avancé', value: 8 },
      { name: 'K-Kid', value: 5 }
    ],
    top_teachers: [
      { name: 'Prof. Martin', hours: 45, students: 12 },
      { name: 'Prof. Dupont', hours: 38, students: 10 },
      { name: 'Prof. Bernard', hours: 25, students: 8 },
      { name: 'Prof. Laurent', hours: 12, students: 5 }
    ]
  });

  // Fonction pour ouvrir le dialog d'édition
  const handleEditRevenue = (monthData) => {
    setEditingMonth(monthData.month);
    setEditForm({
      incoming_eur: monthData.incoming_eur || 0,
      incoming_fcfa: monthData.incoming_fcfa || 0,
      outgoing_eur: monthData.outgoing_eur || 0,
      outgoing_fcfa: monthData.outgoing_fcfa || 0
    });
    setEditDialogOpen(true);
  };

  // Fonction pour sauvegarder les modifications
  const handleSaveRevenue = async () => {
    setSaving(true);
    try {
      await apiClient.post('/admin/update-revenue', {
        month: editingMonth,
        ...editForm
      });
      toast.success(`Revenus de ${editingMonth} mis à jour !`);
      setEditDialogOpen(false);
      fetchAnalytics(); // Recharger les données
    } catch (error) {
      console.error('Error updating revenue:', error);
      toast.error('Erreur lors de la mise à jour des revenus');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement des statistiques...</p>
        </CardContent>
      </Card>
    );
  }

  const data = analytics || getMockData();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <TrendingUp className="w-7 h-7 text-teal-600" />
            Tableau de Bord Analytique
          </h2>
          <p className="text-gray-500">Vue d'ensemble de la croissance de la plateforme</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="week">Cette semaine</option>
            <option value="month">Ce mois</option>
            <option value="year">Cette année</option>
          </select>
          <Button variant="outline" size="sm" onClick={fetchAnalytics}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Actualiser
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-teal-500 to-teal-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-teal-100 text-sm">Étudiants</p>
                <p className="text-3xl font-bold">{data.summary.total_students}</p>
                <p className="text-teal-200 text-xs">+{data.summary.growth_rate}% ce mois</p>
              </div>
              <Users className="w-10 h-10 text-teal-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-500 to-blue-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-100 text-sm">Professeurs</p>
                <p className="text-3xl font-bold">{data.summary.total_teachers}</p>
                <p className="text-blue-200 text-xs">Actifs</p>
              </div>
              <Award className="w-10 h-10 text-blue-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-purple-500 to-purple-600 text-white">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-100 text-sm">Heures ce mois</p>
                <p className="text-3xl font-bold">{data.summary.total_hours_this_month}h</p>
                <p className="text-purple-200 text-xs">De cours dispensés</p>
              </div>
              <Clock className="w-10 h-10 text-purple-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500 to-green-600 text-white cursor-pointer hover:from-green-600 hover:to-green-700 transition-all" onClick={() => setCurrency(currency === 'EUR' ? 'FCFA' : 'EUR')}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-100 text-sm flex items-center gap-1">
                  Revenus nets
                  <span className="text-xs bg-green-400/30 px-1.5 py-0.5 rounded">{currency}</span>
                </p>
                {currency === 'EUR' ? (
                  <>
                    <p className="text-2xl font-bold">{data.summary.net_eur || 0}€</p>
                    <p className="text-green-200 text-xs">
                      +{data.summary.incoming_eur || 0}€ / -{data.summary.outgoing_eur || 0}€
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-2xl font-bold">{(data.summary.net_fcfa || 0).toLocaleString()} F</p>
                    <p className="text-green-200 text-xs">
                      +{(data.summary.incoming_fcfa || 0).toLocaleString()} / -{(data.summary.outgoing_fcfa || 0).toLocaleString()}
                    </p>
                  </>
                )}
              </div>
              <DollarSign className="w-10 h-10 text-green-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1 */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Students Growth */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-teal-600" />
              Évolution des Inscriptions
            </CardTitle>
            <CardDescription>Nombre d'étudiants par mois</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={data.students_by_month}>
                <defs>
                  <linearGradient id="colorStudents" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0d9488" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#0d9488" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Area 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#0d9488" 
                  fillOpacity={1} 
                  fill="url(#colorStudents)"
                  name="Étudiants"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Hours per Semester */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-purple-600" />
              Heures de Cours par Trimestre
            </CardTitle>
            <CardDescription>Volume d'heures enseignées par trimestre</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={data.hours_by_semester || data.hours_by_week}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="label" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value}h`, 'Heures']} />
                <Bar dataKey="hours" fill="#7c3aed" radius={[4, 4, 0, 0]} name="Heures" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Revenue */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  Revenus Mensuels ({currency})
                </CardTitle>
                <CardDescription>Entrées (reçus élèves) vs Sorties (paiements profs)</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
                  <button
                    onClick={() => setCurrency('EUR')}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                      currency === 'EUR' 
                        ? 'bg-white text-green-600 shadow-sm' 
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    EUR €
                  </button>
                  <button
                    onClick={() => setCurrency('FCFA')}
                    className={`px-3 py-1 text-sm font-medium rounded-md transition-all ${
                      currency === 'FCFA' 
                        ? 'bg-white text-green-600 shadow-sm' 
                        : 'text-gray-500 hover:text-gray-700'
                    }`}
                  >
                    FCFA
                  </button>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={data.revenue_by_month}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={(value) => currency === 'FCFA' ? `${(value/1000).toFixed(0)}k` : value} />
                <Tooltip formatter={(value) => currency === 'EUR' ? `${value}€` : `${value.toLocaleString()} FCFA`} />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey={currency === 'EUR' ? 'incoming_eur' : 'incoming_fcfa'}
                  stroke="#16a34a" 
                  strokeWidth={3}
                  dot={{ fill: '#16a34a', strokeWidth: 2 }}
                  name={currency === 'EUR' ? 'Entrées (€)' : 'Entrées (FCFA)'}
                />
                <Line 
                  type="monotone" 
                  dataKey={currency === 'EUR' ? 'outgoing_eur' : 'outgoing_fcfa'}
                  stroke="#dc2626" 
                  strokeWidth={3}
                  dot={{ fill: '#dc2626', strokeWidth: 2 }}
                  name={currency === 'EUR' ? 'Sorties (€)' : 'Sorties (FCFA)'}
                />
              </LineChart>
            </ResponsiveContainer>
            
            {/* Tableau des revenus avec bouton éditer */}
            <div className="mt-4 border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium text-gray-700">Mois</th>
                    <th className="px-3 py-2 text-right font-medium text-green-700">Entrées</th>
                    <th className="px-3 py-2 text-right font-medium text-red-700">Sorties</th>
                    <th className="px-3 py-2 text-right font-medium text-blue-700">Net</th>
                    <th className="px-3 py-2 text-center font-medium text-gray-700">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {data.revenue_by_month.map((row, idx) => {
                    const incoming = currency === 'EUR' ? row.incoming_eur : row.incoming_fcfa;
                    const outgoing = currency === 'EUR' ? row.outgoing_eur : row.outgoing_fcfa;
                    const net = incoming - outgoing;
                    return (
                      <tr key={row.month} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-3 py-2 font-medium">{row.month}</td>
                        <td className="px-3 py-2 text-right text-green-600">
                          {currency === 'EUR' ? `${incoming}€` : `${incoming.toLocaleString()} F`}
                        </td>
                        <td className="px-3 py-2 text-right text-red-600">
                          {currency === 'EUR' ? `${outgoing}€` : `${outgoing.toLocaleString()} F`}
                        </td>
                        <td className="px-3 py-2 text-right font-semibold text-blue-600">
                          {currency === 'EUR' ? `${net}€` : `${net.toLocaleString()} F`}
                        </td>
                        <td className="px-3 py-2 text-center">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleEditRevenue(row)}
                            className="h-7 px-2 text-gray-500 hover:text-blue-600"
                            data-testid={`edit-revenue-${row.month}`}
                          >
                            <Pencil className="w-3.5 h-3.5" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Students by Level */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="w-5 h-5 text-blue-600" />
              Répartition par Niveau
            </CardTitle>
            <CardDescription>Distribution des étudiants</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={data.students_by_level}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {data.students_by_level.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Top Teachers */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="w-5 h-5 text-amber-600" />
            Classement des Professeurs
          </CardTitle>
          <CardDescription>Par nombre d'heures enseignées ce mois</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {data.top_teachers.map((teacher, index) => (
              <div key={teacher.name} className="flex items-center gap-4">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                  index === 0 ? 'bg-amber-500' :
                  index === 1 ? 'bg-gray-400' :
                  index === 2 ? 'bg-orange-400' : 'bg-teal-500'
                }`}>
                  {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                </div>
                <div className="flex-1">
                  <p className="font-semibold">{teacher.name}</p>
                  <p className="text-sm text-gray-500">{teacher.students} étudiants</p>
                </div>
                <div className="text-right">
                  <p className="text-xl font-bold text-teal-600">{teacher.hours}h</p>
                </div>
                <div className="w-32 bg-gray-100 rounded-full h-2">
                  <div 
                    className="bg-teal-500 h-2 rounded-full" 
                    style={{ width: `${(teacher.hours / data.top_teachers[0].hours) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminAnalytics;
