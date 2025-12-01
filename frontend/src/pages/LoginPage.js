import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { toast } from 'sonner';
import axios from 'axios';
import { ArrowLeft } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LoginPage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  
  // Check date for seasonal messages
  const currentDate = new Date();
  const isChristmas = currentDate <= new Date('2025-12-26');
  const isNewYear = currentDate >= new Date('2025-12-27') && currentDate <= new Date('2026-01-10');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      toast.success('Connexion réussie!');
      
      // Redirect based on role and level
      const role = response.data.user.role;
      const level = response.data.user.level;
      
      if (role === 'admin') {
        navigate('/admin');
      } else if (role === 'teacher') {
        navigate('/teacher');
      } else if (role === 'student') {
        // K-Kid students get special kid dashboard
        if (level === 'kkid') {
          navigate('/kid-dashboard');
        } else {
          navigate('/student');
        }
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`min-h-screen flex items-center justify-center px-4 relative overflow-hidden ${
      isChristmas ? 'bg-gradient-to-br from-red-50 via-green-50 to-red-100' : 
      isNewYear ? 'bg-gradient-to-br from-yellow-50 via-orange-50 to-pink-100' :
      'bg-gradient-to-br from-blue-50 via-white to-purple-50'
    }`}>
      {/* Christmas decorations */}
      {isChristmas && (
        <>
          <div className="absolute top-0 left-0 w-full h-20 bg-gradient-to-b from-green-700 to-transparent opacity-30"></div>
          <div className="absolute top-5 left-10 text-6xl animate-bounce">🎄</div>
          <div className="absolute top-5 right-10 text-6xl animate-bounce" style={{ animationDelay: '0.5s' }}>🎅</div>
          <div className="absolute bottom-10 left-20 text-4xl animate-pulse">⛄</div>
          <div className="absolute bottom-10 right-20 text-4xl animate-pulse" style={{ animationDelay: '1s' }}>🎁</div>
          <div className="absolute top-1/4 left-1/4 text-3xl animate-spin" style={{ animationDuration: '3s' }}>❄️</div>
          <div className="absolute top-1/3 right-1/4 text-3xl animate-spin" style={{ animationDuration: '4s', animationDelay: '1s' }}>⭐</div>
          <div className="absolute top-1/2 left-10 text-2xl opacity-50">🔔</div>
          <div className="absolute top-2/3 right-10 text-2xl opacity-50">🕯️</div>
        </>
      )}
      
      {/* New Year decorations */}
      {isNewYear && (
        <>
          <div className="absolute top-10 left-10 text-6xl animate-bounce">🎊</div>
          <div className="absolute top-10 right-10 text-6xl animate-bounce" style={{ animationDelay: '0.5s' }}>🎉</div>
          <div className="absolute bottom-20 left-20 text-5xl animate-pulse">🥳</div>
          <div className="absolute bottom-20 right-20 text-5xl animate-pulse" style={{ animationDelay: '0.5s' }}>🎆</div>
          <div className="absolute top-1/3 left-1/4 text-4xl animate-bounce" style={{ animationDelay: '1s' }}>✨</div>
          <div className="absolute top-1/2 right-1/4 text-4xl animate-bounce" style={{ animationDelay: '1.5s' }}>🎈</div>
        </>
      )}
      
      <div className="w-full max-w-md relative z-10">
        <Link to="/" className="inline-flex items-center text-blue-600 hover:text-blue-700 mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Retour à l'accueil
        </Link>
        
        {/* Seasonal message banner */}
        {isChristmas && (
          <div className="mb-6 p-4 bg-red-600 text-white rounded-lg shadow-lg text-center animate-pulse">
            <p className="text-lg font-bold">🎄 Joyeux Noël ! 🎅</p>
            <p className="text-sm mt-1">Offre valable jusqu'au 26 décembre 2025</p>
          </div>
        )}
        
        {isNewYear && (
          <div className="mb-6 p-4 bg-gradient-to-r from-yellow-500 to-orange-500 text-white rounded-lg shadow-lg text-center animate-pulse">
            <p className="text-xl font-bold">🎉 MyKalamaEnglish vous souhaite une bonne année 2026 ! 🎊</p>
            <p className="text-sm mt-1">Que cette nouvelle année vous apporte succès et réussite</p>
          </div>
        )}
        
        <Card className="shadow-2xl">
          <CardHeader className="text-center">
            <CardTitle className="text-3xl">Connexion</CardTitle>
            <CardDescription>Accédez à votre espace KALAMAENGLISH</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  data-testid="login-email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre@email.com"
                />
              </div>

              <div>
                <Label htmlFor="password">Mot de passe</Label>
                <Input
                  id="password"
                  type="password"
                  data-testid="login-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                />
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={loading}
                data-testid="login-submit-button"
              >
                {loading ? 'Connexion...' : 'Se connecter'}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Pas encore de compte ?{' '}
                <Link to="/?openRegister=true#pricing" className="text-green-600 hover:text-green-700 font-bold">
                  Inscrivez-vous
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LoginPage;
