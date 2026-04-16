import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Printer, Download, Wallet, Calendar, Receipt } from 'lucide-react';

const StudentPayments = () => {
  const [receipts, setReceipts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchReceipts();
  }, []);

  const fetchReceipts = async () => {
    try {
      const response = await apiClient.get('/student/my-receipts');
      setReceipts(response.data);
    } catch (error) {
      console.error('Error fetching receipts:', error);
      toast.error('Erreur lors du chargement des reçus');
    } finally {
      setLoading(false);
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
          body { font-family: 'Segoe UI', Arial, sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; color: #333; }
          .header { display: flex; justify-content: space-between; border-bottom: 3px solid #0d9488; padding-bottom: 20px; margin-bottom: 30px; }
          .logo { font-size: 24px; font-weight: bold; color: #0d9488; }
          .logo span { color: #f59e0b; }
          .subtitle { font-size: 12px; color: #666; margin-top: 5px; }
          .receipt-number { text-align: right; }
          .receipt-number h2 { font-size: 14px; color: #666; margin: 0; }
          .receipt-number p { font-size: 18px; font-weight: bold; color: #0d9488; margin: 5px 0 0; }
          .details { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-bottom: 30px; }
          .section h3 { font-size: 12px; text-transform: uppercase; color: #999; margin-bottom: 10px; letter-spacing: 1px; }
          .section p { margin: 5px 0; font-size: 14px; }
          .amount-box { background: #f0fdfa; border: 2px solid #0d9488; border-radius: 12px; padding: 20px; text-align: center; margin: 30px 0; }
          .amount-box .label { font-size: 14px; color: #666; margin-bottom: 5px; }
          .amount-box .amount { font-size: 36px; font-weight: bold; color: #0d9488; }
          .footer { border-top: 1px solid #eee; padding-top: 20px; margin-top: 30px; text-align: center; font-size: 12px; color: #999; }
          @media print { body { padding: 20px; } }
        </style>
      </head>
      <body>
        <div class="header">
          <div>
            <div class="logo">My<span>KALAMA</span>English</div>
            <div class="subtitle">Plateforme d'apprentissage de l'anglais</div>
          </div>
          <div class="receipt-number">
            <h2>REÇU DE PAIEMENT</h2>
            <p>REC-${new Date(receipt.created_at).getFullYear()}-${receipt.id?.slice(0, 6).toUpperCase() || 'XXXX'}</p>
          </div>
        </div>
        <div class="details">
          <div class="section">
            <h3>Informations de l'etudiant</h3>
            <p><strong>${receipt.student_name || 'N/A'}</strong></p>
            <p>${receipt.email || ''}</p>
          </div>
          <div class="section">
            <h3>Details du paiement</h3>
            <p><strong>Date :</strong> ${new Date(receipt.created_at).toLocaleDateString('fr-FR')}</p>
            <p><strong>Pack :</strong> ${receipt.pack_name || receipt.pack_type || 'N/A'}</p>
            <p><strong>Mode de paiement :</strong> ${receipt.payment_method || 'N/A'}</p>
            ${receipt.notes ? `<p><strong>Notes :</strong> ${receipt.notes}</p>` : ''}
          </div>
        </div>
        <div class="amount-box">
          <div class="label">Montant Paye</div>
          <div class="amount">${receipt.amount} ${receipt.currency || 'EUR'}</div>
        </div>
        <div class="footer">
          <p>MyKalama English - mykalamaenglish@gmail.com</p>
          <p>Ce document est un reçu de paiement officiel.</p>
        </div>
      </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  const totalEUR = receipts
    .filter(r => (r.currency || 'EUR') === 'EUR')
    .reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0);
  const totalFCFA = receipts
    .filter(r => r.currency === 'FCFA')
    .reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0);
  const hasEUR = receipts.some(r => (r.currency || 'EUR') === 'EUR');
  const hasFCFA = receipts.some(r => r.currency === 'FCFA');

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="student-payments-loading">
        <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="student-payments-container">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {hasEUR && (
          <Card className="bg-gradient-to-br from-teal-50 to-emerald-100 border-teal-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-teal-500 rounded-xl">
                  <Wallet className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-teal-700">Total Paye (EUR)</p>
                  <p className="text-2xl font-bold text-teal-800" data-testid="total-eur">{totalEUR.toFixed(2)} EUR</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        {hasFCFA && (
          <Card className="bg-gradient-to-br from-teal-50 to-emerald-100 border-teal-200">
            <CardContent className="p-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-teal-500 rounded-xl">
                  <Wallet className="w-6 h-6 text-white" />
                </div>
                <div>
                  <p className="text-sm text-teal-700">Total Paye (FCFA)</p>
                  <p className="text-2xl font-bold text-teal-800" data-testid="total-fcfa">{totalFCFA.toLocaleString()} FCFA</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 border-blue-200">
          <CardContent className="p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500 rounded-xl">
                <Receipt className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-blue-700">Total Recus</p>
                <p className="text-2xl font-bold text-blue-800" data-testid="total-receipts">{receipts.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Receipts List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2" data-testid="receipts-title">
            <Receipt className="w-5 h-5 text-teal-600" />
            Mes Recus de Paiement
          </CardTitle>
        </CardHeader>
        <CardContent>
          {receipts.length === 0 ? (
            <div className="text-center py-12" data-testid="no-receipts-message">
              <Receipt className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Aucun recu de paiement</h3>
              <p className="text-gray-500">Vos recus apparaitront ici une fois generes par le secretariat.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {receipts.map((receipt) => (
                <Card key={receipt.id} className="hover:shadow-lg transition-shadow border-l-4 border-l-teal-500" data-testid={`receipt-${receipt.id}`}>
                  <CardContent className="p-4">
                    <div className="flex flex-wrap items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Calendar className="w-4 h-4 text-gray-500" />
                          <span className="font-semibold text-lg">{receipt.pack_name || receipt.pack_type || 'Paiement'}</span>
                        </div>
                        {receipt.payment_method && (
                          <p className="text-sm text-gray-600">Mode : {receipt.payment_method}</p>
                        )}
                        {receipt.notes && (
                          <p className="text-sm text-gray-500">{receipt.notes}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">
                          Le {new Date(receipt.created_at).toLocaleDateString('fr-FR', {day: 'numeric', month: 'long', year: 'numeric'})}
                        </p>
                      </div>
                      
                      <div className="text-right">
                        <p className="text-xs text-teal-600 font-medium">MONTANT</p>
                        <p className="text-xl font-bold text-teal-700">{receipt.amount} {receipt.currency || 'EUR'}</p>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => printReceipt(receipt)}
                          className="hover:bg-teal-50"
                          data-testid={`print-receipt-${receipt.id}`}
                        >
                          <Printer className="w-4 h-4 mr-1" />
                          Imprimer
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            printReceipt(receipt);
                            toast.success('Utilisez Ctrl+P puis "Enregistrer en PDF"');
                          }}
                          className="hover:bg-blue-50"
                          data-testid={`pdf-receipt-${receipt.id}`}
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

export default StudentPayments;
