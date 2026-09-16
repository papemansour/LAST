import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from './ui/dialog';
import { Search, Building2, Mail, Phone, Clock, CheckCircle, FileText, User, Download, Filter, Edit, X, AlertTriangle, Trash2, UserCog } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../utils/api';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Services list
const SERVICES_LABELS = {
  'informatique': 'INFORMATIQUE',
  'communication': 'COMMUNICATION',
  'marketing': 'MARKETING',
  'pedagogique': 'PÉDAGOGIQUE',
  'financier': 'FINANCIER'
};

const SERVICES_LIST = [
  { value: 'all', label: 'Tous les services' },
  { value: 'informatique', label: 'INFORMATIQUE' },
  { value: 'communication', label: 'COMMUNICATION' },
  { value: 'marketing', label: 'MARKETING' },
  { value: 'pedagogique', label: 'PÉDAGOGIQUE' },
  { value: 'financier', label: 'FINANCIER' }
];

const getServiceLabel = (value) => {
  return SERVICES_LABELS[value] || value?.toUpperCase() || 'Non défini';
};

const SecretaryPrestataires = () => {
  const [searchCode, setSearchCode] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [allFactures, setAllFactures] = useState([]);
  const [allPrestataires, setAllPrestataires] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('pending');
  const [serviceFilter, setServiceFilter] = useState('all');
  
  // Edit facture modal
  const [editModal, setEditModal] = useState({ open: false, facture: null });
  const [editForm, setEditForm] = useState({ hours: '', minutes: '', amount: '', reason: '' });
  
  // Reject facture modal
  const [rejectModal, setRejectModal] = useState({ open: false, facture: null });
  const [rejectReason, setRejectReason] = useState('');
  
  // Edit prestataire modal
  const [editPrestataireModal, setEditPrestataireModal] = useState({ open: false, prestataire: null });
  const [editPrestataireForm, setEditPrestataireForm] = useState({
    first_name: '', last_name: '', email: '', phone: '', company_name: '', services: ''
  });
  
  // Delete prestataire modal
  const [deletePrestataireModal, setDeletePrestataireModal] = useState({ open: false, prestataire: null });

  useEffect(() => {
    fetchAllFactures();
    fetchAllPrestataires();
  }, []);

  const fetchAllFactures = async () => {
    try {
      const response = await apiClient.get('/secretary/prestataire-factures');
      setAllFactures(response.data);
    } catch (error) {
      console.error('Error fetching factures:', error);
    }
  };

  const fetchAllPrestataires = async () => {
    try {
      const response = await apiClient.get('/secretary/all-prestataires');
      setAllPrestataires(response.data);
    } catch (error) {
      console.error('Error fetching prestataires:', error);
    }
  };

  const handleSearch = async () => {
    if (!searchCode.trim()) {
      toast.error('Veuillez entrer un code prestataire');
      return;
    }
    
    setLoading(true);
    try {
      const response = await apiClient.get(`/secretary/prestataire/${searchCode}`);
      setSearchResult(response.data);
      toast.success('Prestataire trouvé');
    } catch (error) {
      setSearchResult(null);
      toast.error(error.response?.data?.detail || 'Prestataire non trouvé');
    } finally {
      setLoading(false);
    }
  };

  const handlePayFacture = async (factureId) => {
    try {
      await apiClient.post(`/secretary/pay-facture/${factureId}`);
      toast.success('Facture marquée comme payée');
      if (searchResult) handleSearch();
      fetchAllFactures();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors du paiement');
    }
  };

  const handleDownloadFacture = (factureId) => {
    window.open(`${BACKEND_URL}/api/prestataire/facture/${factureId}/download`, '_blank');
  };

  // Edit facture
  const openEditModal = (facture) => {
    const timeMatch = facture.conception_time?.match(/(\d+)h?\s*(\d+)?/);
    const hours = timeMatch ? timeMatch[1] : '';
    const minutes = timeMatch && timeMatch[2] ? timeMatch[2] : '0';
    
    setEditForm({
      hours: hours,
      minutes: minutes,
      amount: facture.amount.toString(),
      reason: ''
    });
    setEditModal({ open: true, facture });
  };

  const handleEditSubmit = async () => {
    const hours = parseInt(editForm.hours) || 0;
    const minutes = parseInt(editForm.minutes) || 0;
    const conceptionTime = hours > 0 && minutes > 0 ? `${hours}h${minutes}min` : hours > 0 ? `${hours}h` : `${minutes}min`;
    
    try {
      await apiClient.put(`/secretary/edit-facture/${editModal.facture.id}`, {
        amount: parseFloat(editForm.amount),
        conception_time: conceptionTime,
        modification_reason: editForm.reason || 'Correction par le secrétariat'
      });
      toast.success('Facture modifiée avec succès');
      setEditModal({ open: false, facture: null });
      fetchAllFactures();
      if (searchResult) handleSearch();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la modification');
    }
  };

  // Reject facture
  const openRejectModal = (facture) => {
    setRejectReason('');
    setRejectModal({ open: true, facture });
  };

  const handleRejectSubmit = async () => {
    if (!rejectReason.trim()) {
      toast.error('Veuillez indiquer un motif de refus');
      return;
    }
    
    try {
      await apiClient.post(`/secretary/reject-facture/${rejectModal.facture.id}`, {
        reason: rejectReason
      });
      toast.success('Facture refusée');
      setRejectModal({ open: false, facture: null });
      fetchAllFactures();
      if (searchResult) handleSearch();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors du refus');
    }
  };

  // Edit prestataire
  const openEditPrestataireModal = (prestataire) => {
    setEditPrestataireForm({
      first_name: prestataire.first_name || '',
      last_name: prestataire.last_name || '',
      email: prestataire.email || '',
      phone: prestataire.phone || '',
      company_name: prestataire.company_name || '',
      services: prestataire.services || 'informatique'
    });
    setEditPrestataireModal({ open: true, prestataire });
  };

  const handleEditPrestataireSubmit = async () => {
    try {
      await apiClient.put(`/secretary/prestataire/${editPrestataireModal.prestataire.prestataire_code}`, editPrestataireForm);
      toast.success('Prestataire modifié avec succès');
      setEditPrestataireModal({ open: false, prestataire: null });
      fetchAllPrestataires();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la modification');
    }
  };

  // Delete prestataire
  const openDeletePrestataireModal = (prestataire) => {
    setDeletePrestataireModal({ open: true, prestataire });
  };

  const handleDeletePrestataireSubmit = async () => {
    try {
      await apiClient.delete(`/secretary/prestataire/${deletePrestataireModal.prestataire.prestataire_code}`);
      toast.success('Prestataire supprimé avec succès');
      setDeletePrestataireModal({ open: false, prestataire: null });
      fetchAllPrestataires();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la suppression');
    }
  };

  // Calculate amount from hours/minutes
  const handleTimeChange = (field, value) => {
    const newForm = { ...editForm, [field]: value };
    const hours = parseFloat(newForm.hours) || 0;
    const minutes = parseFloat(newForm.minutes) || 0;
    const totalHours = hours + (minutes / 60);
    newForm.amount = (totalHours * 10).toFixed(2);
    setEditForm(newForm);
  };

  // Apply service filter
  const filterByService = (factures) => {
    if (serviceFilter === 'all') return factures;
    return factures.filter(f => f.services === serviceFilter);
  };

  const pendingFactures = filterByService(allFactures.filter(f => f.status === 'pending'));
  const paidFactures = filterByService(allFactures.filter(f => f.status === 'paid'));
  const rejectedFactures = filterByService(allFactures.filter(f => f.status === 'rejected'));

  // Facture card with teal colors (like professors)
  const FactureCard = ({ facture, showActions = true }) => {
    const isModified = facture.original_amount !== undefined;
    
    return (
      <div className={`p-4 rounded-lg border ${
        facture.status === 'paid' ? 'bg-teal-50 border-teal-200' :
        facture.status === 'rejected' ? 'bg-red-50 border-red-200' :
        'bg-amber-50 border-amber-200'
      }`}>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                facture.status === 'paid' ? 'bg-teal-100' :
                facture.status === 'rejected' ? 'bg-red-100' : 'bg-amber-100'
              }`}>
                <Building2 className={`w-5 h-5 ${
                  facture.status === 'paid' ? 'text-teal-600' :
                  facture.status === 'rejected' ? 'text-red-600' : 'text-amber-600'
                }`} />
              </div>
              <div>
                <p className="font-semibold">{facture.company_name}</p>
                <p className="text-sm text-gray-500">{facture.contact_name}</p>
              </div>
              <span className="px-2 py-0.5 bg-teal-100 text-teal-700 rounded text-xs font-medium">
                {getServiceLabel(facture.services)}
              </span>
              {isModified && (
                <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded text-xs font-medium flex items-center gap-1">
                  <Edit className="w-3 h-3" /> Modifiée
                </span>
              )}
            </div>
            <div className="mt-2 flex items-center gap-4 text-sm text-gray-600 flex-wrap">
              <span className="flex items-center gap-1">
                <Mail className="w-3 h-3" />
                {facture.email}
              </span>
              <span className="flex items-center gap-1">
                <Phone className="w-3 h-3" />
                {facture.phone}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {facture.conception_time}
              </span>
            </div>
            {facture.status === 'rejected' && facture.rejection_reason && (
              <div className="mt-2 p-2 bg-red-100 rounded text-sm text-red-700">
                <strong>Motif du refus :</strong> {facture.rejection_reason}
              </div>
            )}
            {isModified && (
              <div className="mt-2 p-2 bg-amber-100 rounded text-sm text-amber-700">
                <strong>Modification :</strong> Montant initial {facture.original_amount}€ → {facture.amount}€
                {facture.modification_reason && ` - ${facture.modification_reason}`}
              </div>
            )}
          </div>
          
          <div className="text-right flex flex-col items-end gap-2">
            <div>
              <p className={`text-2xl font-bold ${
                facture.status === 'paid' ? 'text-teal-700' :
                facture.status === 'rejected' ? 'text-red-700' : 'text-amber-700'
              }`}>{facture.amount?.toLocaleString('fr-FR')} {facture.currency === 'FCFA' ? 'FCFA' : '€'}</p>
              <p className="text-xs text-gray-500">
                {new Date(facture.submitted_at).toLocaleDateString('fr-FR')}
              </p>
              {facture.paid_at && (
                <p className="text-xs text-teal-600 flex items-center gap-1 justify-end">
                  <CheckCircle className="w-3 h-3" />
                  Payée le {new Date(facture.paid_at).toLocaleDateString('fr-FR')}
                </p>
              )}
            </div>
            
            {showActions && facture.status === 'pending' && (
              <div className="flex flex-col gap-2">
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    onClick={() => handlePayFacture(facture.id)}
                    className="bg-teal-600 hover:bg-teal-700"
                  >
                    <CheckCircle className="w-4 h-4 mr-1" />
                    Payer
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openEditModal(facture)}
                    className="border-teal-300 text-teal-700 hover:bg-teal-50"
                  >
                    <Edit className="w-4 h-4 mr-1" />
                    Modifier
                  </Button>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openRejectModal(facture)}
                    className="border-red-300 text-red-700 hover:bg-red-50"
                  >
                    <X className="w-4 h-4 mr-1" />
                    Refuser
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleDownloadFacture(facture.id)}
                    className="border-gray-300"
                  >
                    <Download className="w-4 h-4 mr-1" />
                    PDF
                  </Button>
                </div>
              </div>
            )}
            
            {facture.status !== 'pending' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleDownloadFacture(facture.id)}
                className={facture.status === 'paid' ? 'border-teal-300 text-teal-700' : 'border-red-300 text-red-700'}
              >
                <Download className="w-4 h-4 mr-1" />
                Facture
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards - Teal theme */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="border-l-4 border-l-teal-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Prestataires</p>
            <p className="text-2xl font-bold text-teal-700">{allPrestataires.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">En attente</p>
            <p className="text-2xl font-bold text-amber-700">{pendingFactures.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-teal-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Payées</p>
            <p className="text-2xl font-bold text-teal-700">{paidFactures.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-red-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Refusées</p>
            <p className="text-2xl font-bold text-red-700">{rejectedFactures.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-teal-600">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Total payé</p>
            <p className="text-2xl font-bold text-teal-700">
              {paidFactures.reduce((sum, f) => sum + f.amount, 0).toLocaleString('fr-FR')}€
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs - Teal theme */}
      <div className="flex flex-wrap gap-2 border-b pb-2">
        <Button
          variant={activeTab === 'pending' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('pending')}
          className={activeTab === 'pending' ? 'bg-amber-600' : ''}
        >
          <FileText className="w-4 h-4 mr-2" />
          En attente ({pendingFactures.length})
        </Button>
        <Button
          variant={activeTab === 'paid' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('paid')}
          className={activeTab === 'paid' ? 'bg-teal-600' : ''}
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          Payées ({paidFactures.length})
        </Button>
        <Button
          variant={activeTab === 'rejected' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('rejected')}
          className={activeTab === 'rejected' ? 'bg-red-600' : ''}
        >
          <X className="w-4 h-4 mr-2" />
          Refusées ({rejectedFactures.length})
        </Button>
        <Button
          variant={activeTab === 'all' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('all')}
          className={activeTab === 'all' ? 'bg-teal-600' : ''}
        >
          <Building2 className="w-4 h-4 mr-2" />
          Prestataires ({allPrestataires.length})
        </Button>
        <Button
          variant={activeTab === 'search' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('search')}
          className={activeTab === 'search' ? 'bg-teal-600' : ''}
        >
          <Search className="w-4 h-4 mr-2" />
          Recherche
        </Button>
        
        {/* Service Filter */}
        <div className="ml-auto flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <Select value={serviceFilter} onValueChange={setServiceFilter}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Filtrer par service" />
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
      </div>

      {/* Pending Tab */}
      {activeTab === 'pending' && (
        <Card className="border-amber-200">
          <CardHeader className="bg-gradient-to-r from-amber-50 to-orange-50">
            <CardTitle className="flex items-center gap-2 text-amber-700">
              <FileText className="w-5 h-5" />
              Factures en Attente ({pendingFactures.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {pendingFactures.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Aucune facture en attente</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingFactures.map((facture) => (
                  <FactureCard key={facture.id} facture={facture} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Paid Tab */}
      {activeTab === 'paid' && (
        <Card className="border-teal-200">
          <CardHeader className="bg-gradient-to-r from-teal-50 to-emerald-50">
            <CardTitle className="flex items-center gap-2 text-teal-700">
              <CheckCircle className="w-5 h-5" />
              Factures Payées ({paidFactures.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {paidFactures.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Aucune facture payée</p>
              </div>
            ) : (
              <div className="space-y-3">
                {paidFactures.map((facture) => (
                  <FactureCard key={facture.id} facture={facture} showActions={false} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Rejected Tab */}
      {activeTab === 'rejected' && (
        <Card className="border-red-200">
          <CardHeader className="bg-gradient-to-r from-red-50 to-pink-50">
            <CardTitle className="flex items-center gap-2 text-red-700">
              <X className="w-5 h-5" />
              Factures Refusées ({rejectedFactures.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {rejectedFactures.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Aucune facture refusée</p>
              </div>
            ) : (
              <div className="space-y-3">
                {rejectedFactures.map((facture) => (
                  <FactureCard key={facture.id} facture={facture} showActions={false} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* All Prestataires Tab with Edit/Delete */}
      {activeTab === 'all' && (
        <Card className="border-teal-200">
          <CardHeader className="bg-gradient-to-r from-teal-50 to-cyan-50">
            <CardTitle className="flex items-center gap-2 text-teal-700">
              <Building2 className="w-5 h-5" />
              Gestion des Prestataires ({allPrestataires.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            {allPrestataires.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Building2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Aucun prestataire enregistré</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {allPrestataires.map((prest) => (
                  <Card key={prest.id} className="hover:shadow-md transition-shadow border-teal-100">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="w-10 h-10 bg-teal-100 rounded-full flex items-center justify-center flex-shrink-0">
                            <Building2 className="w-5 h-5 text-teal-600" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <h3 className="font-semibold text-gray-900 truncate">{prest.company_name}</h3>
                            <p className="text-xs text-gray-500">{prest.first_name} {prest.last_name}</p>
                            <span className="inline-block px-2 py-0.5 bg-teal-100 text-teal-700 rounded text-xs font-mono mt-1">
                              {prest.prestataire_code}
                            </span>
                          </div>
                        </div>
                        <div className="flex gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditPrestataireModal(prest)}
                            className="h-8 w-8 p-0 text-teal-600 hover:text-teal-700 hover:bg-teal-50"
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openDeletePrestataireModal(prest)}
                            className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="mt-3 space-y-1 text-sm">
                        <div className="flex items-center gap-2 text-gray-600">
                          <Mail className="w-3 h-3" />
                          <span className="truncate">{prest.email}</span>
                        </div>
                        <div className="flex items-center gap-2 text-gray-600">
                          <Phone className="w-3 h-3" />
                          <span>{prest.phone}</span>
                        </div>
                      </div>
                      <div className="mt-2 p-2 bg-teal-50 rounded text-xs text-teal-700">
                        {getServiceLabel(prest.services)}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <Card className="border-teal-200">
          <CardHeader className="bg-gradient-to-r from-teal-50 to-cyan-50">
            <CardTitle className="flex items-center gap-2 text-teal-700">
              <Search className="w-5 h-5" />
              Rechercher par Code Prestataire
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-4 space-y-6">
            <div className="flex gap-3">
              <Input
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value.toUpperCase())}
                placeholder="Ex: ABC123"
                className="font-mono text-lg tracking-widest"
                maxLength={6}
              />
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="bg-teal-600 hover:bg-teal-700"
              >
                {loading ? 'Recherche...' : 'Rechercher'}
              </Button>
            </div>

            {searchResult && (
              <div className="border rounded-lg p-6 bg-teal-50">
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-lg text-teal-800 mb-4 flex items-center gap-2">
                      <Building2 className="w-5 h-5" />
                      {searchResult.prestataire.company_name}
                    </h3>
                    <div className="space-y-3">
                      <div className="flex items-center gap-2 text-sm">
                        <User className="w-4 h-4 text-gray-500" />
                        <span>{searchResult.prestataire.first_name} {searchResult.prestataire.last_name}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Mail className="w-4 h-4 text-gray-500" />
                        <span>{searchResult.prestataire.email}</span>
                      </div>
                      <div className="flex items-center gap-2 text-sm">
                        <Phone className="w-4 h-4 text-gray-500" />
                        <span>{searchResult.prestataire.phone}</span>
                      </div>
                      <div className="p-2 bg-teal-100 rounded text-sm">
                        <strong>Services:</strong> {getServiceLabel(searchResult.prestataire.services)}
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm mb-3">Factures en attente ({searchResult.pending_factures.length})</h4>
                    {searchResult.pending_factures.length === 0 ? (
                      <p className="text-gray-500 text-sm">Aucune facture en attente</p>
                    ) : (
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {searchResult.pending_factures.map((facture) => (
                          <FactureCard key={facture.id} facture={facture} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Edit Facture Modal */}
      <Dialog open={editModal.open} onOpenChange={(open) => setEditModal({ open, facture: editModal.facture })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5 text-teal-600" />
              Modifier la facture
            </DialogTitle>
            <DialogDescription>
              Corrigez les heures de travail et le montant si nécessaire.
            </DialogDescription>
          </DialogHeader>
          
          {editModal.facture && (
            <div className="space-y-4">
              <div className="p-3 bg-teal-50 rounded-lg">
                <p className="font-semibold">{editModal.facture.company_name}</p>
                <p className="text-sm text-gray-500">Montant initial : {editModal.facture.amount}€</p>
              </div>
              
              <div>
                <Label>Temps de conception</Label>
                <div className="grid grid-cols-2 gap-3 mt-2">
                  <div className="relative">
                    <Input
                      type="number"
                      min="0"
                      value={editForm.hours}
                      onChange={(e) => handleTimeChange('hours', e.target.value)}
                      placeholder="0"
                      className="pr-14"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">heures</span>
                  </div>
                  <div className="relative">
                    <Input
                      type="number"
                      min="0"
                      max="59"
                      value={editForm.minutes}
                      onChange={(e) => handleTimeChange('minutes', e.target.value)}
                      placeholder="0"
                      className="pr-8"
                    />
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">min</span>
                  </div>
                </div>
              </div>
              
              <div>
                <Label>Montant corrigé (€)</Label>
                <Input
                  type="number"
                  step="0.01"
                  value={editForm.amount}
                  onChange={(e) => setEditForm({ ...editForm, amount: e.target.value })}
                  className="mt-2"
                />
              </div>
              
              <div>
                <Label>Motif de la modification</Label>
                <Textarea
                  value={editForm.reason}
                  onChange={(e) => setEditForm({ ...editForm, reason: e.target.value })}
                  placeholder="Ex: Correction du nombre d'heures réelles..."
                  className="mt-2"
                  rows={2}
                />
              </div>
            </div>
          )}
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setEditModal({ open: false, facture: null })}>
              Annuler
            </Button>
            <Button onClick={handleEditSubmit} className="bg-teal-600 hover:bg-teal-700">
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reject Facture Modal */}
      <Dialog open={rejectModal.open} onOpenChange={(open) => setRejectModal({ open, facture: rejectModal.facture })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Refuser la facture
            </DialogTitle>
            <DialogDescription>
              Cette action est irréversible. Le prestataire sera notifié par email.
            </DialogDescription>
          </DialogHeader>
          
          {rejectModal.facture && (
            <div className="space-y-4">
              <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                <p className="font-semibold">{rejectModal.facture.company_name}</p>
                <p className="text-sm text-gray-500">Montant : {rejectModal.facture.amount}€</p>
              </div>
              
              <div>
                <Label className="text-red-700">Motif du refus *</Label>
                <Textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Ex: Les heures déclarées ne correspondent pas au travail effectué..."
                  className="mt-2 border-red-200 focus:border-red-400"
                  rows={3}
                />
              </div>
            </div>
          )}
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setRejectModal({ open: false, facture: null })}>
              Annuler
            </Button>
            <Button onClick={handleRejectSubmit} className="bg-red-600 hover:bg-red-700">
              Confirmer le refus
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Prestataire Modal */}
      <Dialog open={editPrestataireModal.open} onOpenChange={(open) => setEditPrestataireModal({ open, prestataire: editPrestataireModal.prestataire })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserCog className="w-5 h-5 text-teal-600" />
              Modifier le prestataire
            </DialogTitle>
            <DialogDescription>
              Modifiez les informations du prestataire.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Prénom</Label>
                <Input
                  value={editPrestataireForm.first_name}
                  onChange={(e) => setEditPrestataireForm({ ...editPrestataireForm, first_name: e.target.value })}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Nom</Label>
                <Input
                  value={editPrestataireForm.last_name}
                  onChange={(e) => setEditPrestataireForm({ ...editPrestataireForm, last_name: e.target.value })}
                  className="mt-1"
                />
              </div>
            </div>
            
            <div>
              <Label>Société</Label>
              <Input
                value={editPrestataireForm.company_name}
                onChange={(e) => setEditPrestataireForm({ ...editPrestataireForm, company_name: e.target.value })}
                className="mt-1"
              />
            </div>
            
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={editPrestataireForm.email}
                onChange={(e) => setEditPrestataireForm({ ...editPrestataireForm, email: e.target.value })}
                className="mt-1"
              />
            </div>
            
            <div>
              <Label>Téléphone</Label>
              <Input
                value={editPrestataireForm.phone}
                onChange={(e) => setEditPrestataireForm({ ...editPrestataireForm, phone: e.target.value })}
                className="mt-1"
              />
            </div>
            
            <div>
              <Label>Service</Label>
              <Select value={editPrestataireForm.services} onValueChange={(v) => setEditPrestataireForm({ ...editPrestataireForm, services: v })}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SERVICES_LIST.filter(s => s.value !== 'all').map((service) => (
                    <SelectItem key={service.value} value={service.value}>
                      {service.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setEditPrestataireModal({ open: false, prestataire: null })}>
              Annuler
            </Button>
            <Button onClick={handleEditPrestataireSubmit} className="bg-teal-600 hover:bg-teal-700">
              Enregistrer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Prestataire Modal */}
      <Dialog open={deletePrestataireModal.open} onOpenChange={(open) => setDeletePrestataireModal({ open, prestataire: deletePrestataireModal.prestataire })}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Supprimer le prestataire
            </DialogTitle>
            <DialogDescription>
              Cette action est irréversible. Toutes les factures associées seront également supprimées.
            </DialogDescription>
          </DialogHeader>
          
          {deletePrestataireModal.prestataire && (
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
              <p className="font-semibold">{deletePrestataireModal.prestataire.company_name}</p>
              <p className="text-sm text-gray-600">{deletePrestataireModal.prestataire.first_name} {deletePrestataireModal.prestataire.last_name}</p>
              <p className="text-xs text-gray-500 font-mono mt-1">{deletePrestataireModal.prestataire.prestataire_code}</p>
            </div>
          )}
          
          <DialogFooter className="gap-2">
            <Button variant="outline" onClick={() => setDeletePrestataireModal({ open: false, prestataire: null })}>
              Annuler
            </Button>
            <Button onClick={handleDeletePrestataireSubmit} className="bg-red-600 hover:bg-red-700">
              Supprimer définitivement
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SecretaryPrestataires;
