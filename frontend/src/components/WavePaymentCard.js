import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Copy, CheckCircle, Phone, User, Banknote } from 'lucide-react';
import { toast } from 'sonner';

const WavePaymentCard = ({ packName, price }) => {
  const waveNumber = '+221 774946561';
  const recipientName = 'Mouhamadou Mansour Diagne';

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copié !');
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <Card className="max-w-2xl w-full border-4 border-orange-500 shadow-2xl animate-in fade-in slide-in-from-bottom-4">
        <CardHeader className="bg-gradient-to-r from-orange-500 to-red-500 text-white">
          <div className="flex items-center justify-center gap-3 mb-2">
            <Banknote className="w-8 h-8" />
            <CardTitle className="text-2xl md:text-3xl">Finaliser votre paiement</CardTitle>
          </div>
          <p className="text-center text-orange-100">Instructions de paiement Wave Sénégal</p>
        </CardHeader>
        <CardContent className="p-6 md:p-8 space-y-6">
          {/* Pack Info */}
          <div className="bg-teal-50 rounded-xl p-4 border-2 border-teal-200">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-600">Vous avez choisi</p>
                <p className="text-xl font-bold text-teal-800">{packName}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Montant</p>
                <p className="text-3xl font-bold text-orange-600">{price.toLocaleString()} FCFA</p>
              </div>
            </div>
          </div>

          {/* Payment Instructions */}
          <div className="space-y-4">
            <div className="bg-white rounded-xl border-2 border-orange-200 p-6">
              <h3 className="font-bold text-lg mb-4 flex items-center gap-2 text-orange-600">
                <CheckCircle className="w-6 h-6" />
                Payez votre pack par WAVE
              </h3>
              
              {/* Phone Number */}
              <div className="bg-orange-50 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center">
                      <Phone className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Numéro Wave</p>
                      <p className="text-2xl font-bold text-orange-600">{waveNumber}</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(waveNumber)}
                    className="border-orange-500 text-orange-600 hover:bg-orange-50"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Recipient Name */}
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center">
                      <User className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Nom du bénéficiaire</p>
                      <p className="text-xl font-bold text-blue-600">{recipientName}</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(recipientName)}
                    className="border-blue-500 text-blue-600 hover:bg-blue-50"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Amount */}
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
                      <Banknote className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Montant à envoyer</p>
                      <p className="text-2xl font-bold text-green-600">{price.toLocaleString()} FCFA</p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => copyToClipboard(price.toString())}
                    className="border-green-500 text-green-600 hover:bg-green-50"
                  >
                    <Copy className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-r-lg">
              <h4 className="font-bold text-yellow-800 mb-2">📱 Étapes de paiement :</h4>
              <ol className="space-y-2 text-sm text-yellow-900">
                <li>1️⃣ Ouvrez votre application Wave</li>
                <li>2️⃣ Sélectionnez "Envoyer de l'argent"</li>
                <li>3️⃣ Entrez le numéro : <strong>{waveNumber}</strong></li>
                <li>4️⃣ Vérifiez le nom : <strong>{recipientName}</strong></li>
                <li>5️⃣ Entrez le montant : <strong>13 500 FCFA pour pack K-Débutant, 22 500 FCFA pour pack K-Intermédiaire et 36 000 FCFA pour pack K-Professionnel</strong></li>
              </ol>
            </div>

            <div className="bg-teal-50 border border-teal-200 p-4 rounded-lg">
              <p className="text-sm text-teal-800">
                <strong>⚠️ Important :</strong> Après avoir effectué le paiement, votre inscription sera validée par notre équipe dans les 24h. Vous recevrez un email de confirmation avec vos identifiants.
              </p>
            </div>
          </div>

          {/* Close Button */}
          <Button
            onClick={() => window.location.href = '/'}
            className="w-full bg-teal-600 hover:bg-teal-700 text-lg py-6"
          >
            J'ai compris, retour à l'accueil
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default WavePaymentCard;
