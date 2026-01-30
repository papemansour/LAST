import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Trash2, Printer, Send, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

const EUR_TO_FCFA = 656;

const SecretaryBilling = ({ teachers, students, onRefresh }) => {
  const [billingTab, setBillingTab] = useState('teachers');
  const [teacherPayments, setTeacherPayments] = useState([]);
  const [studentReceipts, setStudentReceipts] = useState([]);
  const [prestataireInvoices, setPrestataireInvoices] = useState([]);
  const [billingStats, setBillingStats] = useState({
    totalPaid: 0,
    totalReceipts: 0,
    pendingPayments: 0
  });
  const [showStats, setShowStats] = useState(false);
  const [codeInput, setCodeInput] = useState('');
  const SECRET_CODE = '2811';
  const printRef = useRef(null);
  
  // New payment/receipt forms
  const [newPayment, setNewPayment] = useState({
    teacher_id: '',
    teacher_name: '',
    amount: '',
    currency: 'EUR',
    period: '',
    description: '',
    status: 'paid',
    email: '',
    bonus: 0,
    deductions: 0
  });
  
  const [newReceipt, setNewReceipt] = useState({
    student_id: '',
    student_name: '',
    pack_name: '',
    amount: '',
    currency: 'EUR',
    email: ''
  });
  
  const [newPrestataire, setNewPrestataire] = useState({
    name: '',
    service: '',
    amount: '',
    currency: 'EUR',
    email: ''
  });

  const fetchBillingData = async () => {
    try {
      const [paymentsRes, receiptsRes, invoicesRes, statsRes] = await Promise.all([
        apiClient.get('/secretary/teacher-payments'),
        apiClient.get('/secretary/student-receipts'),
        apiClient.get('/secretary/prestataire-invoices'),
        apiClient.get('/secretary/billing-stats')
      ]);
      setTeacherPayments(paymentsRes.data);
      setStudentReceipts(receiptsRes.data);
      setPrestataireInvoices(invoicesRes.data);
      setBillingStats(statsRes.data);
    } catch (error) {
      console.error('Error fetching billing:', error);
    }
  };

  useEffect(() => {
    fetchBillingData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCodeSubmit = () => {
    if (codeInput === SECRET_CODE) {
      setShowStats(true);
      toast.success('Code validé !');
    } else {
      toast.error('Code incorrect');
    }
    setCodeInput('');
  };

  // Calcul du montant final avec bonus et déductions (sans TVA)
  const calculateFinalAmount = (amount, bonus = 0, deductions = 0, currency) => {
    const baseAmount = parseFloat(amount) || 0;
    const bonusAmount = parseFloat(bonus) || 0;
    // Déduction: 1 = 5 EUR ou 1500 FCFA (cours manqué)
    const deductionValue = currency === 'EUR' ? 5 : 1500;
    const deductionsAmount = (parseFloat(deductions) || 0) * deductionValue;
    const finalAmount = baseAmount + bonusAmount - deductionsAmount;
    return {
      baseAmount: baseAmount.toFixed(2),
      bonusAmount: bonusAmount.toFixed(2),
      deductionsCount: deductions,
      deductionsAmount: deductionsAmount.toFixed(2),
      deductionUnitValue: deductionValue,
      finalAmount: Math.max(0, finalAmount).toFixed(2)
    };
  };

  // Télécharger en PDF
  const handleDownloadPDF = (item, type) => {
    const calcInfo = calculateFinalAmount(item.amount, item.bonus || 0, item.deductions || 0, item.currency);
    
    let content = '';
    if (type === 'teacher') {
      const hasDeductions = item.deductions > 0;
      content = `
        <html>
        <head>
          <title>Bulletin de Salaire - ${item.teacher_name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 2px solid #0d9488; padding-bottom: 20px; margin-bottom: 30px; }
            .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
            .invoice-info { display: flex; justify-content: space-between; margin-bottom: 30px; }
            .amount-box { font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; padding: 15px; border-radius: 8px; }
            .initial-amount { background: #f3f4f6; color: #374151; }
            .final-amount { background: #f0fdfa; color: #0d9488; font-size: 28px; }
            .details { background: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .footer { text-align: center; margin-top: 40px; color: #666; font-size: 12px; border-top: 1px solid #ddd; padding-top: 20px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #0d9488; color: white; }
            .bonus { color: green; }
            .deduction { color: #dc2626; }
            .deduction-info { background: #fef2f2; padding: 10px; border-radius: 6px; margin: 10px 0; font-size: 14px; color: #991b1b; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">🎓 MyKalamaEnglish</div>
            <p>Bulletin de Salaire Professeur</p>
          </div>
          <div class="invoice-info">
            <div>
              <strong>Destinataire:</strong><br/>
              ${item.teacher_name}<br/>
              ${item.email || ''}
            </div>
            <div style="text-align: right;">
              <strong>Date:</strong> ${new Date(item.created_at).toLocaleDateString('fr-FR')}<br/>
              <strong>Ref:</strong> SAL-${item.id.substring(0, 8).toUpperCase()}
            </div>
          </div>
          
          <table>
            <tr><th>Description</th><th>Période</th><th>Montant</th></tr>
            <tr>
              <td>${item.description || 'Cours de langue anglaise'}</td>
              <td>${item.period}</td>
              <td><strong>${calcInfo.baseAmount} ${item.currency}</strong></td>
            </tr>
            ${item.bonus > 0 ? `<tr><td class="bonus">+ Bonus</td><td></td><td class="bonus">+${calcInfo.bonusAmount} ${item.currency}</td></tr>` : ''}
          </table>
          
          <div class="amount-box initial-amount">
            Somme Initiale: ${calcInfo.baseAmount} ${item.currency}
          </div>
          
          ${hasDeductions ? `
            <div class="deduction-info">
              <strong>⚠️ Déductions appliquées:</strong><br/>
              ${item.deductions} cours manqué(s) × ${calcInfo.deductionUnitValue} ${item.currency} = <strong>-${calcInfo.deductionsAmount} ${item.currency}</strong>
            </div>
          ` : ''}
          
          <div class="amount-box final-amount">
            Somme Nette ${hasDeductions ? 'après Déductions' : ''}: ${calcInfo.finalAmount} ${item.currency}
          </div>
          
          <div class="footer">
            <p>MyKalamaEnglish - Plateforme d'apprentissage de l'anglais</p>
            <p>Ce bulletin de salaire a été généré automatiquement</p>
          </div>
        </body>
        </html>
      `;
    }
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.print();
  };

  const handleResetStats = async () => {
    if (!window.confirm('Voulez-vous vraiment remettre à zéro les statistiques de facturation ?')) return;
    try {
      await apiClient.post('/secretary/reset-billing-stats');
      toast.success('Statistiques remises à zéro');
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la remise à zéro');
    }
  };

  const handleDeletePayment = async (paymentId) => {
    if (!window.confirm('Supprimer cette facture ?')) return;
    try {
      await apiClient.delete(`/secretary/teacher-payments/${paymentId}`);
      toast.success('Facture supprimée');
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleDeleteReceipt = async (receiptId) => {
    if (!window.confirm('Supprimer ce reçu ?')) return;
    try {
      await apiClient.delete(`/secretary/student-receipts/${receiptId}`);
      toast.success('Reçu supprimé');
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleDeletePrestataire = async (invoiceId) => {
    if (!window.confirm('Supprimer cette facture ?')) return;
    try {
      await apiClient.delete(`/secretary/prestataire-invoices/${invoiceId}`);
      toast.success('Facture supprimée');
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handlePrintInvoice = (item, type) => {
    const printWindow = window.open('', '_blank');
    
    let content = '';
    if (type === 'teacher') {
      const calc = calculateFinalAmount(item.amount, item.bonus || 0, item.deductions || 0, item.currency);
      const hasDeductions = item.deductions > 0;
      content = `
        <html>
        <head>
          <title>Bulletin de Salaire - ${item.teacher_name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 2px solid #0d9488; padding-bottom: 20px; margin-bottom: 30px; }
            .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
            .invoice-info { display: flex; justify-content: space-between; margin-bottom: 30px; }
            .amount-box { font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; padding: 15px; border-radius: 8px; }
            .initial-amount { background: #f3f4f6; color: #374151; }
            .final-amount { background: #f0fdfa; color: #0d9488; font-size: 28px; }
            .details { background: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .footer { text-align: center; margin-top: 40px; color: #666; font-size: 12px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #0d9488; color: white; }
            .bonus { color: green; }
            .deduction { color: #dc2626; }
            .deduction-info { background: #fef2f2; padding: 10px; border-radius: 6px; margin: 10px 0; font-size: 14px; color: #991b1b; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">🎓 MyKalamaEnglish</div>
            <p>Bulletin de Salaire Professeur</p>
          </div>
          <div class="invoice-info">
            <div>
              <strong>Destinataire:</strong><br/>
              ${item.teacher_name}<br/>
              ${item.email || ''}
            </div>
            <div style="text-align: right;">
              <strong>Date:</strong> ${new Date(item.created_at).toLocaleDateString('fr-FR')}<br/>
              <strong>Ref:</strong> SAL-${item.id.substring(0, 8).toUpperCase()}
            </div>
          </div>
          
          <table>
            <tr><th>Description</th><th>Période</th><th>Montant</th></tr>
            <tr>
              <td>${item.description || 'Cours de langue anglaise'}</td>
              <td>${item.period}</td>
              <td><strong>${calc.baseAmount} ${item.currency}</strong></td>
            </tr>
            ${item.bonus > 0 ? `<tr><td class="bonus">+ Bonus</td><td></td><td class="bonus">+${calc.bonusAmount} ${item.currency}</td></tr>` : ''}
          </table>
          
          <div class="amount-box initial-amount">
            Somme Initiale: ${calc.baseAmount} ${item.currency}
          </div>
          
          ${hasDeductions ? `
            <div class="deduction-info">
              <strong>⚠️ Déductions appliquées:</strong><br/>
              ${item.deductions} cours manqué(s) × ${calc.deductionUnitValue} ${item.currency} = <strong>-${calc.deductionsAmount} ${item.currency}</strong>
            </div>
          ` : ''}
          
          <div class="amount-box final-amount">
            Somme Nette ${hasDeductions ? 'après Déductions' : ''}: ${calc.finalAmount} ${item.currency}
          </div>
          
          <div class="footer">
            <p>MyKalamaEnglish - Formation en anglais</p>
          </div>
        </body>
        </html>
      `;
    } else if (type === 'student') {
      content = `
        <html>
        <head>
          <title>Reçu Élève - ${item.student_name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 2px solid #0d9488; padding-bottom: 20px; margin-bottom: 30px; }
            .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
            .amount { font-size: 28px; font-weight: bold; color: #0d9488; text-align: center; margin: 30px 0; padding: 20px; background: #f0fdfa; border-radius: 8px; }
            .details { background: #f9fafb; padding: 20px; border-radius: 8px; }
            .footer { text-align: center; margin-top: 40px; color: #666; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">🎓 MyKalamaEnglish</div>
            <p>Reçu de Paiement</p>
          </div>
          <div class="details">
            <p><strong>Élève:</strong> ${item.student_name}</p>
            <p><strong>Pack:</strong> ${item.pack_name}</p>
            <p><strong>Date:</strong> ${new Date(item.created_at).toLocaleDateString('fr-FR')}</p>
          </div>
          <div class="amount">
            Montant payé: ${item.amount} ${item.currency}
            ${item.currency === 'EUR' ? `<br/><small>(${Math.round(item.amount * EUR_TO_FCFA).toLocaleString()} FCFA)</small>` : ''}
          </div>
          <div class="footer">
            <p>Merci pour votre confiance !</p>
            <p>MyKalamaEnglish - Formation en anglais</p>
          </div>
        </body>
        </html>
      `;
    } else if (type === 'prestataire') {
      content = `
        <html>
        <head>
          <title>Facture Prestataire - ${item.name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 2px solid #0d9488; padding-bottom: 20px; margin-bottom: 30px; }
            .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
            .amount { font-size: 28px; font-weight: bold; color: #0d9488; text-align: center; margin: 30px 0; padding: 20px; background: #f0fdfa; border-radius: 8px; }
            .details { background: #f9fafb; padding: 20px; border-radius: 8px; }
            .footer { text-align: center; margin-top: 40px; color: #666; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">🎓 MyKalamaEnglish</div>
            <p>Facture Prestataire</p>
          </div>
          <div class="details">
            <p><strong>Prestataire:</strong> ${item.name}</p>
            <p><strong>Service:</strong> ${item.service}</p>
            <p><strong>Date:</strong> ${new Date(item.created_at).toLocaleDateString('fr-FR')}</p>
          </div>
          <div class="amount">
            Montant: ${item.amount} ${item.currency}
          </div>
          <div class="footer">
            <p>MyKalamaEnglish - Formation en anglais</p>
          </div>
        </body>
        </html>
      `;
    }
    
    printWindow.document.write(content);
    printWindow.document.close();
    printWindow.print();
  };

  const handleSendEmail = async (item, type) => {
    if (!item.email) {
      toast.error('Pas d\'email disponible');
      return;
    }
    try {
      await apiClient.post('/secretary/send-invoice-email', {
        type,
        item_id: item.id,
        email: item.email
      });
      toast.success('Email envoyé !');
    } catch (error) {
      toast.error('Erreur lors de l\'envoi');
    }
  };

  const handleCreatePayment = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/secretary/teacher-payments', newPayment);
      toast.success('Facture créée');
      setNewPayment({ teacher_id: '', teacher_name: '', amount: '', currency: 'EUR', period: '', description: '', status: 'paid', email: '', bonus: 0, deductions: 0 });
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleCreateReceipt = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/secretary/student-receipts', newReceipt);
      toast.success('Reçu créé');
      setNewReceipt({ student_id: '', student_name: '', pack_name: '', amount: '', currency: 'EUR', email: '' });
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleCreatePrestataire = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/secretary/prestataire-invoices', newPrestataire);
      toast.success('Facture créée');
      setNewPrestataire({ name: '', service: '', amount: '', currency: 'EUR', email: '' });
      fetchBillingData();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Section with Code */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>📊 Statistiques de Facturation</span>
            <Button variant="outline" size="sm" onClick={fetchBillingData}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Actualiser
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!showStats ? (
            <div className="flex items-center gap-4">
              <Input
                type="password"
                placeholder="Entrez le code secret"
                value={codeInput}
                onChange={(e) => setCodeInput(e.target.value)}
                className="max-w-xs"
              />
              <Button onClick={handleCodeSubmit}>Valider</Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">{billingStats.totalPaid?.toLocaleString() || 0} €</p>
                  <p className="text-sm text-gray-600">Total Payé aux Profs</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">{billingStats.totalReceipts || 0}</p>
                  <p className="text-sm text-gray-600">Reçus Générés</p>
                </div>
                <div className="text-center p-4 bg-orange-50 rounded-lg">
                  <p className="text-2xl font-bold text-orange-600">{billingStats.pendingPayments || 0}</p>
                  <p className="text-sm text-gray-600">Paiements en Attente</p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={handleResetStats} className="text-red-600">
                🔄 Remettre à zéro les statistiques
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Billing Tabs */}
      <div className="flex gap-2 mb-4">
        <Button
          variant={billingTab === 'teachers' ? 'default' : 'outline'}
          onClick={() => setBillingTab('teachers')}
        >
          👨‍🏫 Profs ({teacherPayments.length})
        </Button>
        <Button
          variant={billingTab === 'students' ? 'default' : 'outline'}
          onClick={() => setBillingTab('students')}
        >
          👨‍🎓 Élèves ({studentReceipts.length})
        </Button>
        <Button
          variant={billingTab === 'prestataires' ? 'default' : 'outline'}
          onClick={() => setBillingTab('prestataires')}
        >
          🏢 Prestataires ({prestataireInvoices.length})
        </Button>
      </div>

      {/* Teacher Payments */}
      {billingTab === 'teachers' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>➕ Nouvelle Facture Professeur</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreatePayment} className="grid grid-cols-2 gap-4">
                <Select
                  value={newPayment.teacher_id}
                  onValueChange={(value) => {
                    const teacher = teachers.find(t => t.id === value);
                    setNewPayment({
                      ...newPayment,
                      teacher_id: value,
                      teacher_name: teacher ? `${teacher.first_name} ${teacher.last_name}` : '',
                      email: teacher?.email || ''
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner un professeur" />
                  </SelectTrigger>
                  <SelectContent>
                    {teachers.map(t => (
                      <SelectItem key={t.id} value={t.id}>
                        {t.first_name} {t.last_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  placeholder="Montant de base"
                  value={newPayment.amount}
                  onChange={(e) => setNewPayment({ ...newPayment, amount: e.target.value })}
                  required
                />
                <Select
                  value={newPayment.currency}
                  onValueChange={(value) => setNewPayment({ ...newPayment, currency: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="EUR">EUR (€)</SelectItem>
                    <SelectItem value="FCFA">FCFA</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Période (ex: Janvier 2026)"
                  value={newPayment.period}
                  onChange={(e) => setNewPayment({ ...newPayment, period: e.target.value })}
                  required
                />
                <Input
                  type="number"
                  placeholder="Bonus (montant)"
                  value={newPayment.bonus}
                  onChange={(e) => setNewPayment({ ...newPayment, bonus: parseFloat(e.target.value) || 0 })}
                  className="bg-green-50 border-green-200"
                />
                <Input
                  type="number"
                  placeholder="Déductions (nb cours manqués)"
                  value={newPayment.deductions}
                  onChange={(e) => setNewPayment({ ...newPayment, deductions: parseInt(e.target.value) || 0 })}
                  className="bg-red-50 border-red-200"
                />
                <p className="text-xs text-gray-500 col-span-2">
                  💡 1 déduction = {newPayment.currency === 'EUR' ? '5 EUR' : '2000 FCFA'} (pénalité pour cours manqué)
                </p>
                <Textarea
                  placeholder="Description"
                  value={newPayment.description}
                  onChange={(e) => setNewPayment({ ...newPayment, description: e.target.value })}
                  className="col-span-2"
                />
                <Button type="submit" className="col-span-2">Créer la facture</Button>
              </form>
            </CardContent>
          </Card>

          {/* Payments List */}
          <div className="space-y-3">
            {teacherPayments.map(payment => {
              const calc = calculateFinalAmount(payment.amount, payment.bonus || 0, payment.deductions || 0, payment.currency);
              return (
                <Card key={payment.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between flex-wrap gap-4">
                      <div>
                        <h4 className="font-semibold">{payment.teacher_name}</h4>
                        <p className="text-sm text-gray-600">{payment.period} - {payment.description}</p>
                        <p className="text-sm text-gray-500">{payment.email}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-teal-600">{calc.finalAmount} {payment.currency}</p>
                        <p className="text-xs text-gray-500">Base: {calc.baseAmount} {payment.currency}</p>
                        {payment.bonus > 0 && <p className="text-xs text-green-600">+Bonus: {calc.bonusAmount}</p>}
                        {payment.deductions > 0 && <p className="text-xs text-red-600">-Déductions: {calc.deductionsAmount} ({payment.deductions} cours)</p>}
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handleDownloadPDF(payment, 'teacher')} title="Télécharger PDF">
                          <Printer className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => handleSendEmail(payment, 'teacher')}>
                          <Send className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="destructive" onClick={() => handleDeletePayment(payment.id)}>
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* Student Receipts */}
      {billingTab === 'students' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>➕ Nouveau Reçu Élève</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreateReceipt} className="grid grid-cols-2 gap-4">
                <Select
                  value={newReceipt.student_id}
                  onValueChange={(value) => {
                    const student = students.find(s => s.id === value);
                    setNewReceipt({
                      ...newReceipt,
                      student_id: value,
                      student_name: student ? `${student.first_name} ${student.last_name}` : '',
                      email: student?.email || ''
                    });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner un élève" />
                  </SelectTrigger>
                  <SelectContent>
                    {students.map(s => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.first_name} {s.last_name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  placeholder="Nom du pack"
                  value={newReceipt.pack_name}
                  onChange={(e) => setNewReceipt({ ...newReceipt, pack_name: e.target.value })}
                  required
                />
                <Input
                  type="number"
                  placeholder="Montant"
                  value={newReceipt.amount}
                  onChange={(e) => setNewReceipt({ ...newReceipt, amount: e.target.value })}
                  required
                />
                <Select
                  value={newReceipt.currency}
                  onValueChange={(value) => setNewReceipt({ ...newReceipt, currency: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="EUR">EUR (€)</SelectItem>
                    <SelectItem value="FCFA">FCFA</SelectItem>
                  </SelectContent>
                </Select>
                <Button type="submit" className="col-span-2">Créer le reçu</Button>
              </form>
            </CardContent>
          </Card>

          {/* Receipts List */}
          <div className="space-y-3">
            {studentReceipts.map(receipt => (
              <Card key={receipt.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold">{receipt.student_name}</h4>
                      <p className="text-sm text-gray-600">{receipt.pack_name}</p>
                      <p className="text-sm text-gray-500">{receipt.email}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-teal-600">{receipt.amount} {receipt.currency}</p>
                      {receipt.currency === 'EUR' && (
                        <p className="text-xs text-gray-500">{Math.round(receipt.amount * EUR_TO_FCFA).toLocaleString()} FCFA</p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => handlePrintInvoice(receipt, 'student')}>
                        <Printer className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => handleSendEmail(receipt, 'student')}>
                        <Send className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDeleteReceipt(receipt.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Prestataires */}
      {billingTab === 'prestataires' && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>➕ Nouvelle Facture Prestataire</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleCreatePrestataire} className="grid grid-cols-2 gap-4">
                <Input
                  placeholder="Nom du prestataire"
                  value={newPrestataire.name}
                  onChange={(e) => setNewPrestataire({ ...newPrestataire, name: e.target.value })}
                  required
                />
                <Input
                  placeholder="Service fourni"
                  value={newPrestataire.service}
                  onChange={(e) => setNewPrestataire({ ...newPrestataire, service: e.target.value })}
                  required
                />
                <Input
                  type="number"
                  placeholder="Montant"
                  value={newPrestataire.amount}
                  onChange={(e) => setNewPrestataire({ ...newPrestataire, amount: e.target.value })}
                  required
                />
                <Select
                  value={newPrestataire.currency}
                  onValueChange={(value) => setNewPrestataire({ ...newPrestataire, currency: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="EUR">EUR (€)</SelectItem>
                    <SelectItem value="FCFA">FCFA</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  type="email"
                  placeholder="Email"
                  value={newPrestataire.email}
                  onChange={(e) => setNewPrestataire({ ...newPrestataire, email: e.target.value })}
                  className="col-span-2"
                />
                <Button type="submit" className="col-span-2">Créer la facture</Button>
              </form>
            </CardContent>
          </Card>

          {/* Invoices List */}
          <div className="space-y-3">
            {prestataireInvoices.map(invoice => (
              <Card key={invoice.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold">{invoice.name}</h4>
                      <p className="text-sm text-gray-600">{invoice.service}</p>
                      <p className="text-sm text-gray-500">{invoice.email}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-teal-600">{invoice.amount} {invoice.currency}</p>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => handlePrintInvoice(invoice, 'prestataire')}>
                        <Printer className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="destructive" onClick={() => handleDeletePrestataire(invoice.id)}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SecretaryBilling;
