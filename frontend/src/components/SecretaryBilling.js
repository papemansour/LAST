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
    email: ''
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

  const calculateTVA = (amount, currency) => {
    const tvaRate = currency === 'EUR' ? 0.20 : 0.18;
    const netAmount = amount / (1 + tvaRate);
    const tvaAmount = amount - netAmount;
    return { netAmount: netAmount.toFixed(2), tvaAmount: tvaAmount.toFixed(2), tvaRate: (tvaRate * 100) };
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
    const tvaInfo = calculateTVA(parseFloat(item.amount), item.currency);
    
    let content = '';
    if (type === 'teacher') {
      content = `
        <html>
        <head>
          <title>Facture Professeur - ${item.teacher_name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
            .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
            .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
            .invoice-info { display: flex; justify-content: space-between; margin-bottom: 30px; }
            .amount { font-size: 28px; font-weight: bold; color: #0d9488; text-align: center; margin: 30px 0; }
            .details { background: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .footer { text-align: center; margin-top: 40px; color: #666; font-size: 12px; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background: #f3f4f6; }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="logo">🎓 MyKalamaEnglish</div>
            <p>Facture de Paiement Professeur</p>
          </div>
          <div class="invoice-info">
            <div>
              <strong>Destinataire:</strong><br/>
              ${item.teacher_name}<br/>
              ${item.email || ''}
            </div>
            <div style="text-align: right;">
              <strong>Date:</strong> ${new Date(item.created_at).toLocaleDateString('fr-FR')}<br/>
              <strong>Ref:</strong> ${item.id.substring(0, 8).toUpperCase()}
            </div>
          </div>
          <table>
            <tr><th>Description</th><th>Période</th><th>Montant TTC</th></tr>
            <tr>
              <td>${item.description || 'Paiement cours'}</td>
              <td>${item.period}</td>
              <td>${item.amount} ${item.currency}</td>
            </tr>
          </table>
          <div class="details">
            <p><strong>Montant TTC:</strong> ${item.amount} ${item.currency}</p>
            <p><strong>TVA (${tvaInfo.tvaRate}%):</strong> ${tvaInfo.tvaAmount} ${item.currency}</p>
            <p><strong>Montant Net:</strong> ${tvaInfo.netAmount} ${item.currency}</p>
          </div>
          <div class="amount">
            Montant Net: ${tvaInfo.netAmount} ${item.currency}
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
            .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }
            .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
            .amount { font-size: 28px; font-weight: bold; color: #0d9488; text-align: center; margin: 30px 0; }
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
      setNewPayment({ teacher_id: '', teacher_name: '', amount: '', currency: 'EUR', period: '', description: '', status: 'paid', email: '' });
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
                  placeholder="Montant TTC"
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
              const tva = calculateTVA(parseFloat(payment.amount), payment.currency);
              return (
                <Card key={payment.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold">{payment.teacher_name}</h4>
                        <p className="text-sm text-gray-600">{payment.period} - {payment.description}</p>
                        <p className="text-sm text-gray-500">{payment.email}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-lg font-bold text-teal-600">{tva.netAmount} {payment.currency}</p>
                        <p className="text-xs text-gray-500">TTC: {payment.amount} {payment.currency}</p>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => handlePrintInvoice(payment, 'teacher')}>
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
