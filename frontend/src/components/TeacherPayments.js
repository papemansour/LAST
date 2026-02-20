import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Printer, Download, Wallet, TrendingUp, TrendingDown, Calendar, Clock, AlertCircle } from 'lucide-react';

const TeacherPayments = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [upcomingBalance, setUpcomingBalance] = useState(null);

  useEffect(() => {
    fetchPayments();
    fetchUpcomingBalance();
  }, []);

  const fetchPayments = async () => {
    try {
      const response = await apiClient.get('/teacher/my-payments');
      setPayments(response.data);
    } catch (error) {
      console.error('Error fetching payments:', error);
      toast.error('Erreur lors du chargement des bulletins');
    } finally {
      setLoading(false);
    }
  };

  const fetchUpcomingBalance = async () => {
    try {
      const response = await apiClient.get('/teacher/upcoming-balance');
      setUpcomingBalance(response.data);
    } catch (error) {
      console.error('Error fetching upcoming balance:', error);
    }
  };

  const printPayslip = (payment) => {
    const currency = payment.currency || 'EUR';
    const amountBrut = parseFloat(payment.amount || 0);
    const bonus = parseFloat(payment.bonus || 0);
    const deductions = parseInt(payment.deductions || 0);
    const deductionUnitValue = currency === 'EUR' ? 5 : 1500;
    const deductionsAmount = deductions * deductionUnitValue;
    const montantInitial = amountBrut + bonus;
    const montantNet = Math.max(0, montantInitial - deductionsAmount);
    const hasDeductions = deductions > 0;
    // Use invoice_ref from backend if available
    const invoiceNumber = payment.invoice_ref || `FAC-${new Date().getFullYear()}-${payment.id?.slice(0, 3).toUpperCase() || 'XXX'}`;

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Bulletin de Salaire - MyKalama English</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; color: #333; }
          .header { display: flex; justify-content: space-between; border-bottom: 3px solid #059669; padding-bottom: 20px; margin-bottom: 30px; }
          .logo { font-size: 24px; font-weight: bold; color: #059669; }
          .invoice-info { text-align: right; }
          .invoice-number { font-size: 20px; font-weight: bold; color: #059669; }
          .parties { display: flex; justify-content: space-between; margin: 30px 0; }
          .party { width: 45%; }
          .party-title { font-weight: bold; color: #059669; margin-bottom: 10px; border-bottom: 2px solid #d1fae5; padding-bottom: 5px; }
          .party p { margin: 5px 0; font-size: 14px; }
          table { width: 100%; border-collapse: collapse; margin: 30px 0; }
          th { background: #059669; color: white; padding: 12px; text-align: left; }
          td { padding: 12px; border-bottom: 1px solid #e5e7eb; }
          .totals { width: 400px; margin-left: auto; }
          .totals tr td { padding: 8px 12px; }
          .totals .initial-row { background: #f3f4f6; }
          .totals .deduction-row { background: #fef2f2; color: #dc2626; }
          .totals .net-row { background: #d1fae5; font-weight: bold; font-size: 18px; }
          .deduction-info { background: #fef2f2; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626; }
          .footer { margin-top: 50px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #666; }
          .stamp { text-align: center; margin: 30px 0; }
          .stamp-text { display: inline-block; padding: 15px 40px; border: 3px solid #059669; border-radius: 10px; color: #059669; font-weight: bold; font-size: 18px; transform: rotate(-3deg); }
          @media print { body { print-color-adjust: exact; -webkit-print-color-adjust: exact; } }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="logo">🎓 MyKalama English</div>
            <p style="margin-top: 10px; color: #666;">Société de Formation en Langues</p>
          </div>
          <div class="invoice-info">
            <div class="invoice-number">BULLETIN DE SALAIRE</div>
            <p><strong>Réf :</strong> ${invoiceNumber}</p>
            <p><strong>Date :</strong> ${new Date(payment.created_at || Date.now()).toLocaleDateString('fr-FR')}</p>
            <p><strong>Période :</strong> ${payment.month || payment.period || 'Non spécifiée'}</p>
          </div>
        </div>
        
        <div class="parties">
          <div class="party">
            <div class="party-title">📍 ÉMETTEUR</div>
            <p><strong>Société MyKalama English</strong></p>
            <p>Paris, France</p>
            <p>Dakar, Sénégal</p>
            <p>📞 +221 78 260 75 49 / 78 528 68 89</p>
            <p>📧 mykalamaenglish@gmail.com</p>
          </div>
          <div class="party">
            <div class="party-title">👤 PROFESSEUR</div>
            <p><strong>${payment.teacher_name || 'Non spécifié'}</strong></p>
            <p>📧 ${payment.teacher_email || payment.email || ''}</p>
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Heures</th>
              <th>Montant</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>${payment.description || 'Cours de langue anglaise'}</td>
              <td>${payment.hours_worked || payment.hours || '-'} h</td>
              <td><strong>${amountBrut.toFixed(2)} ${currency}</strong></td>
            </tr>
            ${bonus > 0 ? `
            <tr>
              <td style="color: #059669;">+ Bonus / Prime</td>
              <td>-</td>
              <td style="color: #059669;">+${bonus.toFixed(2)} ${currency}</td>
            </tr>
            ` : ''}
          </tbody>
        </table>
        
        ${hasDeductions ? `
        <div class="deduction-info">
          <strong>⚠️ Déductions appliquées</strong><br/>
          <p>${deductions} cours manqué(s) × ${deductionUnitValue} ${currency} = <strong>-${deductionsAmount.toFixed(2)} ${currency}</strong></p>
        </div>
        ` : ''}
        
        <table class="totals">
          <tr class="initial-row">
            <td>Somme Initiale :</td>
            <td style="text-align: right;">${montantInitial.toFixed(2)} ${currency}</td>
          </tr>
          ${hasDeductions ? `
          <tr class="deduction-row">
            <td>Déductions (${deductions} cours) :</td>
            <td style="text-align: right;">- ${deductionsAmount.toFixed(2)} ${currency}</td>
          </tr>
          ` : ''}
          <tr class="net-row">
            <td>💰 SOMME NETTE ${hasDeductions ? 'APRÈS DÉDUCTIONS' : ''} :</td>
            <td style="text-align: right;">${montantNet.toFixed(2)} ${currency}</td>
          </tr>
        </table>
        
        <div class="stamp">
          <span class="stamp-text">✓ PAYÉ</span>
        </div>
        
        <div class="footer">
          <p><strong>Mode de paiement :</strong> Virement bancaire / Mobile Money</p>
          ${hasDeductions ? `<p><strong>Note :</strong> ${deductions} déduction(s) appliquée(s) pour cours manqué(s) (${deductionUnitValue} ${currency}/cours)</p>` : ''}
          <p style="margin-top: 20px; text-align: center;">
            <em>Merci pour votre confiance !</em>
          </p>
          <p style="text-align: center; margin-top: 10px;">
            © 2025 MyKalama English - Tous droits réservés
          </p>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  // Calculate totals separately for EUR and FCFA
  const totalNetEUR = payments
    .filter(p => (p.currency || 'EUR') === 'EUR')
    .reduce((sum, p) => sum + (p.montant_net || 0), 0);
  const totalNetFCFA = payments
    .filter(p => p.currency === 'FCFA')
    .reduce((sum, p) => sum + (p.montant_net || 0), 0);
  
  const totalDeductionsEUR = payments
    .filter(p => (p.currency || 'EUR') === 'EUR')
    .reduce((sum, p) => sum + (p.deductions_amount || 0), 0);
  const totalDeductionsFCFA = payments
    .filter(p => p.currency === 'FCFA')
    .reduce((sum, p) => sum + (p.deductions_amount || 0), 0);

  // Determine primary currency based on payments
  const hasEUR = payments.some(p => (p.currency || 'EUR') === 'EUR');
  const hasFCFA = payments.some(p => p.currency === 'FCFA');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-green-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Upcoming Balance Card - Solde à venir */}
      {upcomingBalance && (
        <Card className={`border-2 ${upcomingBalance.available ? 'bg-gradient-to-br from-amber-50 to-yellow-100 border-amber-300' : 'bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200'}`}>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-4 rounded-xl ${upcomingBalance.available ? 'bg-amber-500' : 'bg-gray-400'}`}>
                  <Clock className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
                    💰 Solde à Venir
                    {!upcomingBalance.available && (
                      <span className="text-xs bg-gray-200 px-2 py-1 rounded-full text-gray-600">
                        Disponible dans {upcomingBalance.available_from} jour(s)
                      </span>
                    )}
                  </h3>
                  {upcomingBalance.available ? (
                    <>
                      <p className="text-3xl font-bold text-amber-700">
                        {upcomingBalance.total_upcoming?.toFixed(2)} {upcomingBalance.currency}
                      </p>
                      <p className="text-sm text-amber-600 mt-1">
                        📅 Bulletin disponible : {upcomingBalance.bulletin_visible_from}
                      </p>
                    </>
                  ) : (
                    <p className="text-sm text-gray-500 mt-1">
                      {upcomingBalance.message}
                    </p>
                  )}
                </div>
              </div>
              {upcomingBalance.available && upcomingBalance.details?.length > 0 && (
                <div className="text-right">
                  <div className="flex items-center gap-2 text-amber-600 bg-amber-100 px-3 py-2 rounded-lg">
                    <AlertCircle className="w-4 h-4" />
                    <span className="text-sm font-medium">En attente de validation</span>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Total Net EUR */}
        {hasEUR && (
        <Card className="bg-gradient-to-br from-green-50 to-emerald-100 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-500 rounded-xl">
                <Wallet className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-green-700">Total Net Reçu (EUR)</p>
                <p className="text-2xl font-bold text-green-800">{totalNetEUR.toFixed(2)} €</p>
              </div>
            </div>
          </CardContent>
        </Card>
        )}
        
        {/* Total Net FCFA */}
        {hasFCFA && (
        <Card className="bg-gradient-to-br from-green-50 to-emerald-100 border-green-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-500 rounded-xl">
                <Wallet className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-green-700">Total Net Reçu (FCFA)</p>
                <p className="text-2xl font-bold text-green-800">{totalNetFCFA.toLocaleString()} FCFA</p>
              </div>
            </div>
          </CardContent>
        </Card>
        )}
        
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500 rounded-xl">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-blue-700">Bulletins</p>
                <p className="text-2xl font-bold text-blue-800">{payments.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Deductions EUR */}
        {totalDeductionsEUR > 0 && (
          <Card className="bg-gradient-to-br from-red-50 to-orange-100 border-red-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-red-500 rounded-xl">
                  <TrendingDown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-red-700">Total Déductions (EUR)</p>
                  <p className="text-2xl font-bold text-red-800">-{totalDeductionsEUR.toFixed(2)} €</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Deductions FCFA */}
        {totalDeductionsFCFA > 0 && (
          <Card className="bg-gradient-to-br from-red-50 to-orange-100 border-red-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-red-500 rounded-xl">
                  <TrendingDown className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-red-700">Total Déductions (FCFA)</p>
                  <p className="text-2xl font-bold text-red-800">-{totalDeductionsFCFA.toLocaleString()} FCFA</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Payments List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">💰</span>
            Mes Bulletins de Salaire
          </CardTitle>
        </CardHeader>
        <CardContent>
          {payments.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-5xl mb-4">📄</div>
              <h3 className="text-xl font-semibold mb-2">Aucun bulletin de salaire</h3>
              <p className="text-gray-500">Vos bulletins apparaîtront ici une fois générés par le secrétariat.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {payments.map((payment) => (
                <Card key={payment.id} className="hover:shadow-lg transition-shadow border-l-4 border-l-green-500">
                  <CardContent className="p-4">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar className="w-4 h-4 text-gray-500" />
                          <span className="font-semibold text-lg">{payment.month || payment.period || 'Période non spécifiée'}</span>
                        </div>
                        <p className="text-sm text-gray-600">
                          {payment.description || 'Cours de langue anglaise'}
                          {payment.hours_worked || payment.hours ? ` • ${payment.hours_worked || payment.hours}h` : ''}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          Créé le {new Date(payment.created_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-xs text-gray-500">Montant initial</p>
                        <p className="text-sm">{payment.montant_initial?.toFixed(2) || payment.amount} {payment.currency}</p>
                        
                        {payment.deductions > 0 && (
                          <>
                            <p className="text-xs text-red-500 mt-1">Déductions ({payment.deductions} cours)</p>
                            <p className="text-sm text-red-600">-{payment.deductions_amount?.toFixed(2)} {payment.currency}</p>
                          </>
                        )}
                        
                        <div className="mt-2 pt-2 border-t">
                          <p className="text-xs text-green-600 font-medium">SOMME NETTE</p>
                          <p className="text-xl font-bold text-green-700">{payment.montant_net?.toFixed(2)} {payment.currency}</p>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => printPayslip(payment)}
                          className="hover:bg-green-50"
                        >
                          <Printer className="w-4 h-4 mr-1" />
                          Imprimer
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            printPayslip(payment);
                            toast.success('💡 Utilisez Ctrl+P puis "Enregistrer en PDF"');
                          }}
                          className="hover:bg-blue-50"
                        >
                          <Download className="w-4 h-4 mr-1" />
                          PDF
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TeacherPayments;
