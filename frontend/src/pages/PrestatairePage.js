import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Building2, User, Mail, Phone, FileText, Euro, Clock, ArrowLeft, LogIn, UserPlus, CheckCircle, History, Calculator, Download } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Services list
const SERVICES_LIST = [
  { value: 'informatique', label: 'INFORMATIQUE' },
  { value: 'communication', label: 'COMMUNICATION' },
  { value: 'marketing', label: 'MARKETING' },
  { value: 'pedagogique', label: 'PÉDAGOGIQUE' },
  { value: 'financier', label: 'FINANCIER' }
];

// Rate: 10€ per hour
const HOURLY_RATE = 10;

const PrestatairePage = () => {
  const [searchParams] = useSearchParams();
  const initialMode = searchParams.get('mode') || 'choice';
  const [mode, setMode] = useState(initialMode); // choice, register, login, dashboard
  const [loading, setLoading] = useState(false);
  const [prestataire, setPrestataire] = useState(null);
  const [factures, setFactures] = useState([]);

  // Registration form
  const [registerForm, setRegisterForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company_name: '',
    services: ''
  });

  // Login form
  const [accessCode, setAccessCode] = useState('');

  // Facture form with attestation
  const [factureForm, setFactureForm] = useState({
    hours: '',
    minutes: '',
    services: '',
    // Attestation fields
    attestation_name: '',
    attestation_location: 'Paris',
    attestation_date_start: '',
    attestation_date_end: '',
    attestation_signature_location: '',
    attestation_signature_date: new Date().toLocaleDateString('fr-FR')
  });

  // Calculate amount automatically based on time
  const calculateAmount = () => {
    const hours = parseFloat(factureForm.hours) || 0;
    const minutes = parseFloat(factureForm.minutes) || 0;
    const totalHours = hours + (minutes / 60);
    return (totalHours * HOURLY_RATE).toFixed(2);
  };

  const getConceptionTime = () => {
    const hours = parseInt(factureForm.hours) || 0;
    const minutes = parseInt(factureForm.minutes) || 0;
    if (hours > 0 && minutes > 0) {
      return `${hours}h${minutes}min`;
    } else if (hours > 0) {
      return `${hours}h`;
    } else if (minutes > 0) {
      return `${minutes}min`;
    }
    return '';
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/prestataire/register`, registerForm);
      toast.success(response.data.message);
      toast.info(`Votre code prestataire: ${response.data.prestataire_code}`, { duration: 10000 });
      if (response.data.access_code) {
        toast.success(`Code d'accès: ${response.data.access_code}`, { duration: 15000 });
        setAccessCode(response.data.access_code);
      }
      setMode('login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de l\'inscription');
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/prestataire/login`, { access_code: accessCode });
      setPrestataire(response.data.prestataire);
      toast.success('Connexion réussie');
      
      // Fetch factures
      const facturesRes = await axios.get(`${API}/prestataire/my-factures/${response.data.prestataire.prestataire_code}`);
      setFactures(facturesRes.data);
      
      setFactureForm(prev => ({ ...prev, services: response.data.prestataire.services }));
      setMode('dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Code d\'accès invalide');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitFacture = async (e) => {
    e.preventDefault();
    
    const amount = parseFloat(calculateAmount());
    const conceptionTime = getConceptionTime();
    
    if (amount <= 0) {
      toast.error('Veuillez indiquer le temps de conception');
      return;
    }
    
    if (!factureForm.services) {
      toast.error('Veuillez sélectionner un service');
      return;
    }
    
    setLoading(true);

    // Build attestation text
    const attestationText = `Je soussigné(e), ${factureForm.attestation_name}, prestataire de services ${getServiceLabel(factureForm.services)}, atteste sur l'honneur avoir effectué un total de ${conceptionTime} heures de travail pour la société MyKalama, située à ${factureForm.attestation_location}, durant la période du ${factureForm.attestation_date_start} au ${factureForm.attestation_date_end}. Je certifie que ces heures ont été réalisées conformément aux termes de notre contrat et aux exigences de la société. Fait à ${factureForm.attestation_signature_location}, le ${factureForm.attestation_signature_date}. Signature: ${factureForm.attestation_name}`;

    try {
      await axios.post(`${API}/prestataire/facture`, {
        prestataire_code: prestataire.prestataire_code,
        amount: amount,
        conception_time: conceptionTime,
        services: factureForm.services,
        description: attestationText,
        attestation: {
          name: factureForm.attestation_name,
          location: factureForm.attestation_location,
          date_start: factureForm.attestation_date_start,
          date_end: factureForm.attestation_date_end,
          signature_location: factureForm.attestation_signature_location,
          signature_date: factureForm.attestation_signature_date
        }
      });
      toast.success('Facture déposée avec succès ! Elle est maintenant en attente de validation.');
      
      // Refresh factures
      const facturesRes = await axios.get(`${API}/prestataire/my-factures/${prestataire.prestataire_code}`);
      setFactures(facturesRes.data);
      
      // Reset form
      setFactureForm({
        hours: '', minutes: '', services: '',
        attestation_name: '',
        attestation_location: 'Paris',
        attestation_date_start: '',
        attestation_date_end: '',
        attestation_signature_location: '',
        attestation_signature_date: new Date().toLocaleDateString('fr-FR')
      });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors du dépôt');
    } finally {
      setLoading(false);
    }
  };

  const statusLabel = (status) => {
    switch (status) {
      case 'pending': return { text: 'En attente', cls: 'bg-yellow-100 text-yellow-800' };
      case 'paid': return { text: 'Payée', cls: 'bg-green-100 text-green-800' };
      case 'rejected': return { text: 'Refusée', cls: 'bg-red-100 text-red-800' };
      default: return { text: status, cls: 'bg-gray-100 text-gray-800' };
    }
  };

  const getServiceLabel = (value) => {
    const service = SERVICES_LIST.find(s => s.value === value);
    return service ? service.label : value?.toUpperCase() || 'Non défini';
  };

  const handleDownloadFacture = (factureId) => {
    window.open(`${API}/prestataire/facture/${factureId}/download`, '_blank');
  };

  // Choice screen
  if (mode === 'choice') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <Link to="/" className="inline-flex items-center text-teal-600 hover:text-teal-700 mb-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Retour au site
            </Link>
            <h1 className="text-3xl font-bold text-gray-900">Espace Prestataire</h1>
            <p className="text-gray-600 mt-2">Gérez vos factures facilement</p>
          </div>

          <div className="space-y-4">
            <Button
              onClick={() => setMode('login')}
              className="w-full py-6 text-lg bg-teal-600 hover:bg-teal-700"
              data-testid="prestataire-login-btn"
            >
              <LogIn className="w-5 h-5 mr-2" />
              Se connecter
            </Button>

            <Button
              onClick={() => setMode('register')}
              variant="outline"
              className="w-full py-6 text-lg border-teal-300 text-teal-700 hover:bg-teal-50"
              data-testid="prestataire-register-btn"
            >
              <UserPlus className="w-5 h-5 mr-2" />
              Créer un compte
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // Registration form
  if (mode === 'register') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 py-12 px-4">
        <div className="max-w-lg mx-auto">
          <Button
            variant="ghost"
            onClick={() => setMode('choice')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>

          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Building2 className="w-8 h-8 text-teal-600" />
              </div>
              <CardTitle className="text-2xl">Inscription Prestataire</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="first_name">Prénom *</Label>
                    <Input
                      id="first_name"
                      value={registerForm.first_name}
                      onChange={(e) => setRegisterForm({ ...registerForm, first_name: e.target.value })}
                      required
                      data-testid="prestataire-firstname"
                    />
                  </div>
                  <div>
                    <Label htmlFor="last_name">Nom *</Label>
                    <Input
                      id="last_name"
                      value={registerForm.last_name}
                      onChange={(e) => setRegisterForm({ ...registerForm, last_name: e.target.value })}
                      required
                      data-testid="prestataire-lastname"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="email">Adresse e-mail *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={registerForm.email}
                    onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                    required
                    data-testid="prestataire-email"
                  />
                </div>

                <div>
                  <Label htmlFor="phone">Numéro de téléphone *</Label>
                  <Input
                    id="phone"
                    type="tel"
                    value={registerForm.phone}
                    onChange={(e) => setRegisterForm({ ...registerForm, phone: e.target.value })}
                    required
                    data-testid="prestataire-phone"
                  />
                </div>

                <div>
                  <Label htmlFor="company_name">Nom de la société</Label>
                  <Input
                    id="company_name"
                    value={registerForm.company_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, company_name: e.target.value })}
                    placeholder="Optionnel"
                    data-testid="prestataire-company"
                  />
                </div>

                <div>
                  <Label htmlFor="services">Services concernés *</Label>
                  <Select
                    value={registerForm.services}
                    onValueChange={(value) => setRegisterForm({ ...registerForm, services: value })}
                  >
                    <SelectTrigger data-testid="prestataire-services">
                      <SelectValue placeholder="Sélectionner un service" />
                    </SelectTrigger>
                    <SelectContent>
                      {SERVICES_LIST.map((service) => (
                        <SelectItem key={service.value} value={service.value}>
                          {service.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-teal-600 hover:bg-teal-700"
                  disabled={loading}
                  data-testid="prestataire-submit-register"
                >
                  {loading ? 'Inscription...' : 'Valider l\'inscription'}
                </Button>
              </form>

              <p className="text-center text-sm text-gray-500 mt-4">
                Un code d&apos;accès vous sera envoyé par email.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Login form
  if (mode === 'login') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md">
          <Button
            variant="ghost"
            onClick={() => setMode('choice')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Retour
          </Button>

          <Card className="shadow-xl">
            <CardHeader className="text-center">
              <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <LogIn className="w-8 h-8 text-teal-600" />
              </div>
              <CardTitle className="text-2xl">Connexion Prestataire</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleLogin} className="space-y-4">
                <div>
                  <Label htmlFor="access_code">Code d&apos;accès</Label>
                  <Input
                    id="access_code"
                    value={accessCode}
                    onChange={(e) => setAccessCode(e.target.value.toUpperCase())}
                    placeholder="XXXXXXXX"
                    className="text-center text-xl tracking-widest font-mono"
                    maxLength={8}
                    required
                    data-testid="prestataire-access-code"
                  />
                  <p className="text-xs text-gray-500 mt-1">Le code reçu par email</p>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-teal-600 hover:bg-teal-700"
                  disabled={loading}
                  data-testid="prestataire-submit-login"
                >
                  {loading ? 'Connexion...' : 'Se connecter'}
                </Button>
              </form>

              <div className="mt-6 pt-6 border-t text-center">
                <p className="text-sm text-gray-500">
                  Pas encore de compte ?{' '}
                  <button
                    onClick={() => setMode('register')}
                    className="text-teal-600 hover:underline font-medium"
                  >
                    S&apos;inscrire
                  </button>
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  // Dashboard
  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Espace Prestataire</h1>
            <p className="text-gray-600">Bienvenue, {prestataire?.company_name}</p>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              setPrestataire(null);
              setMode('choice');
            }}
          >
            Déconnexion
          </Button>
        </div>

        {/* Info Card */}
        <Card className="mb-6 bg-teal-50 border-teal-200">
          <CardContent className="p-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-teal-600" />
                <span>{prestataire?.first_name} {prestataire?.last_name}</span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-teal-600" />
                <span className="truncate">{prestataire?.email}</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-teal-600" />
                <span>{prestataire?.phone}</span>
              </div>
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-teal-600" />
                <span className="font-mono text-teal-700">{prestataire?.prestataire_code}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Deposit Facture */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-teal-600" />
                Déposer une facture
              </CardTitle>
              <p className="text-sm text-gray-500">Tarif: 10€ / heure</p>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmitFacture} className="space-y-4">
                <div>
                  <Label>Service concerné *</Label>
                  <Select
                    value={factureForm.services}
                    onValueChange={(value) => setFactureForm({ ...factureForm, services: value })}
                  >
                    <SelectTrigger data-testid="facture-services">
                      <SelectValue placeholder="Sélectionner un service" />
                    </SelectTrigger>
                    <SelectContent>
                      {SERVICES_LIST.map((service) => (
                        <SelectItem key={service.value} value={service.value}>
                          {service.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <Label>Temps de conception *</Label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="relative">
                        <Input
                          type="number"
                          min="0"
                          max="999"
                          value={factureForm.hours}
                          onChange={(e) => setFactureForm({ ...factureForm, hours: e.target.value })}
                          placeholder="0"
                          className="pr-12"
                          data-testid="facture-hours"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">heures</span>
                      </div>
                    </div>
                    <div>
                      <div className="relative">
                        <Input
                          type="number"
                          min="0"
                          max="59"
                          value={factureForm.minutes}
                          onChange={(e) => setFactureForm({ ...factureForm, minutes: e.target.value })}
                          placeholder="0"
                          className="pr-8"
                          data-testid="facture-minutes"
                        />
                        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">min</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Auto-calculated amount display */}
                <div className="p-4 bg-teal-50 rounded-lg border border-teal-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Calculator className="w-5 h-5 text-teal-600" />
                      <span className="text-sm font-medium text-teal-700">Montant calculé</span>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-teal-700">{calculateAmount()}€</p>
                      <p className="text-xs text-teal-600">{getConceptionTime() || '0h'} × 10€/h</p>
                    </div>
                  </div>
                </div>

                {/* Attestation sur l'honneur */}
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-4">
                  <h4 className="font-semibold text-gray-800 text-sm">Attestation sur l&apos;honneur</h4>
                  
                  <div className="text-sm text-gray-700 leading-relaxed">
                    <p>
                      Je soussigné(e), <Input
                        value={factureForm.attestation_name}
                        onChange={(e) => setFactureForm({ ...factureForm, attestation_name: e.target.value })}
                        placeholder="Votre Nom et Prénom"
                        className="inline-block w-48 h-8 mx-1 text-sm"
                        required
                      />, prestataire de services <Select
                        value={factureForm.services}
                        onValueChange={(value) => setFactureForm({ ...factureForm, services: value })}
                      >
                        <SelectTrigger className="inline-flex w-40 h-8 mx-1 text-sm">
                          <SelectValue placeholder="Service" />
                        </SelectTrigger>
                        <SelectContent>
                          {SERVICES_LIST.map((service) => (
                            <SelectItem key={service.value} value={service.value}>
                              {service.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>, atteste sur l&apos;honneur avoir effectué un total de <strong className="text-teal-700">{getConceptionTime() || '___'}</strong> heures de travail pour la société <strong>MyKalama</strong>, située à <Input
                        value={factureForm.attestation_location}
                        onChange={(e) => setFactureForm({ ...factureForm, attestation_location: e.target.value })}
                        placeholder="Ville"
                        className="inline-block w-28 h-8 mx-1 text-sm"
                      />, durant la période du <Input
                        type="date"
                        value={factureForm.attestation_date_start}
                        onChange={(e) => setFactureForm({ ...factureForm, attestation_date_start: e.target.value })}
                        className="inline-block w-36 h-8 mx-1 text-sm"
                        required
                      /> au <Input
                        type="date"
                        value={factureForm.attestation_date_end}
                        onChange={(e) => setFactureForm({ ...factureForm, attestation_date_end: e.target.value })}
                        className="inline-block w-36 h-8 mx-1 text-sm"
                        required
                      />.
                    </p>
                    
                    <p className="mt-3">
                      Je certifie que ces heures ont été réalisées conformément aux termes de notre contrat et aux exigences de la société.
                    </p>
                    
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <p>
                        Fait à <Input
                          value={factureForm.attestation_signature_location}
                          onChange={(e) => setFactureForm({ ...factureForm, attestation_signature_location: e.target.value })}
                          placeholder="Ville"
                          className="inline-block w-28 h-8 mx-1 text-sm"
                          required
                        />, le <Input
                          value={factureForm.attestation_signature_date}
                          onChange={(e) => setFactureForm({ ...factureForm, attestation_signature_date: e.target.value })}
                          placeholder="Date"
                          className="inline-block w-28 h-8 mx-1 text-sm"
                          required
                        />.
                      </p>
                      
                      <div className="mt-3">
                        <Label className="text-xs text-gray-500">Signature (Nom complet)</Label>
                        <div className="mt-1 p-3 bg-white border-2 border-dashed border-gray-300 rounded text-center">
                          <p className="font-signature text-xl text-gray-800 italic">
                            {factureForm.attestation_name || 'Votre signature'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-teal-600 hover:bg-teal-700"
                  disabled={loading || parseFloat(calculateAmount()) <= 0 || !factureForm.attestation_name || !factureForm.attestation_date_start || !factureForm.attestation_date_end}
                  data-testid="submit-facture-btn"
                >
                  {loading ? 'Envoi...' : 'Déposer la facture'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Factures Section - Like Teachers */}
          <div className="space-y-4">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 gap-3">
              <Card className="border-l-4 border-l-yellow-500">
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500">En attente</p>
                  <p className="text-2xl font-bold text-yellow-700">
                    {factures.filter(f => f.status === 'pending').length}
                  </p>
                  <p className="text-xs text-gray-400">
                    {factures.filter(f => f.status === 'pending').reduce((sum, f) => sum + f.amount, 0).toFixed(2)}€
                  </p>
                </CardContent>
              </Card>
              <Card className="border-l-4 border-l-green-500">
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500">Payées</p>
                  <p className="text-2xl font-bold text-green-700">
                    {factures.filter(f => f.status === 'paid').length}
                  </p>
                  <p className="text-xs text-gray-400">
                    {factures.filter(f => f.status === 'paid').reduce((sum, f) => sum + f.amount, 0).toFixed(2)}€
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Pending Factures */}
            <Card className="border-yellow-200">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-yellow-700">
                  <Clock className="w-5 h-5" />
                  Factures en attente de paiement
                </CardTitle>
              </CardHeader>
              <CardContent>
                {factures.filter(f => f.status === 'pending').length === 0 ? (
                  <div className="text-center py-6 text-gray-400">
                    <CheckCircle className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Aucune facture en attente</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {factures.filter(f => f.status === 'pending').map((facture) => (
                      <div key={facture.id} className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-bold text-lg text-yellow-700">{facture.amount}€</p>
                            <p className="text-sm text-gray-600">{getServiceLabel(facture.services)}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              Déposée le {new Date(facture.submitted_at).toLocaleDateString('fr-FR')} • {facture.conception_time}
                            </p>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                              En attente
                            </span>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadFacture(facture.id)}
                              className="text-xs"
                            >
                              <Download className="w-3 h-3 mr-1" />
                              Télécharger
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Paid Factures */}
            <Card className="border-green-200">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-green-700">
                  <CheckCircle className="w-5 h-5" />
                  Factures payées
                </CardTitle>
              </CardHeader>
              <CardContent>
                {factures.filter(f => f.status === 'paid').length === 0 ? (
                  <div className="text-center py-6 text-gray-400">
                    <FileText className="w-10 h-10 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Aucune facture payée</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {factures.filter(f => f.status === 'paid').map((facture) => (
                      <div key={facture.id} className="p-4 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-bold text-lg text-green-700">{facture.amount}€</p>
                            <p className="text-sm text-gray-600">{getServiceLabel(facture.services)}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              Déposée le {new Date(facture.submitted_at).toLocaleDateString('fr-FR')} • {facture.conception_time}
                            </p>
                            {facture.paid_at && (
                              <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
                                <CheckCircle className="w-3 h-3" />
                                Payée le {new Date(facture.paid_at).toLocaleDateString('fr-FR')}
                              </p>
                            )}
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                              Payée
                            </span>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadFacture(facture.id)}
                              className="text-xs border-green-300 text-green-700"
                            >
                              <Download className="w-3 h-3 mr-1" />
                              Télécharger
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PrestatairePage;
