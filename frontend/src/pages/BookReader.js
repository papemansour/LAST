import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { getFileUrl } from '../utils/fileUrl';
import { ArrowLeft, Search, Volume2, Brain, BookOpen } from 'lucide-react';

const BookReader = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [selectedText, setSelectedText] = useState('');
  const [aiResult, setAiResult] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [searchWord, setSearchWord] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBook();
  }, [id]);

  const fetchBook = async () => {
    try {
      const res = await apiClient.get(`/kalamatheque/books/${id}`);
      setBook(res.data);
    } catch (error) {
      toast.error('Livre non trouvé');
      navigate('/kalamatheque');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    if (text) {
      setSelectedText(text);
      toast.success(`Texte sélectionné: "${text.substring(0, 50)}..."`);
    }
  };

  const handleAiAction = async (action) => {
    if (!selectedText) {
      toast.error('Veuillez sélectionner du texte d\'abord');
      return;
    }

    setAiLoading(true);
    setAiResult('');

    try {
      const res = await apiClient.post('/kalamatheque/ai-assistant', {
        action: action,
        text: selectedText
      });
      setAiResult(res.data.result);
    } catch (error) {
      toast.error('Erreur de l\'assistant IA');
    } finally {
      setAiLoading(false);
    }
  };

  const handleListenWord = async () => {
    if (!searchWord.trim()) {
      toast.error('Veuillez entrer un mot');
      return;
    }

    try {
      const res = await apiClient.post('/kalamatheque/text-to-speech', {
        text: searchWord
      });
      
      const audio = new Audio(`data:audio/mp3;base64,${res.data.audio_base64}`);
      audio.play();
      toast.success('Prononciation en cours...');
    } catch (error) {
      toast.error('Erreur de prononciation');
    }
  };

  const handleSearchInDictionary = () => {
    if (!searchWord.trim()) {
      toast.error('Veuillez entrer un mot');
      return;
    }
    
    const url = `https://www.wordreference.com/enfr/${encodeURIComponent(searchWord)}`;
    window.open(url, '_blank');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 to-blue-50 flex items-center justify-center">
        <p className="text-xl text-gray-600">Chargement du livre...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-blue-50 p-6">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex justify-between items-center">
          <div>
            <Button onClick={() => navigate('/kalamatheque')} variant="outline" className="mb-2">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Retour à la bibliothèque
            </Button>
            <h1 className="text-3xl font-bold text-gray-800">{book.title}</h1>
            {book.author && <p className="text-gray-600">Par {book.author}</p>}
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Main Content - Book Content */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="bg-teal-50">
                <CardTitle>📖 Contenu du livre</CardTitle>
                <p className="text-sm text-gray-600">Sélectionnez du texte pour utiliser l'Assistant IA</p>
              </CardHeader>
              <CardContent className="pt-6">
                <div 
                  onMouseUp={handleTextSelection}
                  className="prose max-w-none p-6 bg-white rounded-lg border min-h-[600px]"
                >
                  {/* Book content display */}
                  {book.file_type === 'txt' || book.file_type === 'html' ? (
                    <div>
                      <p className="text-gray-700 leading-relaxed">
                        {book.description}
                      </p>
                      <div className="mt-4 p-4 bg-blue-50 rounded">
                        <p className="text-sm text-blue-800">
                          📄 Pour afficher le contenu complet, le fichier doit être chargé depuis l'URL: 
                          <a href={book.file_url} target="_blank" rel="noopener noreferrer" className="underline ml-1">
                            Ouvrir le fichier
                          </a>
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12">
                      <BookOpen className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                      <p className="text-gray-600 mb-4">Ce livre est au format {book.file_type.toUpperCase()}</p>
                      <a 
                        href={book.file_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-block px-6 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition"
                      >
                        📥 Télécharger et ouvrir le livre
                      </a>
                    </div>
                  )}
                </div>

                {selectedText && (
                  <div className="mt-4 p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <p className="text-sm font-semibold text-purple-800 mb-2">Texte sélectionné :</p>
                    <p className="text-gray-700 italic">"{selectedText}"</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar - Tools */}
          <div className="space-y-6">
            {/* Dictionary Search */}
            <Card className="border-blue-200">
              <CardHeader className="bg-blue-50">
                <CardTitle className="text-lg">🔍 Dictionnaire</CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="space-y-2">
                  <Input
                    type="text"
                    placeholder="Rechercher un mot..."
                    value={searchWord}
                    onChange={(e) => setSearchWord(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button onClick={handleListenWord} variant="outline" className="flex-1">
                      <Volume2 className="mr-2 h-4 w-4" />
                      Écouter
                    </Button>
                    <Button onClick={handleSearchInDictionary} className="flex-1 bg-blue-600 hover:bg-blue-700">
                      <Search className="mr-2 h-4 w-4" />
                      Chercher
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* AI Assistant */}
            <Card className="border-purple-200">
              <CardHeader className="bg-purple-50">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Assistant IA
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-4">
                <div className="space-y-2">
                  <Button 
                    onClick={() => handleAiAction('summarize')} 
                    className="w-full bg-purple-600 hover:bg-purple-700"
                    disabled={!selectedText || aiLoading}
                  >
                    📝 Résumer
                  </Button>
                  <Button 
                    onClick={() => handleAiAction('explain')} 
                    className="w-full bg-purple-600 hover:bg-purple-700"
                    disabled={!selectedText || aiLoading}
                  >
                    💡 Expliquer
                  </Button>
                  <Button 
                    onClick={() => handleAiAction('examples')} 
                    className="w-full bg-purple-600 hover:bg-purple-700"
                    disabled={!selectedText || aiLoading}
                  >
                    📚 Exemples
                  </Button>
                </div>

                {aiLoading && (
                  <div className="mt-4 text-center">
                    <p className="text-sm text-gray-600">🤖 L'IA analyse le texte...</p>
                  </div>
                )}

                {aiResult && (
                  <div className="mt-4 p-4 bg-white rounded-lg border">
                    <p className="text-sm font-semibold text-purple-800 mb-2">Résultat :</p>
                    <Textarea 
                      value={aiResult} 
                      readOnly 
                      rows={8}
                      className="text-sm"
                    />
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

export default BookReader;