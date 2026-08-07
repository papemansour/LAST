import React, { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { CalendarDays, TrendingDown, TrendingUp, Clock } from 'lucide-react';
import apiClient from '../utils/api';

const LeaveBalanceCard = ({ compact = false }) => {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchBalance = async () => {
      try {
        const response = await apiClient.get('/teacher/my-leave-balance');
        setBalance(response.data);
      } catch (error) {
        console.error('Error fetching leave balance:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchBalance();
  }, []);

  if (loading || !balance) return null;

  const percentage = balance.total_earned > 0 ? (balance.remaining / balance.total_earned) * 100 : 0;
  const barColor = percentage > 50 ? 'bg-emerald-500' : percentage > 25 ? 'bg-amber-500' : 'bg-red-500';

  if (compact) {
    return (
      <div className="flex items-center gap-2" data-testid="leave-balance-compact">
        <CalendarDays className="w-4 h-4 text-teal-600" />
        <span className="text-sm text-teal-700">
          <strong className="text-teal-800 text-lg">{balance.remaining}j</strong> / {balance.total_earned}j
        </span>
      </div>
    );
  }

  return (
    <Card className="bg-white/70 backdrop-blur-xl border-gray-200/60 shadow-lg" data-testid="leave-balance-card">
      <CardContent className="p-5">
        <div className="flex items-center gap-2 mb-4">
          <CalendarDays className="w-5 h-5 text-teal-600" />
          <h3 className="font-semibold text-gray-800">Compteur de Conges</h3>
        </div>
        
        <div className="grid grid-cols-3 gap-3 mb-4">
          <div className="text-center p-3 bg-emerald-50 rounded-lg">
            <TrendingUp className="w-4 h-4 mx-auto text-emerald-600 mb-1" />
            <p className="text-xl font-bold text-emerald-700">{balance.total_earned}</p>
            <p className="text-xs text-gray-500">Acquis</p>
          </div>
          <div className="text-center p-3 bg-amber-50 rounded-lg">
            <TrendingDown className="w-4 h-4 mx-auto text-amber-600 mb-1" />
            <p className="text-xl font-bold text-amber-700">{balance.total_taken}</p>
            <p className="text-xs text-gray-500">Pris</p>
          </div>
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <Clock className="w-4 h-4 mx-auto text-blue-600 mb-1" />
            <p className="text-xl font-bold text-blue-700">{balance.remaining}</p>
            <p className="text-xs text-gray-500">Restants</p>
          </div>
        </div>

        <div className="relative w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div 
            className={`h-full rounded-full transition-all duration-500 ${barColor}`}
            style={{ width: `${Math.min(100, percentage)}%` }}
          />
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          {balance.months_worked} mois travailles - 2.5j/mois (max 30j/an)
        </p>
      </CardContent>
    </Card>
  );
};

export default LeaveBalanceCard;
