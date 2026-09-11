import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import { Building2, User, Mail, Phone, FileText, Euro, Clock, ArrowLeft, LogIn, UserPlus, CheckCircle, History } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PrestatairePage = () => {
  const [mode, setMode] = useState('choice'); // choice, register, login, dashboard
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

  // Facture form
  const [factureForm, setFactureForm] = useState({
    amount: '',
    conception_time: '',
    services: '',
    description: ''
  });

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
    setLoading(true);

    try {
      await axios.post(`${API}/prestataire/facture`, {
        prestataire_code: prestataire.prestataire_code,
        amount: parseFloat(factureForm.amount),
        conception_time: factureForm.conception_time,
        services: factureForm.services || prestataire.services,
        description: factureForm.description
      });
      toast.success('Facture déposée avec succès');
      
      // Refresh factures
      const facturesRes = await axios.get(`${API}/prestataire/my-factures/${prestataire.prestataire_code}`);
      setFactures(facturesRes.data);
      
      // Reset form
      setFactureForm({ amount: '', conception_time: '', services: prestataire.services, description: '' });
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
                  <Label htmlFor="company_name">Nom de la société *</Label>
                  <Input
                    id="company_name"
                    value={registerForm.company_name}
                    onChange={(e) => setRegisterForm({ ...registerForm, company_name: e.target.value })}
                    required
                    data-testid="prestataire-company"
                  />
                </div>

                <div>
                  <Label htmlFor="services">Services concernés *</Label>
                  <Textarea
                    id="services"
                    value={registerForm.services}
                    onChange={(e) => setRegisterForm({ ...registerForm, services: e.target.value })}
                    placeholder="Ex: Design graphique, Développement web, Marketing..."
                    required
                    data-testid="prestataire-services"
                  />
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
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmitFacture} className="space-y-4">
                <div>
                  <Label htmlFor="services">Services concernés</Label>
                  <Input
                    id="services"
                    value={factureForm.services}
                    onChange={(e) => setFactureForm({ ...factureForm, services: e.target.value })}
                    placeholder={prestataire?.services}
                  />
                </div>

                <div>
                  <Label htmlFor="amount">Montant de la facture (€) *</Label>
                  <div className="relative">
                    <Euro className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      id="amount"
                      type="number"
                      step="0.01"
                      min="0"
                      value={factureForm.amount}
                      onChange={(e) => setFactureForm({ ...factureForm, amount: e.target.value })}
                      className="pl-10"
                      required
                      data-testid="facture-amount"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="conception_time">Temps de conception mensuel *</Label>
                  <div className="relative">
                    <Clock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <Input
                      id="conception_time"
                      value={factureForm.conception_time}
                      onChange={(e) => setFactureForm({ ...factureForm, conception_time: e.target.value })}
                      placeholder="Ex: 20 heures"
                      className="pl-10"
                      required
                      data-testid="facture-time"
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="description">Description (optionnel)</Label>
                  <Textarea
                    id="description"
                    value={factureForm.description}
                    onChange={(e) => setFactureForm({ ...factureForm, description: e.target.value })}
                    placeholder="Détails supplémentaires..."
                    rows={3}
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full bg-teal-600 hover:bg-teal-700"
                  disabled={loading}
                  data-testid="submit-facture-btn"
                >
                  {loading ? 'Envoi...' : 'Déposer la facture'}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Facture History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="w-5 h-5 text-teal-600" />
                Mes factures
              </CardTitle>
            </CardHeader>
            <CardContent>
              {factures.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>Aucune facture déposée</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {factures.map((facture) => {
                    const s = statusLabel(facture.status);
                    return (
                      <div key={facture.id} className="p-3 bg-gray-50 rounded-lg border">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-bold text-teal-700">{facture.amount}€</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>
                            {s.text}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{facture.services}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(facture.submitted_at).toLocaleDateString('fr-FR')} • {facture.conception_time}
                        </p>
                        {facture.status === 'paid' && facture.paid_at && (
                          <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            Payée le {new Date(facture.paid_at).toLocaleDateString('fr-FR')}
                          </p>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PrestatairePage;
