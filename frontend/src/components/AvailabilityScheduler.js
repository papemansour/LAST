import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import { Calendar, Plane, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const AvailabilityScheduler = ({ apiClient }) => {
  const days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];
  const dayKeys = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  const timeSlots = [
    '08:00', '09:00', '10:00', '11:00', '12:00', 
    '13:00', '14:00', '15:00', '16:00', '17:00', 
    '18:00', '19:00', '20:00'
  ];

  const [availability, setAvailability] = useState({
    monday: [],
    tuesday: [],
    wednesday: [],
    thursday: [],
    friday: [],
    saturday: [],
    sunday: []
  });
  const [loading, setLoading] = useState(false);
  
  // Leave request state
  const [leaveRequests, setLeaveRequests] = useState([]);
  const [newLeave, setNewLeave] = useState({
    start_date: '',
    end_date: '',
    reason: ''
  });
  const [submittingLeave, setSubmittingLeave] = useState(false);

  useEffect(() => {
    fetchAvailability();
    fetchLeaveRequests();
  }, []);

  const fetchAvailability = async () => {
    try {
      const response = await apiClient.get('/teacher/my-availability');
      if (response.data && response.data.availability) {
        setAvailability(response.data.availability);
      }
    } catch (error) {
      console.error('Error fetching availability:', error);
    }
  };

  const fetchLeaveRequests = async () => {
    try {
      const response = await apiClient.get('/teacher/my-leave-requests');
      setLeaveRequests(response.data || []);
    } catch (error) {
      console.error('Error fetching leave requests:', error);
    }
  };

  const toggleTimeSlot = (day, time) => {
    setAvailability(prev => {
      const daySlots = prev[day] || [];
      const isSelected = daySlots.includes(time);
      
      return {
        ...prev,
        [day]: isSelected 
          ? daySlots.filter(t => t !== time)
          : [...daySlots, time].sort()
      };
    });
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await apiClient.post('/teacher/set-availability', {
        availability: availability
      });
      toast.success('Disponibilités enregistrées avec succès!');
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement des disponibilités');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitLeave = async () => {
    if (!newLeave.start_date || !newLeave.end_date) {
      toast.error('Veuillez remplir les dates de début et fin');
      return;
    }
    
    if (new Date(newLeave.end_date) < new Date(newLeave.start_date)) {
      toast.error('La date de fin doit être après la date de début');
      return;
    }

    setSubmittingLeave(true);
    try {
      await apiClient.post('/teacher/leave-request', newLeave);
      toast.success('🏖️ Demande de congé envoyée ! En attente de validation admin.');
      setNewLeave({ start_date: '', end_date: '', reason: '' });
      fetchLeaveRequests();
    } catch (error) {
      toast.error('Erreur lors de l\'envoi de la demande');
    } finally {
      setSubmittingLeave(false);
    }
  };

  const cancelLeaveRequest = async (leaveId) => {
    if (!window.confirm('Annuler cette demande de congé ?')) return;
    
    try {
      await apiClient.delete(`/teacher/leave-request/${leaveId}`);
      toast.success('Demande annulée');
      fetchLeaveRequests();
    } catch (error) {
      toast.error('Erreur lors de l\'annulation');
    }
  };

  const isSelected = (day, time) => {
    return (availability[day] || []).includes(time);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700"><AlertCircle className="w-3 h-3" /> En attente</span>;
      case 'approved':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700"><CheckCircle className="w-3 h-3" /> Approuvé</span>;
      case 'rejected':
        return <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700"><XCircle className="w-3 h-3" /> Refusé</span>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6">
      {/* Leave Request Section - Blue Theme */}
      <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
        <CardHeader className="bg-blue-100/50">
          <CardTitle className="text-blue-800 flex items-center gap-2">
            <Plane className="w-6 h-6" />
            🏖️ Demande de Congé
          </CardTitle>
          <CardDescription className="text-blue-600">
            Posez vos congés ici - Validation requise par l'admin
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6">
          <div className="grid md:grid-cols-4 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-blue-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                Date de début *
              </label>
              <Input
                type="date"
                value={newLeave.start_date}
                onChange={(e) => setNewLeave({...newLeave, start_date: e.target.value})}
                className="border-blue-300 focus:border-blue-500"
                min={new Date().toISOString().split('T')[0]}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-blue-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                Date de fin *
              </label>
              <Input
                type="date"
                value={newLeave.end_date}
                onChange={(e) => setNewLeave({...newLeave, end_date: e.target.value})}
                className="border-blue-300 focus:border-blue-500"
                min={newLeave.start_date || new Date().toISOString().split('T')[0]}
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-blue-700 mb-1">
                Motif (optionnel)
              </label>
              <Input
                value={newLeave.reason}
                onChange={(e) => setNewLeave({...newLeave, reason: e.target.value})}
                placeholder="Ex: Vacances, Raison personnelle..."
                className="border-blue-300 focus:border-blue-500"
              />
            </div>
          </div>
          
          <Button 
            onClick={handleSubmitLeave}
            disabled={submittingLeave}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            <Plane className="w-4 h-4 mr-2" />
            {submittingLeave ? 'Envoi...' : 'Envoyer la demande'}
          </Button>

          {/* Leave Requests List */}
          {leaveRequests.length > 0 && (
            <div className="mt-6">
              <h4 className="text-sm font-semibold text-blue-800 mb-3">Mes demandes de congé</h4>
              <div className="space-y-2">
                {leaveRequests.map((leave) => (
                  <div 
                    key={leave.id} 
                    className={`p-3 rounded-lg border flex items-center justify-between ${
                      leave.status === 'approved' ? 'bg-green-50 border-green-200' :
                      leave.status === 'rejected' ? 'bg-red-50 border-red-200' :
                      'bg-blue-50 border-blue-200'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      <div>
                        <p className="font-medium text-gray-800">
                          📅 {new Date(leave.start_date).toLocaleDateString('fr-FR')} → {new Date(leave.end_date).toLocaleDateString('fr-FR')}
                        </p>
                        {leave.reason && <p className="text-sm text-gray-600">{leave.reason}</p>}
                        {leave.admin_comment && (
                          <p className="text-sm text-gray-500 italic mt-1">💬 Admin: {leave.admin_comment}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {getStatusBadge(leave.status)}
                      {leave.status === 'pending' && (
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => cancelLeaveRequest(leave.id)}
                          className="text-red-600 hover:bg-red-100"
                        >
                          Annuler
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Availability Grid */}
      <Card className="border-teal-100">
        <CardHeader className="bg-teal-50">
          <CardTitle className="text-teal-800 flex items-center gap-2">
            <Clock className="w-6 h-6" />
            Mes Horaires
          </CardTitle>
          <CardDescription>
            Sélectionnez vos créneaux disponibles (vert = disponible, rouge = indisponible)
          </CardDescription>
        </CardHeader>
      <CardContent className="pt-6">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="border p-2 bg-gray-50 text-left font-semibold">Horaire</th>
                {days.map((day, idx) => (
                  <th key={idx} className="border p-2 bg-gray-50 text-center font-semibold">
                    {day}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {timeSlots.map((time) => (
                <tr key={time}>
                  <td className="border p-2 font-medium text-gray-700">{time}</td>
                  {dayKeys.map((dayKey, idx) => {
                    const selected = isSelected(dayKey, time);
                    return (
                      <td key={idx} className="border p-1">
                        <button
                          onClick={() => toggleTimeSlot(dayKey, time)}
                          className={`w-full h-10 rounded transition-colors ${
                            selected 
                              ? 'bg-green-500 hover:bg-green-600 text-white' 
                              : 'bg-red-500 hover:bg-red-600 text-white'
                          }`}
                        >
                          {selected ? '✓' : '✗'}
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        <div className="mt-6 flex justify-end">
          <Button 
            onClick={handleSave} 
            disabled={loading}
            className="bg-teal-600 hover:bg-teal-700"
          >
            {loading ? 'Enregistrement...' : '💾 Enregistrer mes disponibilités'}
          </Button>
        </div>
      </CardContent>
    </Card>
    </div>
  );
};

export default AvailabilityScheduler;
