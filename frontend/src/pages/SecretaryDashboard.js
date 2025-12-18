import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { LogOut, Calendar, FileText, MessageCircle, Plus, Trash2, Edit, Save, X } from 'lucide-react';

const SecretaryDashboard = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Meetings state
  const [meetings, setMeetings] = useState([]);
  const [newMeeting, setNewMeeting] = useState({
    title: '',
    date: '',
    time: '',
    attendees: '',
    notes: '',
    meetingLink: '',
    notifyProfs: [],
    notifyAdmin: false
  });
  
  // Notes state
  const [notes, setNotes] = useState([]);
  const [newNote, setNewNote] = useState({
    title: '',
    content: ''
  });
  const [editingNote, setEditingNote] = useState(null);
  
  // Messages state
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState({
    recipient: '',
    subject: '',
    content: ''
  });
  
  // Comptes rendus prof state
  const [profReports, setProfReports] = useState([]);
  const [newReport, setNewReport] = useState({
    profName: '',
    date: '',
    content: '',
    notes: ''
  });

  // Facturation state
  const [teacherPayments, setTeacherPayments] = useState([]);
  const [studentReceipts, setStudentReceipts] = useState([]);
  const [prestataireInvoices, setPrestataireInvoices] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [billingTab, setBillingTab] = useState('teachers'); // teachers, students, prestataires
  const [newPayment, setNewPayment] = useState({
    teacherId: '',
    teacherName: '',
    teacherEmail: '',
    teacherAddress: '',
    month: new Date().toISOString().slice(0, 7),
    amount: '',
    currency: 'EUR',
    hoursWorked: '',
    hourlyRate: '',
    bonus: '0',
    description: 'Cours de langue anglaise',
    notes: ''
  });
  const [newReceipt, setNewReceipt] = useState({
    studentId: '',
    studentName: '',
    packType: '',
    amount: '',
    currency: 'EUR',
    paymentMethod: 'Virement',
    notes: ''
  });
  const [newPrestataire, setNewPrestataire] = useState({
    name: '',
    service: '',
    amount: '',
    currency: 'EUR',
    description: '',
    notes: ''
  });
  const [billingStats, setBillingStats] = useState({
    totalPaidTeachers: 0,
    totalReceipts: 0,
    totalPrestataires: 0,
    pendingPayments: 0
  });

  // Taux de conversion EUR -> FCFA
  const EUR_TO_FCFA = 656;

  useEffect(() => {
    fetchUserData();
    loadAllData();
  }, []);

  const fetchUserData = async () => {
    try {
      const res = await apiClient.get('/auth/me');
      if (res.data.role !== 'secretary') {
        toast.error('Accès non autorisé');
        navigate('/');
        return;
      }
      setUser(res.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      toast.error('Session expirée');
      navigate('/secretary-login');
    } finally {
      setLoading(false);
    }
  };

  // Charger données depuis l'API backend
  const loadAllData = async () => {
    try {
      // Charger réunions depuis l'API
      const meetingsRes = await apiClient.get('/secretary/meetings');
      setMeetings(meetingsRes.data || []);
    } catch (error) {
      // Fallback localStorage si API échoue
      const savedMeetings = localStorage.getItem('secretary_meetings');
      if (savedMeetings) setMeetings(JSON.parse(savedMeetings));
    }
    
    try {
      // Charger comptes rendus depuis l'API
      const reportsRes = await apiClient.get('/secretary/reports');
      setProfReports(reportsRes.data || []);
    } catch (error) {
      const savedReports = localStorage.getItem('secretary_prof_reports');
      if (savedReports) setProfReports(JSON.parse(savedReports));
    }
    
    // Notes et messages restent en localStorage (données locales)
    const savedNotes = localStorage.getItem('secretary_notes');
    const savedMessages = localStorage.getItem('secretary_messages');
    if (savedNotes) setNotes(JSON.parse(savedNotes));
    if (savedMessages) setMessages(JSON.parse(savedMessages));
    
    // Charger données de facturation
    try {
      const [paymentsRes, receiptsRes, teachersRes, studentsRes] = await Promise.all([
        apiClient.get('/secretary/teacher-payments'),
        apiClient.get('/secretary/student-receipts'),
        apiClient.get('/secretary/teachers-list'),
        apiClient.get('/secretary/students-list')
      ]);
      setTeacherPayments(paymentsRes.data || []);
      setStudentReceipts(receiptsRes.data || []);
      setTeachers(teachersRes.data || []);
      setStudents(studentsRes.data || []);
      
      // Calculer les stats
      const totalPaid = (paymentsRes.data || []).reduce((sum, p) => sum + parseFloat(p.amount || 0), 0);
      const totalReceipts = (receiptsRes.data || []).reduce((sum, r) => sum + parseFloat(r.amount || 0), 0);
      setBillingStats({
        totalPaidTeachers: totalPaid,
        totalReceipts: totalReceipts,
        pendingPayments: (teachersRes.data || []).length - (paymentsRes.data || []).filter(p => p.month === new Date().toISOString().slice(0, 7)).length
      });
    } catch (error) {
      console.log('Billing data not available yet');
    }
  };

  // Sauvegarder dans localStorage (notes et messages)
  const saveNotes = (data) => {
    localStorage.setItem('secretary_notes', JSON.stringify(data));
    setNotes(data);
  };

  const saveMessages = (data) => {
    localStorage.setItem('secretary_messages', JSON.stringify(data));
    setMessages(data);
  };

  // Meetings handlers - API Backend
  const handleAddMeeting = async () => {
    if (!newMeeting.title || !newMeeting.date || !newMeeting.time) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await apiClient.post('/secretary/meetings', newMeeting);
      const res = await apiClient.get('/secretary/meetings');
      setMeetings(res.data || []);
      setNewMeeting({ 
        title: '', 
        date: '', 
        time: '', 
        attendees: '', 
        notes: '',
        meetingLink: '',
        notifyProfs: [],
        notifyAdmin: false
      });
      toast.success('Réunion ajoutée !');
    } catch (error) {
      console.error('Error adding meeting:', error);
      toast.error('Erreur lors de l\'ajout de la réunion');
    }
  };

  const handleDeleteMeeting = async (id) => {
    if (window.confirm('Supprimer cette réunion ?')) {
      try {
        await apiClient.delete(`/secretary/meetings/${id}`);
        setMeetings(meetings.filter(m => m.id !== id));
        toast.success('Réunion supprimée');
      } catch (error) {
        console.error('Error deleting meeting:', error);
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  // Notes handlers
  const handleAddNote = () => {
    if (!newNote.title || !newNote.content) {
      toast.error('Veuillez remplir le titre et le contenu');
      return;
    }

    const note = {
      id: Date.now(),
      ...newNote,
      createdAt: new Date().toISOString()
    };

    saveNotes([...notes, note]);
    setNewNote({ title: '', content: '' });
    toast.success('Note ajoutée !');
  };

  const handleUpdateNote = () => {
    if (!editingNote.title || !editingNote.content) {
      toast.error('Veuillez remplir le titre et le contenu');
      return;
    }

    saveNotes(notes.map(n => n.id === editingNote.id ? editingNote : n));
    setEditingNote(null);
    toast.success('Note mise à jour !');
  };

  const handleDeleteNote = (id) => {
    if (window.confirm('Supprimer cette note ?')) {
      saveNotes(notes.filter(n => n.id !== id));
      toast.success('Note supprimée');
    }
  };

  // Comptes rendus handlers - API Backend
  const handleAddReport = async () => {
    if (!newReport.profName || !newReport.date || !newReport.content) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await apiClient.post('/secretary/reports', newReport);
      const res = await apiClient.get('/secretary/reports');
      setProfReports(res.data || []);
      setNewReport({ profName: '', date: '', content: '', notes: '' });
      toast.success('Compte rendu ajouté !');
    } catch (error) {
      console.error('Error adding report:', error);
      toast.error('Erreur lors de l\'ajout du compte rendu');
    }
  };

  const handleDeleteReport = async (id) => {
    if (window.confirm('Supprimer ce compte rendu ?')) {
      try {
        await apiClient.delete(`/secretary/reports/${id}`);
        setProfReports(profReports.filter(r => r.id !== id));
        toast.success('Compte rendu supprimé');
      } catch (error) {
        console.error('Error deleting report:', error);
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  // Facturation handlers
  const handleAddTeacherPayment = async () => {
    if (!newPayment.teacherName || !newPayment.month || !newPayment.amount) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await apiClient.post('/secretary/teacher-payments', newPayment);
      const res = await apiClient.get('/secretary/teacher-payments');
      setTeacherPayments(res.data || []);
      setNewPayment({
        teacherId: '',
        teacherName: '',
        month: new Date().toISOString().slice(0, 7),
        amount: '',
        hoursWorked: '',
        bonus: '0',
        notes: ''
      });
      toast.success('💰 Paiement enregistré !');
    } catch (error) {
      console.error('Error adding payment:', error);
      toast.error('Erreur lors de l\'enregistrement du paiement');
    }
  };

  const handleAddStudentReceipt = async () => {
    if (!newReceipt.studentName || !newReceipt.packType || !newReceipt.amount) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await apiClient.post('/secretary/student-receipts', newReceipt);
      const res = await apiClient.get('/secretary/student-receipts');
      setStudentReceipts(res.data || []);
      setNewReceipt({
        studentId: '',
        studentName: '',
        packType: '',
        amount: '',
        paymentMethod: 'Virement',
        notes: ''
      });
      toast.success('🧾 Reçu généré !');
    } catch (error) {
      console.error('Error adding receipt:', error);
      toast.error('Erreur lors de la génération du reçu');
    }
  };

  const handleDeletePayment = async (id) => {
    if (window.confirm('Supprimer ce paiement ?')) {
      try {
        await apiClient.delete(`/secretary/teacher-payments/${id}`);
        setTeacherPayments(teacherPayments.filter(p => p.id !== id));
        toast.success('Paiement supprimé');
      } catch (error) {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  const handleDeleteReceipt = async (id) => {
    if (window.confirm('Supprimer ce reçu ?')) {
      try {
        await apiClient.delete(`/secretary/student-receipts/${id}`);
        setStudentReceipts(studentReceipts.filter(r => r.id !== id));
        toast.success('Reçu supprimé');
      } catch (error) {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  const printReceipt = (receipt) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Reçu de Paiement - MyKalama English</title>
        <style>
          body { font-family: Arial, sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; }
          .header { text-align: center; border-bottom: 3px solid #7c3aed; padding-bottom: 20px; margin-bottom: 30px; }
          .logo { font-size: 28px; font-weight: bold; color: #7c3aed; }
          .receipt-number { color: #666; font-size: 14px; margin-top: 10px; }
          .details { margin: 20px 0; }
          .row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
          .label { color: #666; }
          .value { font-weight: bold; }
          .amount { font-size: 24px; color: #059669; text-align: center; margin: 30px 0; padding: 20px; background: #ecfdf5; border-radius: 10px; }
          .footer { text-align: center; margin-top: 40px; color: #666; font-size: 12px; }
          .stamp { text-align: center; margin-top: 30px; }
          .stamp-text { display: inline-block; padding: 10px 30px; border: 3px solid #059669; border-radius: 10px; color: #059669; font-weight: bold; transform: rotate(-5deg); }
          @media print { body { print-color-adjust: exact; } }
        </style>
      </head>
      <body>
        <div class="header">
          <div class="logo">🎓 MyKalama English</div>
          <div class="receipt-number">Reçu N° ${receipt.id?.slice(0, 8).toUpperCase() || 'XXXXX'}</div>
        </div>
        <div class="details">
          <div class="row"><span class="label">Étudiant:</span><span class="value">${receipt.student_name || receipt.studentName}</span></div>
          <div class="row"><span class="label">Pack:</span><span class="value">${receipt.pack_type || receipt.packType}</span></div>
          <div class="row"><span class="label">Mode de paiement:</span><span class="value">${receipt.payment_method || receipt.paymentMethod}</span></div>
          <div class="row"><span class="label">Date:</span><span class="value">${new Date(receipt.created_at || Date.now()).toLocaleDateString('fr-FR')}</span></div>
          ${receipt.notes ? `<div class="row"><span class="label">Notes:</span><span class="value">${receipt.notes}</span></div>` : ''}
        </div>
        <div class="amount">
          <div style="font-size: 14px; color: #666;">Montant payé</div>
          <div style="font-size: 32px; font-weight: bold;">${receipt.amount} €</div>
        </div>
        <div class="stamp">
          <span class="stamp-text">✓ PAYÉ</span>
        </div>
        <div class="footer">
          <p>MyKalama English - Formation en Anglais</p>
          <p>contact@mykalamaenglish.com</p>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  // Imprimer facture professeur
  const printTeacherInvoice = (payment) => {
    const currency = payment.currency || 'EUR';
    const amount = parseFloat(payment.amount || 0);
    const bonus = parseFloat(payment.bonus || 0);
    const totalHT = amount + bonus;
    const tva = totalHT * 0.20;
    const totalTTC = totalHT + tva;
    const invoiceNumber = `FAC-PROF-${payment.id?.slice(0, 8).toUpperCase() || 'XXXXX'}`;
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Facture Professeur - MyKalama English</title>
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
          .totals { width: 300px; margin-left: auto; }
          .totals tr td { padding: 8px 12px; }
          .totals .total-row { background: #d1fae5; font-weight: bold; font-size: 18px; }
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
            <div class="invoice-number">FACTURE</div>
            <p><strong>N° :</strong> ${invoiceNumber}</p>
            <p><strong>Date :</strong> ${new Date(payment.created_at || Date.now()).toLocaleDateString('fr-FR')}</p>
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
            <div class="party-title">👤 DESTINATAIRE (Prestataire)</div>
            <p><strong>${payment.teacher_name || payment.teacherName}</strong></p>
            <p>${payment.teacher_email || 'Email non spécifié'}</p>
            <p>${payment.teacher_address || 'Adresse non spécifiée'}</p>
          </div>
        </div>
        
        <table>
          <thead>
            <tr>
              <th>Description</th>
              <th>Quantité</th>
              <th>Prix Unitaire</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>${payment.description || 'Cours de langue anglaise'}</td>
              <td>${payment.hours_worked || payment.hoursWorked || '1'} h</td>
              <td>${payment.hourly_rate || payment.hourlyRate || amount} ${currency}</td>
              <td>${amount.toFixed(2)} ${currency}</td>
            </tr>
            ${bonus > 0 ? `
            <tr>
              <td>Bonus / Prime</td>
              <td>1</td>
              <td>${bonus.toFixed(2)} ${currency}</td>
              <td>${bonus.toFixed(2)} ${currency}</td>
            </tr>
            ` : ''}
          </tbody>
        </table>
        
        <table class="totals">
          <tr>
            <td>Total HT :</td>
            <td style="text-align: right;">${totalHT.toFixed(2)} ${currency}</td>
          </tr>
          <tr>
            <td>TVA (20%) :</td>
            <td style="text-align: right;">${tva.toFixed(2)} ${currency}</td>
          </tr>
          <tr class="total-row">
            <td>Total TTC :</td>
            <td style="text-align: right;">${totalTTC.toFixed(2)} ${currency}</td>
          </tr>
        </table>
        
        <div class="stamp">
          <span class="stamp-text">✓ PAYÉ</span>
        </div>
        
        <div class="footer">
          <p><strong>Conditions de paiement :</strong> Paiement à réception de facture</p>
          <p><strong>Mode de paiement :</strong> Virement bancaire / Mobile Money</p>
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

  // Handler pour prestataires
  const handleAddPrestataire = async () => {
    if (!newPrestataire.name || !newPrestataire.service || !newPrestataire.amount) {
      toast.error('Veuillez remplir tous les champs obligatoires');
      return;
    }

    try {
      await apiClient.post('/secretary/prestataire-invoices', newPrestataire);
      const res = await apiClient.get('/secretary/prestataire-invoices');
      setPrestataireInvoices(res.data || []);
      setNewPrestataire({
        name: '',
        service: '',
        amount: '',
        currency: 'EUR',
        description: '',
        notes: ''
      });
      toast.success('🏢 Facture prestataire créée !');
    } catch (error) {
      console.error('Error adding prestataire invoice:', error);
      toast.error('Erreur lors de la création');
    }
  };

  const handleDeletePrestataire = async (id) => {
    if (window.confirm('Supprimer cette facture prestataire ?')) {
      try {
        await apiClient.delete(`/secretary/prestataire-invoices/${id}`);
        setPrestataireInvoices(prestataireInvoices.filter(p => p.id !== id));
        toast.success('Facture supprimée');
      } catch (error) {
        toast.error('Erreur lors de la suppression');
      }
    }
  };

  // Messages handler
  const handleSendMessage = async () => {
    if (!newMessage.recipient || !newMessage.subject || !newMessage.content) {
      toast.error('Veuillez remplir tous les champs');
      return;
    }

    const message = {
      id: Date.now(),
      ...newMessage,
      sentAt: new Date().toISOString(),
      status: 'envoyé'
    };

    saveMessages([...messages, message]);
    setNewMessage({ recipient: '', subject: '', content: '' });
    toast.success('Message envoyé !');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    toast.success('Déconnexion réussie');
    navigate('/secretary-login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50">
      {/* Header */}
      <header className="bg-white border-b border-purple-100 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-purple-600">Espace Secrétaire</h1>
            <p className="text-sm text-gray-600">
              Bienvenue, {user?.first_name}
            </p>
          </div>
          <Button
            onClick={handleLogout}
            variant="outline"
            className="border-purple-200 hover:bg-purple-50"
          >
            <LogOut className="w-4 h-4 mr-2" />
            Déconnexion
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Tabs defaultValue="meetings" className="space-y-6">
          <TabsList className="bg-white border border-purple-100 p-1 rounded-lg">
            <TabsTrigger value="meetings" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <Calendar className="w-4 h-4 mr-2" />
              Réunions
            </TabsTrigger>
            <TabsTrigger value="notes" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Notes
            </TabsTrigger>
            <TabsTrigger value="reports" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <FileText className="w-4 h-4 mr-2" />
              Comptes Rendus
            </TabsTrigger>
            <TabsTrigger value="messages" className="data-[state=active]:bg-purple-600 data-[state=active]:text-white">
              <MessageCircle className="w-4 h-4 mr-2" />
              Messages
            </TabsTrigger>
            <TabsTrigger value="billing" className="data-[state=active]:bg-green-600 data-[state=active]:text-white">
              💰 Facturation
            </TabsTrigger>
          </TabsList>

          {/* Meetings Tab */}
          <TabsContent value="meetings" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Planifier une réunion
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre *</label>
                    <Input
                      value={newMeeting.title}
                      onChange={(e) => setNewMeeting({...newMeeting, title: e.target.value})}
                      placeholder="Ex: Réunion équipe pédagogique"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Participants</label>
                    <Input
                      value={newMeeting.attendees}
                      onChange={(e) => setNewMeeting({...newMeeting, attendees: e.target.value})}
                      placeholder="Ex: Admin, Prof1, Prof2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Date *</label>
                    <Input
                      type="date"
                      value={newMeeting.date}
                      onChange={(e) => setNewMeeting({...newMeeting, date: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Heure *</label>
                    <Input
                      type="time"
                      value={newMeeting.time}
                      onChange={(e) => setNewMeeting({...newMeeting, time: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Notes</label>
                  <Textarea
                    value={newMeeting.notes}
                    onChange={(e) => setNewMeeting({...newMeeting, notes: e.target.value})}
                    placeholder="Ordre du jour, points à discuter..."
                    rows={3}
                  />
                </div>
                <Button onClick={handleAddMeeting} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Ajouter la réunion
                </Button>
              </CardContent>
            </Card>

            {/* Meetings List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Réunions planifiées ({meetings.length})</h3>
              {meetings.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucune réunion planifiée
                  </CardContent>
                </Card>
              ) : (
                meetings.map(meeting => (
                  <Card key={meeting.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <h4 className="font-semibold text-lg mb-2">{meeting.title}</h4>
                          <div className="space-y-1 text-sm text-gray-600">
                            <p>📅 {new Date(meeting.date).toLocaleDateString('fr-FR')} à {meeting.time}</p>
                            {meeting.attendees && <p>👥 {meeting.attendees}</p>}
                            {meeting.notes && <p className="mt-2 text-gray-700">📝 {meeting.notes}</p>}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteMeeting(meeting.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Notes Tab */}
          <TabsContent value="notes" className="space-y-6">
            {!editingNote ? (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    Nouvelle note
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre *</label>
                    <Input
                      value={newNote.title}
                      onChange={(e) => setNewNote({...newNote, title: e.target.value})}
                      placeholder="Titre de la note"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Contenu *</label>
                    <Textarea
                      value={newNote.content}
                      onChange={(e) => setNewNote({...newNote, content: e.target.value})}
                      placeholder="Contenu de la note..."
                      rows={5}
                    />
                  </div>
                  <Button onClick={handleAddNote} className="bg-purple-600 hover:bg-purple-700">
                    <Plus className="w-4 h-4 mr-2" />
                    Ajouter la note
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Edit className="w-5 h-5" />
                    Modifier la note
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Titre *</label>
                    <Input
                      value={editingNote.title}
                      onChange={(e) => setEditingNote({...editingNote, title: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Contenu *</label>
                    <Textarea
                      value={editingNote.content}
                      onChange={(e) => setEditingNote({...editingNote, content: e.target.value})}
                      rows={5}
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleUpdateNote} className="bg-purple-600 hover:bg-purple-700">
                      <Save className="w-4 h-4 mr-2" />
                      Enregistrer
                    </Button>
                    <Button onClick={() => setEditingNote(null)} variant="outline">
                      <X className="w-4 h-4 mr-2" />
                      Annuler
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Notes List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Mes notes ({notes.length})</h3>
              {notes.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucune note enregistrée
                  </CardContent>
                </Card>
              ) : (
                <div className="grid md:grid-cols-2 gap-4">
                  {notes.map(note => (
                    <Card key={note.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="pt-6">
                        <div className="flex justify-between items-start mb-3">
                          <h4 className="font-semibold text-lg">{note.title}</h4>
                          <div className="flex gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setEditingNote(note)}
                              className="text-purple-600 hover:text-purple-700 hover:bg-purple-50"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteNote(note.id)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{note.content}</p>
                        <p className="text-xs text-gray-400 mt-3">
                          {new Date(note.createdAt).toLocaleDateString('fr-FR')}
                        </p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          {/* Reports Tab - Comptes Rendus des Professeurs */}
          <TabsContent value="reports" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Nouveau compte rendu
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Nom du professeur *</label>
                    <Input
                      value={newReport.profName}
                      onChange={(e) => setNewReport({...newReport, profName: e.target.value})}
                      placeholder="Ex: Marie Martin"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-2">Date du cours *</label>
                    <Input
                      type="date"
                      value={newReport.date}
                      onChange={(e) => setNewReport({...newReport, date: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Compte rendu *</label>
                  <Textarea
                    value={newReport.content}
                    onChange={(e) => setNewReport({...newReport, content: e.target.value})}
                    placeholder="Contenu du cours, présence des élèves, objectifs atteints..."
                    rows={5}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Notes supplémentaires</label>
                  <Textarea
                    value={newReport.notes}
                    onChange={(e) => setNewReport({...newReport, notes: e.target.value})}
                    placeholder="Remarques, suggestions, suivi à faire..."
                    rows={3}
                  />
                </div>
                <Button onClick={handleAddReport} className="bg-purple-600 hover:bg-purple-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Enregistrer le compte rendu
                </Button>
              </CardContent>
            </Card>

            {/* Reports List */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Comptes rendus ({profReports.length})</h3>
              {profReports.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucun compte rendu enregistré
                  </CardContent>
                </Card>
              ) : (
                profReports.map(report => (
                  <Card key={report.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="font-semibold text-lg">👨‍🏫 {report.prof_name || report.profName}</h4>
                            <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              📅 {new Date(report.date).toLocaleDateString('fr-FR')}
                            </span>
                          </div>
                          <div className="bg-purple-50 border border-purple-100 rounded-lg p-3 mb-3">
                            <p className="text-sm text-gray-700 whitespace-pre-wrap">{report.content}</p>
                          </div>
                          {report.notes && (
                            <div className="bg-gray-50 rounded-lg p-3">
                              <p className="text-xs text-gray-500 font-medium mb-1">📝 Notes :</p>
                              <p className="text-sm text-gray-600">{report.notes}</p>
                            </div>
                          )}
                          <p className="text-xs text-gray-400 mt-3">
                            Créé le {new Date(report.created_at || report.createdAt).toLocaleDateString('fr-FR')}
                          </p>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteReport(report.id)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Messages Tab */}
          <TabsContent value="messages" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageCircle className="w-5 h-5" />
                  Envoyer un message
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Destinataire *</label>
                  <Input
                    value={newMessage.recipient}
                    onChange={(e) => setNewMessage({...newMessage, recipient: e.target.value})}
                    placeholder="Email ou nom du destinataire"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Sujet *</label>
                  <Input
                    value={newMessage.subject}
                    onChange={(e) => setNewMessage({...newMessage, subject: e.target.value})}
                    placeholder="Sujet du message"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Message *</label>
                  <Textarea
                    value={newMessage.content}
                    onChange={(e) => setNewMessage({...newMessage, content: e.target.value})}
                    placeholder="Votre message..."
                    rows={5}
                  />
                </div>
                <Button onClick={handleSendMessage} className="bg-purple-600 hover:bg-purple-700">
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Envoyer le message
                </Button>
              </CardContent>
            </Card>

            {/* Messages History */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Messages envoyés ({messages.length})</h3>
              {messages.length === 0 ? (
                <Card>
                  <CardContent className="text-center py-12 text-gray-500">
                    Aucun message envoyé
                  </CardContent>
                </Card>
              ) : (
                messages.map(message => (
                  <Card key={message.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <p className="font-semibold">À: {message.recipient}</p>
                          <p className="text-sm text-gray-600 font-medium">{message.subject}</p>
                        </div>
                        <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                          {message.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 mt-3 whitespace-pre-wrap">{message.content}</p>
                      <p className="text-xs text-gray-400 mt-3">
                        {new Date(message.sentAt).toLocaleString('fr-FR')}
                      </p>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </TabsContent>

          {/* Billing Tab - Facturation */}
          <TabsContent value="billing" className="space-y-6">
            {/* Stats Cards */}
            <div className="grid md:grid-cols-3 gap-4">
              <Card className="bg-gradient-to-br from-green-500 to-emerald-600 text-white">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-green-100 text-sm">Total Payé aux Profs</p>
                    <p className="text-3xl font-bold mt-2">{billingStats.totalPaidTeachers.toLocaleString()} €</p>
                    <p className="text-green-200 text-xs mt-1">Ce mois</p>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-blue-100 text-sm">Reçus Générés</p>
                    <p className="text-3xl font-bold mt-2">{billingStats.totalReceipts.toLocaleString()} €</p>
                    <p className="text-blue-200 text-xs mt-1">{studentReceipts.length} reçus</p>
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-gradient-to-br from-orange-500 to-red-500 text-white">
                <CardContent className="pt-6">
                  <div className="text-center">
                    <p className="text-orange-100 text-sm">Paiements en Attente</p>
                    <p className="text-3xl font-bold mt-2">{billingStats.pendingPayments}</p>
                    <p className="text-orange-200 text-xs mt-1">Professeurs</p>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="grid lg:grid-cols-2 gap-6">
              {/* Teacher Payments Section */}
              <Card className="border-green-200">
                <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50">
                  <CardTitle className="flex items-center gap-2 text-green-700">
                    💰 Paiement des Professeurs
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Professeur *</label>
                      <select
                        value={newPayment.teacherName}
                        onChange={(e) => {
                          const selectedTeacher = teachers.find(t => `${t.first_name} ${t.last_name}` === e.target.value);
                          setNewPayment({
                            ...newPayment,
                            teacherName: e.target.value,
                            teacherId: selectedTeacher?.id || ''
                          });
                        }}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      >
                        <option value="">Sélectionner...</option>
                        {teachers.map(t => (
                          <option key={t.id} value={`${t.first_name} ${t.last_name}`}>
                            {t.first_name} {t.last_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Mois *</label>
                      <Input
                        type="month"
                        value={newPayment.month}
                        onChange={(e) => setNewPayment({...newPayment, month: e.target.value})}
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Montant *</label>
                      <Input
                        type="number"
                        value={newPayment.amount}
                        onChange={(e) => setNewPayment({...newPayment, amount: e.target.value})}
                        placeholder="500"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Devise</label>
                      <select
                        value={newPayment.currency}
                        onChange={(e) => setNewPayment({...newPayment, currency: e.target.value})}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm h-10"
                      >
                        <option value="EUR">🇪🇺 EUR</option>
                        <option value="FCFA">🇸🇳 FCFA</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Heures</label>
                      <Input
                        type="number"
                        value={newPayment.hoursWorked}
                        onChange={(e) => setNewPayment({...newPayment, hoursWorked: e.target.value})}
                        placeholder="20"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Bonus</label>
                      <Input
                        type="number"
                        value={newPayment.bonus}
                        onChange={(e) => setNewPayment({...newPayment, bonus: e.target.value})}
                        placeholder="0"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Notes</label>
                    <Input
                      value={newPayment.notes}
                      onChange={(e) => setNewPayment({...newPayment, notes: e.target.value})}
                      placeholder="Commentaires..."
                    />
                  </div>
                  <Button onClick={handleAddTeacherPayment} className="w-full bg-green-600 hover:bg-green-700">
                    💸 Enregistrer le Paiement
                  </Button>

                  {/* Recent Payments */}
                  <div className="mt-4 pt-4 border-t">
                    <h4 className="font-semibold text-sm mb-3">Paiements Récents</h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {teacherPayments.length === 0 ? (
                        <p className="text-gray-500 text-sm text-center py-4">Aucun paiement enregistré</p>
                      ) : (
                        teacherPayments.slice(0, 5).map(payment => (
                          <div key={payment.id} className="flex justify-between items-center p-2 bg-green-50 rounded-lg">
                            <div>
                              <p className="font-medium text-sm">{payment.teacher_name || payment.teacherName}</p>
                              <p className="text-xs text-gray-500">{payment.month}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-green-600">{payment.amount} {payment.currency || 'EUR'}</span>
                              <button onClick={() => printTeacherInvoice(payment)} className="text-purple-500 hover:text-purple-700" title="Imprimer facture">
                                📄
                              </button>
                              <button onClick={() => handleDeletePayment(payment.id)} className="text-red-500 hover:text-red-700">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Student Receipts Section */}
              <Card className="border-blue-200">
                <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50">
                  <CardTitle className="flex items-center gap-2 text-blue-700">
                    🧾 Reçus de Paiement (Élèves)
                  </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Étudiant *</label>
                      <select
                        value={newReceipt.studentName}
                        onChange={(e) => {
                          const selectedStudent = students.find(s => `${s.first_name} ${s.last_name}` === e.target.value);
                          setNewReceipt({
                            ...newReceipt,
                            studentName: e.target.value,
                            studentId: selectedStudent?.id || ''
                          });
                        }}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      >
                        <option value="">Sélectionner...</option>
                        {students.map(s => (
                          <option key={s.id} value={`${s.first_name} ${s.last_name}`}>
                            {s.first_name} {s.last_name}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Pack *</label>
                      <select
                        value={newReceipt.packType}
                        onChange={(e) => setNewReceipt({...newReceipt, packType: e.target.value})}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                      >
                        <option value="">Sélectionner...</option>
                        <option value="K-Débutant">K-Débutant</option>
                        <option value="K-Intermédiaire">K-Intermédiaire</option>
                        <option value="K-Professionnel">K-Professionnel</option>
                        <option value="K-Kids">K-Kids</option>
                        <option value="Pack Trio">Pack Trio</option>
                      </select>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Montant *</label>
                      <Input
                        type="number"
                        value={newReceipt.amount}
                        onChange={(e) => setNewReceipt({...newReceipt, amount: e.target.value})}
                        placeholder="76"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Devise</label>
                      <select
                        value={newReceipt.currency}
                        onChange={(e) => setNewReceipt({...newReceipt, currency: e.target.value})}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm h-10"
                      >
                        <option value="EUR">🇪🇺 EUR</option>
                        <option value="FCFA">🇸🇳 FCFA</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Mode paiement</label>
                      <select
                        value={newReceipt.paymentMethod}
                        onChange={(e) => setNewReceipt({...newReceipt, paymentMethod: e.target.value})}
                        className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm h-10"
                      >
                        <option value="Virement">Virement</option>
                        <option value="Carte">Carte</option>
                        <option value="Mobile Money">Mobile Money</option>
                        <option value="Espèces">Espèces</option>
                        <option value="Stripe">Stripe</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Notes</label>
                    <Input
                      value={newReceipt.notes}
                      onChange={(e) => setNewReceipt({...newReceipt, notes: e.target.value})}
                      placeholder="Détails supplémentaires..."
                    />
                  </div>
                  <Button onClick={handleAddStudentReceipt} className="w-full bg-blue-600 hover:bg-blue-700">
                    📝 Générer le Reçu
                  </Button>

                  {/* Recent Receipts */}
                  <div className="mt-4 pt-4 border-t">
                    <h4 className="font-semibold text-sm mb-3">Reçus Récents</h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {studentReceipts.length === 0 ? (
                        <p className="text-gray-500 text-sm text-center py-4">Aucun reçu généré</p>
                      ) : (
                        studentReceipts.slice(0, 5).map(receipt => (
                          <div key={receipt.id} className="flex justify-between items-center p-2 bg-blue-50 rounded-lg">
                            <div>
                              <p className="font-medium text-sm">{receipt.student_name || receipt.studentName}</p>
                              <p className="text-xs text-gray-500">{receipt.pack_type || receipt.packType}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-blue-600">{receipt.amount} {receipt.currency || 'EUR'}</span>
                              <button onClick={() => printReceipt(receipt)} className="text-purple-500 hover:text-purple-700" title="Imprimer">
                                🖨️
                              </button>
                              <button onClick={() => handleDeleteReceipt(receipt.id)} className="text-red-500 hover:text-red-700">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Prestataires Section */}
            <Card className="border-purple-200 mt-6">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-pink-50">
                <CardTitle className="flex items-center gap-2 text-purple-700">
                  🏢 Factures Prestataires / Organismes
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Formulaire */}
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium mb-1">Nom Prestataire *</label>
                        <Input
                          value={newPrestataire.name}
                          onChange={(e) => setNewPrestataire({...newPrestataire, name: e.target.value})}
                          placeholder="Ex: Organisme XYZ"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Service *</label>
                        <Input
                          value={newPrestataire.service}
                          onChange={(e) => setNewPrestataire({...newPrestataire, service: e.target.value})}
                          placeholder="Ex: Formation entreprise"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium mb-1">Montant *</label>
                        <Input
                          type="number"
                          value={newPrestataire.amount}
                          onChange={(e) => setNewPrestataire({...newPrestataire, amount: e.target.value})}
                          placeholder="1000"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Devise</label>
                        <select
                          value={newPrestataire.currency}
                          onChange={(e) => setNewPrestataire({...newPrestataire, currency: e.target.value})}
                          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm h-10"
                        >
                          <option value="EUR">🇪🇺 EUR</option>
                          <option value="FCFA">🇸🇳 FCFA</option>
                        </select>
                      </div>
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Description</label>
                      <Input
                        value={newPrestataire.description}
                        onChange={(e) => setNewPrestataire({...newPrestataire, description: e.target.value})}
                        placeholder="Description du service..."
                      />
                    </div>
                    <Button onClick={handleAddPrestataire} className="w-full bg-purple-600 hover:bg-purple-700">
                      🏢 Créer la Facture Prestataire
                    </Button>
                  </div>

                  {/* Liste des factures prestataires */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">Factures Prestataires ({prestataireInvoices.length})</h4>
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {prestataireInvoices.length === 0 ? (
                        <p className="text-gray-500 text-sm text-center py-8">Aucune facture prestataire</p>
                      ) : (
                        prestataireInvoices.map(invoice => (
                          <div key={invoice.id} className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                            <div>
                              <p className="font-medium text-sm">{invoice.name}</p>
                              <p className="text-xs text-gray-500">{invoice.service}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-bold text-purple-600">{invoice.amount} {invoice.currency || 'EUR'}</span>
                              <button onClick={() => handleDeletePrestataire(invoice.id)} className="text-red-500 hover:text-red-700">
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default SecretaryDashboard;
