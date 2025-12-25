import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { getFileUrl } from '../utils/fileUrl';
import { Search, Volume2, BookOpen, LogOut, Brain, Download } from 'lucide-react';

const Kalamatheque = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [books, setBooks] = useState([]);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLevel, setSelectedLevel] = useState(null);
  const [dictionaryWord, setDictionaryWord] = useState('');
  const [aiAssistantOpen, setAiAssistantOpen] = useState(false);

  useEffect(() => {
    // Check access
    const access = localStorage.getItem('kalamatheque_access');
    if (access !== 'granted') {
      navigate('/kalamatheque-access');
      return;
    }
    
    fetchUser();
    fetchBooks();
  }, []);

  const fetchUser = async () => {
    try {
      const res = await apiClient.get('/auth/me');
      setUser(res.data);
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const fetchBooks = async (level = null) => {
    try {
      const url = level ? `/kalamatheque/books?level=${level}` : '/kalamatheque/books';
      const res = await apiClient.get(url);
      setBooks(res.data);
      setFilteredBooks(res.data);
    } catch (error) {
      toast.error('Erreur de chargement des livres');
    }
  };

  const handleSearch = (query) => {
    setSearchQuery(query);
    if (!query) {
      setFilteredBooks(books);
      return;
    }
    
    const filtered = books.filter(book => 
      book.title.toLowerCase().includes(query.toLowerCase()) ||
      book.author.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredBooks(filtered);
  };

  const handleLevelSelect = (level) => {
    setSelectedLevel(level);
    fetchBooks(level);
  };

  const handleListenWord = async () => {
    if (!dictionaryWord.trim()) {
      toast.error('Veuillez entrer un mot');
      return;
    }

    try {
      const res = await apiClient.post('/kalamatheque/text-to-speech', {
        text: dictionaryWord
      });
      
      // Play audio from base64
      const audio = new Audio(`data:audio/mp3;base64,${res.data.audio_base64}`);
      audio.play();
      toast.success('Prononciation en cours...');
    } catch (error) {
      toast.error('Erreur de prononciation');
    }
  };

  const handleDictionarySearch = () => {
    if (!dictionaryWord.trim()) {
      toast.error('Veuillez entrer un mot');
      return;
    }
    
    const url = `https://www.wordreference.com/enfr/${encodeURIComponent(dictionaryWord)}`;
    window.open(url, '_blank');
  };

  const handleExit = () => {
    localStorage.removeItem('kalamatheque_access');
    navigate(-1);
  };

  const handleOpenBook = (book) => {
    navigate(`/kalamatheque/reader/${book.id}`);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-blue-50 p-6">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-800">KALAMATHÈQUE</h1>
              <p className="text-gray-600">Explorez notre collection de ressources pédagogiques</p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => setAiAssistantOpen(!aiAssistantOpen)}
                className="bg-purple-600 hover:bg-purple-700"
              >
                <Brain className="mr-2 h-4 w-4" />
                IA Assistant
              </Button>
              <Button
                onClick={() => {
                  localStorage.removeItem('kalamatheque_access');
                  if (user?.role === 'student') {
                    window.location.href = '/student';
                  } else if (user?.role === 'teacher') {
                    window.location.href = '/teacher';
                  } else if (user?.role === 'admin') {
                    window.location.href = '/admin';
                  } else {
                    window.location.href = '/';
                  }
                }}
                variant="outline"
                className="border-blue-500 text-blue-600 hover:bg-blue-50"
              >
                ← Retour au dashboard
              </Button>
              <Button
                onClick={() => {
                  localStorage.removeItem('kalamatheque_access');
                  window.location.href = '/';
                }}
                variant="outline"
                className="border-red-500 text-red-500 hover:bg-red-50"
              >
                Quitter
                <LogOut className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <Input
              type="text"
              placeholder="Rechercher un document..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
              className="pl-10 text-lg"
            />
          </div>
        </div>

        {/* Dictionary Section */}
        <Card className="mb-6 border-blue-200">
          <CardHeader className="bg-blue-50">
            <CardTitle className="flex items-center gap-2">
              📖 Dictionnaire en ligne
              <span className="text-sm font-normal text-gray-600">Propulsé par WordReference</span>
            </CardTitle>
            <CardDescription>Recherchez la traduction et la définition des mots</CardDescription>
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex gap-2">
              <Input
                type="text"
                placeholder="Entrez un mot en anglais..."
                value={dictionaryWord}
                onChange={(e) => setDictionaryWord(e.target.value)}
                className="flex-1"
              />
              <Button onClick={handleListenWord} variant="outline">
                <Volume2 className="mr-2 h-4 w-4" />
                Écouter
              </Button>
              <Button onClick={handleDictionarySearch} className="bg-blue-600 hover:bg-blue-700">
                <Search className="mr-2 h-4 w-4" />
                Rechercher
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* AI Assistant Modal */}
        {aiAssistantOpen && (
          <Card className="mb-6 border-purple-200">
            <CardHeader className="bg-purple-50">
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Assistant IA
              </CardTitle>
              <CardDescription>
                Sélectionnez du texte dans un document pour l'analyser avec l'IA
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid grid-cols-3 gap-4">
                <Button className="bg-purple-600 hover:bg-purple-700" disabled>
                  <BookOpen className="mr-2 h-4 w-4" />
                  Résumer
                </Button>
                <Button className="bg-purple-600 hover:bg-purple-700" disabled>
                  <Brain className="mr-2 h-4 w-4" />
                  Expliquer
                </Button>
                <Button className="bg-purple-600 hover:bg-purple-700" disabled>
                  📝 Exemples
                </Button>
              </div>
              <p className="text-sm text-gray-500 mt-4 text-center">
                Ouvrez un livre pour utiliser l'Assistant IA
              </p>
            </CardContent>
          </Card>
        )}

        {/* Level Selection */}
        {!selectedLevel ? (
          <div>
            <div className="text-center mb-6">
              <BookOpen className="mx-auto h-12 w-12 text-teal-600 mb-2" />
              <p className="text-gray-600">Sélectionnez un niveau pour voir les documents disponibles</p>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              <Card 
                className="cursor-pointer hover:shadow-lg transition border-green-200"
                onClick={() => handleLevelSelect('beginner')}
              >
                <CardHeader className="bg-green-50">
                  <CardTitle className="text-green-700">Beginner</CardTitle>
                  <CardDescription>Niveau débutant</CardDescription>
                </CardHeader>
              </Card>
              <Card 
                className="cursor-pointer hover:shadow-lg transition border-yellow-200"
                onClick={() => handleLevelSelect('intermediate')}
              >
                <CardHeader className="bg-yellow-50">
                  <CardTitle className="text-yellow-700">Intermediate</CardTitle>
                  <CardDescription>Niveau intermédiaire</CardDescription>
                </CardHeader>
              </Card>
              <Card 
                className="cursor-pointer hover:shadow-lg transition border-red-200"
                onClick={() => handleLevelSelect('advanced')}
              >
                <CardHeader className="bg-red-50">
                  <CardTitle className="text-red-700">Pack professionnel</CardTitle>
                  <CardDescription>Niveau professionnel</CardDescription>
                </CardHeader>
              </Card>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-800 capitalize">
                {selectedLevel} - {filteredBooks.length} livre(s)
              </h2>
              <Button onClick={() => setSelectedLevel(null)} variant="outline">
                ← Retour aux niveaux
              </Button>
            </div>

            {filteredBooks.length === 0 ? (
              <p className="text-center text-gray-500 py-12">Aucun livre disponible pour ce niveau</p>
            ) : (
              <div className="grid md:grid-cols-3 lg:grid-cols-4 gap-6">
                {filteredBooks.map((book) => (
                  <Card 
                    key={book.id} 
                    className="hover:shadow-xl transition"
                  >
                    <CardHeader className="cursor-pointer" onClick={() => handleOpenBook(book)}>
                      {book.cover_image && (
                        <img 
                          src={book.cover_image} 
                          alt={book.title}
                          className="w-full h-48 object-cover rounded-md mb-3"
                        />
                      )}
                      <CardTitle className="text-lg">{book.title}</CardTitle>
                      <CardDescription>
                        {book.author && <span className="block">Par {book.author}</span>}
                        <span className="text-xs text-gray-400">{book.file_type.toUpperCase()}</span>
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-gray-600 line-clamp-3 mb-4">{book.description}</p>
                      <div className="flex gap-2">
                        <Button 
                          onClick={() => handleOpenBook(book)}
                          className="flex-1 bg-teal-600 hover:bg-teal-700"
                          size="sm"
                        >
                          👁️ Ouvrir
                        </Button>
                        <a 
                          href={getFileUrl(book.file_url)} 
                          download={book.title}
                          onClick={(e) => e.stopPropagation()}
                          className="flex-1"
                        >
                          <Button 
                            variant="outline"
                            className="w-full"
                            size="sm"
                          >
                            ⬇️ Télécharger
                          </Button>
                        </a>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Kalamatheque;