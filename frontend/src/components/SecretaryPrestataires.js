import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Search, Building2, Mail, Phone, Euro, Clock, CheckCircle, FileText, User } from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../utils/api';

// Services list labels
const SERVICES_LABELS = {
  'informatique': 'INFORMATIQUE',
  'communication': 'COMMUNICATION',
  'marketing': 'MARKETING',
  'pedagogique': 'PÉDAGOGIQUE',
  'financier': 'FINANCIER'
};

const getServiceLabel = (value) => {
  return SERVICES_LABELS[value] || value?.toUpperCase() || 'Non défini';
};

const SecretaryPrestataires = () => {
  const [searchCode, setSearchCode] = useState('');
  const [searchResult, setSearchResult] = useState(null);
  const [allFactures, setAllFactures] = useState([]);
  const [allPrestataires, setAllPrestataires] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('search'); // search, pending, all

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
      // Refresh data
      if (searchResult) {
        handleSearch();
      }
      fetchAllFactures();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors du paiement');
    }
  };

  const pendingFactures = allFactures.filter(f => f.status === 'pending');
  const paidFactures = allFactures.filter(f => f.status === 'paid');

  const statusLabel = (status) => {
    switch (status) {
      case 'pending': return { text: 'En attente', cls: 'bg-yellow-100 text-yellow-800' };
      case 'paid': return { text: 'Payée', cls: 'bg-green-100 text-green-800' };
      default: return { text: status, cls: 'bg-gray-100 text-gray-800' };
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Prestataires</p>
            <p className="text-2xl font-bold text-purple-700">{allPrestataires.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-yellow-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Factures en attente</p>
            <p className="text-2xl font-bold text-yellow-700">{pendingFactures.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Factures payées</p>
            <p className="text-2xl font-bold text-green-700">{paidFactures.length}</p>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <p className="text-sm text-gray-500">Total payé</p>
            <p className="text-2xl font-bold text-blue-700">
              {paidFactures.reduce((sum, f) => sum + f.amount, 0).toLocaleString('fr-FR')}€
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b pb-2">
        <Button
          variant={activeTab === 'search' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('search')}
          className={activeTab === 'search' ? 'bg-purple-600' : ''}
        >
          <Search className="w-4 h-4 mr-2" />
          Recherche par code
        </Button>
        <Button
          variant={activeTab === 'pending' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('pending')}
          className={activeTab === 'pending' ? 'bg-yellow-600' : ''}
        >
          <FileText className="w-4 h-4 mr-2" />
          En attente ({pendingFactures.length})
        </Button>
        <Button
          variant={activeTab === 'all' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('all')}
          className={activeTab === 'all' ? 'bg-green-600' : ''}
        >
          <Building2 className="w-4 h-4 mr-2" />
          Tous les prestataires
        </Button>
      </div>

      {/* Search Tab */}
      {activeTab === 'search' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5 text-purple-600" />
              Rechercher par Code Prestataire
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex gap-3">
              <Input
                value={searchCode}
                onChange={(e) => setSearchCode(e.target.value.toUpperCase())}
                placeholder="Ex: ABC123"
                className="font-mono text-lg tracking-widest"
                maxLength={6}
                data-testid="search-prestataire-code"
              />
              <Button
                onClick={handleSearch}
                disabled={loading}
                className="bg-purple-600 hover:bg-purple-700"
                data-testid="search-prestataire-btn"
              >
                {loading ? 'Recherche...' : 'Rechercher'}
              </Button>
            </div>

            {searchResult && (
              <div className="border rounded-lg p-6 bg-purple-50">
                <div className="grid md:grid-cols-2 gap-6">
                  {/* Prestataire Info */}
                  <div>
                    <h3 className="font-semibold text-lg text-purple-800 mb-4 flex items-center gap-2">
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
                      <div className="p-2 bg-purple-100 rounded text-sm">
                        <strong>Services:</strong> {searchResult.prestataire.services}
                      </div>
                    </div>
                  </div>

                  {/* Pending Factures */}
                  <div>
                    <h4 className="font-semibold text-sm mb-3">Factures en attente ({searchResult.pending_factures.length})</h4>
                    {searchResult.pending_factures.length === 0 ? (
                      <p className="text-gray-500 text-sm">Aucune facture en attente</p>
                    ) : (
                      <div className="space-y-2 max-h-60 overflow-y-auto">
                        {searchResult.pending_factures.map((facture) => (
                          <div key={facture.id} className="p-3 bg-white rounded-lg border">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-bold text-purple-700 flex items-center gap-1">
                                <Euro className="w-4 h-4" />
                                {facture.amount}€
                              </span>
                              <span className="text-xs text-gray-500 flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                {facture.conception_time}
                              </span>
                            </div>
                            <p className="text-xs text-gray-500 mb-2">
                              {new Date(facture.submitted_at).toLocaleDateString('fr-FR')}
                            </p>
                            <Button
                              size="sm"
                              onClick={() => handlePayFacture(facture.id)}
                              className="w-full bg-green-600 hover:bg-green-700"
                              data-testid={`pay-facture-${facture.id}`}
                            >
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Valider le paiement
                            </Button>
                          </div>
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

      {/* Pending Tab */}
      {activeTab === 'pending' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-yellow-600" />
              Factures en Attente de Paiement
            </CardTitle>
          </CardHeader>
          <CardContent>
            {pendingFactures.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Aucune facture en attente</p>
              </div>
            ) : (
              <div className="space-y-3">
                {pendingFactures.map((facture) => (
                  <div key={facture.id} className="p-4 bg-yellow-50 rounded-lg border border-yellow-200 flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-semibold">{facture.company_name}</p>
                          <p className="text-sm text-gray-500">{facture.contact_name}</p>
                        </div>
                      </div>
                      <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
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
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-purple-700">{facture.amount}€</p>
                      <p className="text-xs text-gray-500 mb-2">
                        {new Date(facture.submitted_at).toLocaleDateString('fr-FR')}
                      </p>
                      <Button
                        size="sm"
                        onClick={() => handlePayFacture(facture.id)}
                        className="bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Payer
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* All Prestataires Tab */}
      {activeTab === 'all' && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-5 h-5 text-purple-600" />
              Tous les Prestataires ({allPrestataires.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {allPrestataires.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Building2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Aucun prestataire enregistré</p>
              </div>
            ) : (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {allPrestataires.map((prest) => (
                  <Card key={prest.id} className="hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 bg-purple-100 rounded-full flex items-center justify-center">
                          <Building2 className="w-5 h-5 text-purple-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 truncate">{prest.company_name}</h3>
                          <p className="text-xs text-gray-500">{prest.first_name} {prest.last_name}</p>
                          <span className="inline-block px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-mono mt-1">
                            {prest.prestataire_code}
                          </span>
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
                      <div className="mt-2 p-2 bg-gray-50 rounded text-xs text-gray-600">
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
    </div>
  );
};

export default SecretaryPrestataires;
