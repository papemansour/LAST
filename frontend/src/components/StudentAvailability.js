import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Calendar, Clock, Save, RefreshCw, Check } from 'lucide-react';

const DAYS = [
  { id: 'monday', label: 'Lundi' },
  { id: 'tuesday', label: 'Mardi' },
  { id: 'wednesday', label: 'Mercredi' },
  { id: 'thursday', label: 'Jeudi' },
  { id: 'friday', label: 'Vendredi' },
  { id: 'saturday', label: 'Samedi' },
  { id: 'sunday', label: 'Dimanche' }
];

const TIME_SLOTS = [
  '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00',
  '15:00', '16:00', '17:00', '18:00', '19:00', '20:00', '21:00'
];

const StudentAvailability = () => {
  const [availability, setAvailability] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchAvailability();
  }, []);

  const fetchAvailability = async () => {
    try {
      const res = await apiClient.get('/student/my-availability');
      // Convert slots array to object for easy manipulation
      const slotsObj = {};
      (res.data.slots || []).forEach(slot => {
        const key = `${slot.day}-${slot.time}`;
        slotsObj[key] = slot.available;
      });
      setAvailability(slotsObj);
    } catch (error) {
      console.error('Error fetching availability:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleSlot = (day, time) => {
    const key = `${day}-${time}`;
    setAvailability(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Convert object back to slots array
      const slots = Object.entries(availability)
        .filter(([, available]) => available)
        .map(([key]) => {
          const [day, time] = key.split('-');
          return { day, time, available: true };
        });
      
      await apiClient.post('/student/set-availability', { slots });
      toast.success('Disponibilités enregistrées !');
    } catch (error) {
      toast.error('Erreur lors de l\'enregistrement');
    } finally {
      setSaving(false);
    }
  };

  const selectAllDay = (day) => {
    const newAvail = { ...availability };
    const allSelected = TIME_SLOTS.every(time => availability[`${day}-${time}`]);
    
    TIME_SLOTS.forEach(time => {
      newAvail[`${day}-${time}`] = !allSelected;
    });
    
    setAvailability(newAvail);
  };

  const clearAll = () => {
    setAvailability({});
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement...</p>
        </CardContent>
      </Card>
    );
  }

  const selectedCount = Object.values(availability).filter(Boolean).length;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-6 h-6 text-teal-600" />
                📅 Mes Disponibilités
              </CardTitle>
              <CardDescription>
                Sélectionnez vos créneaux disponibles pour les cours
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={clearAll}>
                Effacer tout
              </Button>
              <Button variant="outline" size="sm" onClick={fetchAvailability}>
                <RefreshCw className="w-4 h-4 mr-1" />
                Actualiser
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Stats */}
          <div className="mb-4 p-3 bg-teal-50 rounded-lg flex items-center justify-between">
            <span className="text-teal-700">
              <Clock className="w-4 h-4 inline mr-2" />
              {selectedCount} créneau(x) sélectionné(s)
            </span>
            <Button 
              onClick={handleSave}
              disabled={saving}
              className="bg-teal-600 hover:bg-teal-700"
            >
              <Save className="w-4 h-4 mr-2" />
              {saving ? 'Enregistrement...' : 'Enregistrer'}
            </Button>
          </div>

          {/* Calendar grid */}
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr>
                  <th className="p-2 border bg-gray-50 text-left w-20">Heure</th>
                  {DAYS.map(day => (
                    <th key={day.id} className="p-2 border bg-gray-50 text-center min-w-[100px]">
                      <button
                        onClick={() => selectAllDay(day.id)}
                        className="hover:text-teal-600 transition-colors"
                      >
                        {day.label}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TIME_SLOTS.map(time => (
                  <tr key={time}>
                    <td className="p-2 border bg-gray-50 font-medium text-sm">
                      {time}
                    </td>
                    {DAYS.map(day => {
                      const key = `${day.id}-${time}`;
                      const isSelected = availability[key];
                      
                      return (
                        <td key={key} className="p-1 border">
                          <button
                            onClick={() => toggleSlot(day.id, time)}
                            className={`w-full h-10 rounded transition-all flex items-center justify-center ${
                              isSelected
                                ? 'bg-teal-500 text-white hover:bg-teal-600'
                                : 'bg-gray-100 hover:bg-gray-200 text-gray-400'
                            }`}
                          >
                            {isSelected && <Check className="w-5 h-5" />}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Legend */}
          <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-teal-500 rounded flex items-center justify-center">
                <Check className="w-4 h-4 text-white" />
              </div>
              <span>Disponible</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 bg-gray-100 rounded"></div>
              <span>Non disponible</span>
            </div>
          </div>

          <p className="mt-4 text-xs text-gray-500">
            💡 Astuce : Cliquez sur le nom du jour pour sélectionner/désélectionner toute la journée.
            Vos disponibilités seront visibles par votre professeur.
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default StudentAvailability;
