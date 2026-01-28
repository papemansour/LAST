import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Calendar, Clock, Users, RefreshCw, ChevronLeft, ChevronRight, Download, BarChart3 } from 'lucide-react';

const AdminMonthlyHours = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth() + 1);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [expandedTeacher, setExpandedTeacher] = useState(null);

  useEffect(() => {
    fetchMonthlyHours();
  }, [currentMonth, currentYear]);

  const fetchMonthlyHours = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/admin/monthly-teacher-hours?month=${currentMonth}&year=${currentYear}`);
      setData(res.data);
    } catch (error) {
      console.error('Error fetching monthly hours:', error);
      toast.error('Erreur lors du chargement des données');
    } finally {
      setLoading(false);
    }
  };

  const goToPreviousMonth = () => {
    if (currentMonth === 1) {
      setCurrentMonth(12);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const goToNextMonth = () => {
    if (currentMonth === 12) {
      setCurrentMonth(1);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
  };

  const handleExportCSV = () => {
    if (!data || !data.teachers.length) return;
    
    const headers = ['Professeur', 'Email', 'Heures Totales', 'Sessions', 'Minutes Totales'];
    const rows = data.teachers.map(t => [
      t.teacher_name,
      t.teacher_email,
      t.total_hours,
      t.total_sessions,
      t.total_minutes
    ]);
    
    const csvContent = [
      `Récapitulatif ${data.month_name} ${data.year}`,
      '',
      headers.join(','),
      ...rows.map(r => r.join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `recap_heures_${data.month_name}_${data.year}.csv`;
    link.click();
    toast.success('Export CSV téléchargé');
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-blue-600" />
                Récapitulatif Mensuel des Heures
              </CardTitle>
              <CardDescription>
                Total des heures effectuées par chaque professeur
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={goToPreviousMonth}>
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="font-semibold text-lg min-w-[180px] text-center">
                {data?.month_name} {data?.year}
              </span>
              <Button variant="outline" size="sm" onClick={goToNextMonth}>
                <ChevronRight className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={fetchMonthlyHours}>
                <RefreshCw className="w-4 h-4" />
              </Button>
              <Button variant="outline" size="sm" onClick={handleExportCSV} disabled={!data?.teachers?.length}>
                <Download className="w-4 h-4 mr-1" />
                CSV
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Summary Stats */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-blue-600">{data?.total_hours_all || 0}h</p>
              <p className="text-sm text-blue-700">Heures Totales</p>
            </div>
            <div className="bg-green-50 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-green-600">{data?.total_teachers || 0}</p>
              <p className="text-sm text-green-700">Professeurs Actifs</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 text-center">
              <p className="text-3xl font-bold text-purple-600">
                {data?.teachers?.reduce((sum, t) => sum + t.total_sessions, 0) || 0}
              </p>
              <p className="text-sm text-purple-700">Sessions Totales</p>
            </div>
          </div>

          {/* Teachers List */}
          {!data?.teachers?.length ? (
            <div className="text-center py-8 text-gray-500">
              <Calendar className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p>Aucune session enregistrée pour ce mois</p>
            </div>
          ) : (
            <div className="space-y-3">
              {data.teachers.map((teacher, index) => (
                <div
                  key={teacher.teacher_id}
                  className={`border rounded-lg overflow-hidden ${
                    index === 0 ? 'border-yellow-400 bg-yellow-50' : 
                    index === 1 ? 'border-gray-400 bg-gray-50' :
                    index === 2 ? 'border-orange-400 bg-orange-50' : ''
                  }`}
                >
                  <div
                    className="p-4 flex items-center justify-between cursor-pointer hover:bg-white/50 transition"
                    onClick={() => setExpandedTeacher(expandedTeacher === teacher.teacher_id ? null : teacher.teacher_id)}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-white ${
                        index === 0 ? 'bg-yellow-500' :
                        index === 1 ? 'bg-gray-500' :
                        index === 2 ? 'bg-orange-500' : 'bg-blue-500'
                      }`}>
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : index + 1}
                      </div>
                      <div>
                        <p className="font-semibold">{teacher.teacher_name}</p>
                        <p className="text-sm text-gray-500">{teacher.teacher_email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <p className="text-2xl font-bold text-blue-600">{teacher.total_hours}h</p>
                        <p className="text-xs text-gray-500">{formatDuration(teacher.total_minutes)}</p>
                      </div>
                      <div className="text-center px-4 border-l">
                        <p className="text-lg font-semibold">{teacher.total_sessions}</p>
                        <p className="text-xs text-gray-500">sessions</p>
                      </div>
                    </div>
                  </div>
                  
                  {/* Expanded sessions */}
                  {expandedTeacher === teacher.teacher_id && teacher.sessions?.length > 0 && (
                    <div className="border-t bg-white p-4">
                      <p className="text-sm font-semibold text-gray-600 mb-2">
                        Dernières sessions:
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-2">
                        {teacher.sessions.map((session, idx) => (
                          <div key={idx} className="bg-gray-50 rounded p-2 text-center text-sm">
                            <p className="font-medium">
                              {session.date ? new Date(session.date).toLocaleDateString('fr-FR') : 'N/A'}
                            </p>
                            <p className="text-gray-500">{formatDuration(session.duration_minutes)}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default AdminMonthlyHours;
