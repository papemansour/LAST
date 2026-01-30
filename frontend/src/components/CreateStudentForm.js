import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { toast } from 'sonner';
import { UserPlus, Copy, Eye, EyeOff } from 'lucide-react';
import apiClient from '../utils/api';

const CreateStudentForm = ({ onStudentCreated }) => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [createdStudent, setCreatedStudent] = useState(null);
  
  const [formData, setFormData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    phone_country_code: '+221',
    level: 'beginner',
    price: '',
    currency: 'EUR',
    password: ''
  });

  const resetForm = () => {
    setFormData({
      first_name: '',
      last_name: '',
      email: '',
      phone: '',
      phone_country_code: '+221',
      level: 'beginner',
      price: '',
      currency: 'EUR',
      password: ''
    });
    setCreatedStudent(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.first_name || !formData.last_name || !formData.email) {
      toast.error('Veuillez remplir les champs obligatoires');
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post('/admin/create-student', {
        ...formData,
        price: parseFloat(formData.price) || 0
      });
      
      setCreatedStudent(response.data);
      toast.success('✅ Étudiant créé avec succès!');
      
      if (onStudentCreated) {
        onStudentCreated(response.data.student);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, label) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copié!`);
  };

  const getLevelLabel = (level) => {
    const labels = {
      'beginner': 'Débutant',
      'intermediate': 'Intermédiaire',
      'advanced': 'Professionnel',
      'kkid': 'K-Kid'
    };
    return labels[level] || level;
  };

  return (
    <Dialog open={open} onOpenChange={(isOpen) => {
      setOpen(isOpen);
      if (!isOpen) resetForm();
    }}>
      <DialogTrigger asChild>
        <Button className="bg-teal-600 hover:bg-teal-700">
          <UserPlus className="w-4 h-4 mr-2" />
          Créer un Étudiant
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-teal-600" />
            {createdStudent ? 'Étudiant Créé!' : 'Créer un Nouvel Étudiant'}
          </DialogTitle>
        </DialogHeader>

        {createdStudent ? (
          // Affichage des informations après création
          <div className="space-y-4 mt-4">
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4">
                <div className="text-center mb-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                    <span className="text-3xl">✅</span>
                  </div>
                  <h3 className="font-bold text-lg text-green-800">
                    {createdStudent.student.first_name} {createdStudent.student.last_name}
                  </h3>
                  <p className="text-sm text-green-600">Compte créé avec succès</p>
                </div>

                <div className="space-y-3 bg-white p-4 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Email:</span>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{createdStudent.student.email}</span>
                      <button 
                        onClick={() => copyToClipboard(createdStudent.student.email, 'Email')}
                        className="text-teal-600 hover:text-teal-800"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Mot de passe:</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono bg-gray-100 px-2 py-1 rounded">
                        {createdStudent.temporary_password}
                      </span>
                      <button 
                        onClick={() => copyToClipboard(createdStudent.temporary_password, 'Mot de passe')}
                        className="text-teal-600 hover:text-teal-800"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Code Digika:</span>
                    <div className="flex items-center gap-2">
                      <span className="font-mono bg-purple-100 text-purple-700 px-2 py-1 rounded">
                        {createdStudent.digika_code}
                      </span>
                      <button 
                        onClick={() => copyToClipboard(createdStudent.digika_code, 'Code Digika')}
                        className="text-teal-600 hover:text-teal-800"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Téléphone:</span>
                    <span className="font-medium">{createdStudent.student.phone}</span>
                  </div>
                  
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Niveau:</span>
                    <span className="font-medium">{getLevelLabel(createdStudent.student.level)}</span>
                  </div>
                  
                  {createdStudent.student.price > 0 && (
                    <div className="flex justify-between items-center">
                      <span className="text-gray-600">Prix:</span>
                      <span className="font-medium text-green-600">
                        {createdStudent.student.price} {createdStudent.student.currency}
                      </span>
                    </div>
                  )}
                </div>

                <div className="mt-4 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    <strong>💡 Conseil:</strong> Envoyez ces informations à l'étudiant pour qu'il puisse se connecter.
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => {
                resetForm();
              }}>
                Créer un autre
              </Button>
              <Button onClick={() => setOpen(false)} className="bg-teal-600 hover:bg-teal-700">
                Fermer
              </Button>
            </div>
          </div>
        ) : (
          // Formulaire de création
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="first_name">Prénom *</Label>
                <Input
                  id="first_name"
                  value={formData.first_name}
                  onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                  placeholder="Jean"
                  required
                />
              </div>
              <div>
                <Label htmlFor="last_name">Nom *</Label>
                <Input
                  id="last_name"
                  value={formData.last_name}
                  onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                  placeholder="Dupont"
                  required
                />
              </div>
            </div>

            <div>
              <Label htmlFor="email">Email *</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="jean.dupont@gmail.com"
                required
              />
            </div>

            <div>
              <Label>Téléphone</Label>
              <div className="flex gap-2">
                <Select
                  value={formData.phone_country_code}
                  onValueChange={(value) => setFormData({...formData, phone_country_code: value})}
                >
                  <SelectTrigger className="w-[130px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="+221">🇸🇳 +221</SelectItem>
                    <SelectItem value="+33">🇫🇷 +33</SelectItem>
                    <SelectItem value="+225">🇨🇮 +225</SelectItem>
                    <SelectItem value="+223">🇲🇱 +223</SelectItem>
                    <SelectItem value="+237">🇨🇲 +237</SelectItem>
                    <SelectItem value="+1">🇺🇸 +1</SelectItem>
                    <SelectItem value="+44">🇬🇧 +44</SelectItem>
                    <SelectItem value="+32">🇧🇪 +32</SelectItem>
                    <SelectItem value="+41">🇨🇭 +41</SelectItem>
                    <SelectItem value="+212">🇲🇦 +212</SelectItem>
                    <SelectItem value="+216">🇹🇳 +216</SelectItem>
                    <SelectItem value="+213">🇩🇿 +213</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData({...formData, phone: e.target.value})}
                  placeholder="77 123 45 67"
                  className="flex-1"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Niveau</Label>
                <Select
                  value={formData.level}
                  onValueChange={(value) => setFormData({...formData, level: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="beginner">🟢 Débutant</SelectItem>
                    <SelectItem value="intermediate">🟡 Intermédiaire</SelectItem>
                    <SelectItem value="advanced">🔴 Professionnel</SelectItem>
                    <SelectItem value="kkid">🧒 K-Kid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Mot de passe provisoire</Label>
                <div className="relative">
                  <Input
                    type={showPassword ? "text" : "password"}
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    placeholder="Auto-généré si vide"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Prix</Label>
                <Input
                  type="number"
                  value={formData.price}
                  onChange={(e) => setFormData({...formData, price: e.target.value})}
                  placeholder="0"
                />
              </div>
              <div>
                <Label>Devise</Label>
                <Select
                  value={formData.currency}
                  onValueChange={(value) => setFormData({...formData, currency: value})}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="EUR">💶 Euro (EUR)</SelectItem>
                    <SelectItem value="FCFA">🌍 Franc CFA (FCFA)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex gap-2 justify-end pt-4">
              <Button type="button" variant="outline" onClick={() => setOpen(false)}>
                Annuler
              </Button>
              <Button type="submit" disabled={loading} className="bg-teal-600 hover:bg-teal-700">
                {loading ? 'Création...' : 'Créer l\'Étudiant'}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default CreateStudentForm;
