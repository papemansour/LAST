import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { useAuth } from '../hooks/useAuth';
import { Lock, Key } from 'lucide-react';

const SecretaryLogin = () => {
  const navigate = useNavigate();
  const { checkAuth } = useAuth();
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!code) {
      toast.error('Veuillez entrer le code d\'acces');
      return;
    }

    setLoading(true);

    try {
      const response = await apiClient.post('/auth/secretary-login', { code });
      
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // Update auth context before navigating
      await checkAuth();
      
      toast.success('Acces secretaire autorise !');
      navigate('/secretary');
    } catch (error) {
      console.error('Login error:', error);
      toast.error(error.response?.data?.detail || 'Code incorrect');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-pink-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 bg-purple-600 rounded-full mb-4">
            <Lock className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Espace Secretaire
          </h1>
          <p className="text-gray-600">
            Acces reserve avec code secret
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8 border border-purple-100">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Code d&apos;acces
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-purple-400" />
                <Input
                  type="password"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="Entrez le code secret"
                  className="pl-10 border-purple-200 focus:border-purple-500 focus:ring-purple-500"
                  disabled={loading}
                  data-testid="secretary-code-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-6 text-lg font-semibold"
              data-testid="secretary-login-submit"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Verification...
                </span>
              ) : (
                'Acceder'
              )}
            </Button>
          </form>
        </div>

        <div className="text-center mt-6">
          <button
            onClick={() => navigate('/')}
            className="text-purple-600 hover:text-purple-700 text-sm font-medium"
          >
            Retour a l&apos;accueil
          </button>
        </div>
      </div>
    </div>
  );
};

export default SecretaryLogin;
