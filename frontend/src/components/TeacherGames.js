import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Checkbox } from './ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Trash2, Plus, Send, Trophy, Brain, Layers, HelpCircle, Users } from 'lucide-react';

const TeacherGames = ({ students }) => {
  // Flashcards state
  const [flashcardSets, setFlashcardSets] = useState([]);
  const [showCreateFlashcard, setShowCreateFlashcard] = useState(false);
  const [showAddCard, setShowAddCard] = useState(false);
  const [selectedSet, setSelectedSet] = useState(null);
  const [newSetData, setNewSetData] = useState({ title: '', description: '' });
  const [newCard, setNewCard] = useState({ question: '', answer: '', image_url: '' });

  // Quiz state
  const [quizzes, setQuizzes] = useState([]);
  const [showCreateQuiz, setShowCreateQuiz] = useState(false);
  const [showAddQuestion, setShowAddQuestion] = useState(false);
  const [selectedQuiz, setSelectedQuiz] = useState(null);
  const [newQuizData, setNewQuizData] = useState({ title: '', description: '', time_limit: 0 });
  const [newQuestion, setNewQuestion] = useState({
    question: '', options: ['', '', '', ''], correct_answer: 0, image_url: ''
  });

  // Memory game state
  const [memoryGames, setMemoryGames] = useState([]);
  const [showCreateMemory, setShowCreateMemory] = useState(false);
  const [showAddPair, setShowAddPair] = useState(false);
  const [selectedMemory, setSelectedMemory] = useState(null);
  const [newMemoryData, setNewMemoryData] = useState({ title: '', description: '' });
  const [newPair, setNewPair] = useState({ card1: '', card2: '', type: 'text' });

  // Assignment state
  const [gameScores, setGameScores] = useState([]);
  const [showAssignGame, setShowAssignGame] = useState(false);
  const [assignData, setAssignData] = useState({
    game_type: 'flashcard',
    game_id: '',
    game_url: '',
    title: '',
    student_ids: [],
    selectAll: false
  });

  useEffect(() => {
    fetchFlashcardSets();
    fetchQuizzes();
    fetchMemoryGames();
    fetchGameScores();
  }, []);

  // Fetch functions
  const fetchFlashcardSets = async () => {
    try {
      const response = await apiClient.get('/teacher/my-flashcard-sets');
      setFlashcardSets(response.data);
    } catch (error) {
      console.error('Error fetching flashcard sets:', error);
    }
  };

  const fetchQuizzes = async () => {
    try {
      const response = await apiClient.get('/teacher/my-quizzes');
      setQuizzes(response.data);
    } catch (error) {
      console.error('Error fetching quizzes:', error);
    }
  };

  const fetchMemoryGames = async () => {
    try {
      const response = await apiClient.get('/teacher/my-memory-games');
      setMemoryGames(response.data);
    } catch (error) {
      console.error('Error fetching memory games:', error);
    }
  };

  const fetchGameScores = async () => {
    try {
      const response = await apiClient.get('/teacher/game-scores');
      setGameScores(response.data);
    } catch (error) {
      console.error('Error fetching game scores:', error);
    }
  };

  // Flashcard handlers
  const handleCreateSet = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/teacher/create-flashcard-set', newSetData);
      toast.success('Set de flashcards créé !');
      setNewSetData({ title: '', description: '' });
      setShowCreateFlashcard(false);
      fetchFlashcardSets();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleAddCard = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/teacher/add-flashcard', {
        set_id: selectedSet.id,
        ...newCard
      });
      toast.success('Flashcard ajoutée !');
      setNewCard({ question: '', answer: '', image_url: '' });
      setShowAddCard(false);
      fetchFlashcardSets();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const handleDeleteSet = async (setId) => {
    if (!window.confirm('Supprimer ce set de flashcards ?')) return;
    try {
      await apiClient.delete(`/teacher/delete-flashcard-set/${setId}`);
      toast.success('Set supprimé');
      fetchFlashcardSets();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  // Quiz handlers
  const handleCreateQuiz = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/teacher/create-quiz', newQuizData);
      toast.success('Quiz créé !');
      setNewQuizData({ title: '', description: '', time_limit: 0 });
      setShowCreateQuiz(false);
      fetchQuizzes();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleAddQuestion = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/teacher/add-quiz-question', {
        quiz_id: selectedQuiz.id,
        ...newQuestion
      });
      toast.success('Question ajoutée !');
      setNewQuestion({ question: '', options: ['', '', '', ''], correct_answer: 0, image_url: '' });
      setShowAddQuestion(false);
      fetchQuizzes();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const handleDeleteQuiz = async (quizId) => {
    if (!window.confirm('Supprimer ce quiz ?')) return;
    try {
      await apiClient.delete(`/teacher/delete-quiz/${quizId}`);
      toast.success('Quiz supprimé');
      fetchQuizzes();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  // Memory game handlers
  const handleCreateMemory = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/teacher/create-memory-game', newMemoryData);
      toast.success('Jeu Memory créé !');
      setNewMemoryData({ title: '', description: '' });
      setShowCreateMemory(false);
      fetchMemoryGames();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleAddPair = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/teacher/add-memory-pair', {
        game_id: selectedMemory.id,
        ...newPair
      });
      toast.success('Paire ajoutée !');
      setNewPair({ card1: '', card2: '', type: 'text' });
      setShowAddPair(false);
      fetchMemoryGames();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout');
    }
  };

  const handleDeleteMemory = async (gameId) => {
    if (!window.confirm('Supprimer ce jeu Memory ?')) return;
    try {
      await apiClient.delete(`/teacher/delete-memory-game/${gameId}`);
      toast.success('Jeu Memory supprimé');
      fetchMemoryGames();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  // Assignment handler
  const handleAssignGame = async (e) => {
    e.preventDefault();
    
    const studentIds = assignData.selectAll 
      ? students.map(s => s.id) 
      : assignData.student_ids;
    
    if (studentIds.length === 0) {
      toast.error('Sélectionnez au moins un étudiant');
      return;
    }
    
    try {
      const response = await apiClient.post('/teacher/assign-game', {
        ...assignData,
        student_ids: studentIds
      });
      toast.success(`🎮 ${response.data.message}`);
      setAssignData({
        game_type: 'flashcard',
        game_id: '',
        game_url: '',
        title: '',
        student_ids: [],
        selectAll: false
      });
      setShowAssignGame(false);
      fetchGameScores();
    } catch (error) {
      toast.error('Erreur lors de l\'assignation');
    }
  };

  const toggleStudentSelection = (studentId) => {
    setAssignData(prev => ({
      ...prev,
      student_ids: prev.student_ids.includes(studentId)
        ? prev.student_ids.filter(id => id !== studentId)
        : [...prev.student_ids, studentId]
    }));
  };

  const openAssignDialog = (gameType, gameId, title) => {
    setAssignData({
      game_type: gameType,
      game_id: gameId,
      game_url: '',
      title: title,
      student_ids: [],
      selectAll: false
    });
    setShowAssignGame(true);
  };

  return (
    <div className="space-y-6">
      <Tabs defaultValue="flashcards" className="w-full">
        <TabsList className="grid w-full grid-cols-4 mb-4">
          <TabsTrigger value="flashcards" className="flex items-center gap-2">
            <Layers className="w-4 h-4" />
            Flashcards
          </TabsTrigger>
          <TabsTrigger value="quiz" className="flex items-center gap-2">
            <HelpCircle className="w-4 h-4" />
            Quiz
          </TabsTrigger>
          <TabsTrigger value="memory" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Memory
          </TabsTrigger>
          <TabsTrigger value="scores" className="flex items-center gap-2">
            <Trophy className="w-4 h-4" />
            Scores
          </TabsTrigger>
        </TabsList>

        {/* FLASHCARDS TAB */}
        <TabsContent value="flashcards">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">🎴</span>
                Mes Sets de Flashcards
              </CardTitle>
              <CardDescription>
                Créez des flashcards pour aider vos étudiants à réviser
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCreateFlashcard(true)} className="mb-4">
                <Plus className="w-4 h-4 mr-2" />
                Créer un nouveau set
              </Button>

              <div className="grid md:grid-cols-2 gap-4">
                {flashcardSets.map((set) => (
                  <Card key={set.id} className="border-2 border-yellow-200">
                    <CardContent className="p-4">
                      <h3 className="font-bold text-lg">{set.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{set.description}</p>
                      <p className="text-xs text-gray-500 mb-3">
                        {set.flashcards?.length || 0} carte(s)
                      </p>
                      <div className="flex gap-2 flex-wrap">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedSet(set);
                            setShowAddCard(true);
                          }}
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Carte
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-green-600 border-green-200"
                          onClick={() => openAssignDialog('flashcard', set.id, set.title)}
                        >
                          <Send className="w-4 h-4 mr-1" />
                          Assigner
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteSet(set.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Kahoot Links */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">🎯</span>
                Liens Kahoot
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={() => {
                  setAssignData({
                    game_type: 'kahoot',
                    game_id: '',
                    game_url: '',
                    title: '',
                    student_ids: [],
                    selectAll: false
                  });
                  setShowAssignGame(true);
                }}
              >
                <Plus className="w-4 h-4 mr-2" />
                Assigner un Kahoot
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* QUIZ TAB */}
        <TabsContent value="quiz">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">❓</span>
                Mes Quiz
              </CardTitle>
              <CardDescription>
                Créez des quiz à choix multiples pour tester vos étudiants
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCreateQuiz(true)} className="mb-4 bg-purple-600 hover:bg-purple-700">
                <Plus className="w-4 h-4 mr-2" />
                Créer un nouveau quiz
              </Button>

              <div className="grid md:grid-cols-2 gap-4">
                {quizzes.map((quiz) => (
                  <Card key={quiz.id} className="border-2 border-purple-200">
                    <CardContent className="p-4">
                      <h3 className="font-bold text-lg">{quiz.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{quiz.description}</p>
                      <p className="text-xs text-gray-500 mb-3">
                        {quiz.questions?.length || 0} question(s)
                        {quiz.time_limit > 0 && ` • ${quiz.time_limit}s/question`}
                      </p>
                      <div className="flex gap-2 flex-wrap">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedQuiz(quiz);
                            setShowAddQuestion(true);
                          }}
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Question
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-green-600 border-green-200"
                          onClick={() => openAssignDialog('quiz', quiz.id, quiz.title)}
                        >
                          <Send className="w-4 h-4 mr-1" />
                          Assigner
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteQuiz(quiz.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              {quizzes.length === 0 && (
                <p className="text-gray-500 text-center py-8">Aucun quiz créé. Commencez par en créer un !</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* MEMORY TAB */}
        <TabsContent value="memory">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">🧠</span>
                Mes Jeux Memory
              </CardTitle>
              <CardDescription>
                Créez des jeux de mémoire pour associer des paires de mots
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button onClick={() => setShowCreateMemory(true)} className="mb-4 bg-blue-600 hover:bg-blue-700">
                <Plus className="w-4 h-4 mr-2" />
                Créer un nouveau Memory
              </Button>

              <div className="grid md:grid-cols-2 gap-4">
                {memoryGames.map((game) => (
                  <Card key={game.id} className="border-2 border-blue-200">
                    <CardContent className="p-4">
                      <h3 className="font-bold text-lg">{game.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{game.description}</p>
                      <p className="text-xs text-gray-500 mb-3">
                        {game.pairs?.length || 0} paire(s)
                      </p>
                      <div className="flex gap-2 flex-wrap">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedMemory(game);
                            setShowAddPair(true);
                          }}
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Paire
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-green-600 border-green-200"
                          onClick={() => openAssignDialog('memory', game.id, game.title)}
                        >
                          <Send className="w-4 h-4 mr-1" />
                          Assigner
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteMemory(game.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              {memoryGames.length === 0 && (
                <p className="text-gray-500 text-center py-8">Aucun jeu Memory créé. Commencez par en créer un !</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SCORES TAB */}
        <TabsContent value="scores">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="w-6 h-6 text-yellow-500" />
                Scores des étudiants
              </CardTitle>
              <CardDescription>
                Consultez les performances de vos étudiants
              </CardDescription>
            </CardHeader>
            <CardContent>
              {gameScores.length === 0 ? (
                <p className="text-gray-500 text-center py-8">Aucun score pour le moment</p>
              ) : (
                <div className="space-y-3">
                  {gameScores.map((score) => (
                    <div
                      key={score.id}
                      className="flex justify-between items-center p-4 border rounded-lg bg-gradient-to-r from-yellow-50 to-orange-50"
                    >
                      <div>
                        <p className="font-semibold">{score.student_name}</p>
                        <p className="text-sm text-gray-600">
                          {score.game_type === 'flashcard' && '🎴 '}
                          {score.game_type === 'quiz' && '❓ '}
                          {score.game_type === 'memory' && '🧠 '}
                          {score.game_type === 'kahoot' && '🎯 '}
                          {score.title}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(score.completed_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-2xl font-bold text-yellow-600">
                          {score.score}/{score.total}
                        </p>
                        <p className="text-xs text-gray-500">
                          {Math.round((score.score / score.total) * 100)}%
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* CREATE FLASHCARD SET DIALOG */}
      <Dialog open={showCreateFlashcard} onOpenChange={setShowCreateFlashcard}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Créer un nouveau set de flashcards</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateSet} className="space-y-4">
            <div>
              <Label>Titre *</Label>
              <Input
                value={newSetData.title}
                onChange={(e) => setNewSetData({ ...newSetData, title: e.target.value })}
                required
                placeholder="Ex: Vocabulaire - Famille"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={newSetData.description}
                onChange={(e) => setNewSetData({ ...newSetData, description: e.target.value })}
                placeholder="Description du set"
              />
            </div>
            <Button type="submit" className="w-full">Créer le set</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* ADD FLASHCARD DIALOG */}
      <Dialog open={showAddCard} onOpenChange={setShowAddCard}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter une flashcard</DialogTitle>
            <DialogDescription>{selectedSet?.title}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddCard} className="space-y-4">
            <div>
              <Label>Mot en français (Recto) *</Label>
              <Input
                value={newCard.question}
                onChange={(e) => setNewCard({ ...newCard, question: e.target.value })}
                required
                placeholder="Ex: Pomme"
              />
            </div>
            <div>
              <Label>Mot en anglais (Verso) *</Label>
              <Input
                value={newCard.answer}
                onChange={(e) => setNewCard({ ...newCard, answer: e.target.value })}
                required
                placeholder="Ex: Apple"
              />
            </div>
            <div>
              <Label>URL de l'image (optionnel)</Label>
              <Input
                value={newCard.image_url}
                onChange={(e) => setNewCard({ ...newCard, image_url: e.target.value })}
                placeholder="https://example.com/image.jpg"
              />
            </div>
            <Button type="submit" className="w-full">Ajouter la carte</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* CREATE QUIZ DIALOG */}
      <Dialog open={showCreateQuiz} onOpenChange={setShowCreateQuiz}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Créer un nouveau quiz</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateQuiz} className="space-y-4">
            <div>
              <Label>Titre *</Label>
              <Input
                value={newQuizData.title}
                onChange={(e) => setNewQuizData({ ...newQuizData, title: e.target.value })}
                required
                placeholder="Ex: Quiz - Verbes Irréguliers"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={newQuizData.description}
                onChange={(e) => setNewQuizData({ ...newQuizData, description: e.target.value })}
                placeholder="Description du quiz"
              />
            </div>
            <div>
              <Label>Temps par question (secondes, 0 = illimité)</Label>
              <Input
                type="number"
                min="0"
                value={newQuizData.time_limit}
                onChange={(e) => setNewQuizData({ ...newQuizData, time_limit: parseInt(e.target.value) || 0 })}
              />
            </div>
            <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700">Créer le quiz</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* ADD QUIZ QUESTION DIALOG */}
      <Dialog open={showAddQuestion} onOpenChange={setShowAddQuestion}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Ajouter une question</DialogTitle>
            <DialogDescription>{selectedQuiz?.title}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddQuestion} className="space-y-4">
            <div>
              <Label>Question *</Label>
              <Textarea
                value={newQuestion.question}
                onChange={(e) => setNewQuestion({ ...newQuestion, question: e.target.value })}
                required
                placeholder="Ex: What is the past tense of 'go'?"
              />
            </div>
            <div className="space-y-2">
              <Label>Options (4 choix) *</Label>
              {newQuestion.options.map((opt, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="correct"
                    checked={newQuestion.correct_answer === idx}
                    onChange={() => setNewQuestion({ ...newQuestion, correct_answer: idx })}
                    className="w-4 h-4 text-green-600"
                  />
                  <Input
                    value={opt}
                    onChange={(e) => {
                      const newOpts = [...newQuestion.options];
                      newOpts[idx] = e.target.value;
                      setNewQuestion({ ...newQuestion, options: newOpts });
                    }}
                    placeholder={`Option ${idx + 1}`}
                    required
                  />
                </div>
              ))}
              <p className="text-xs text-gray-500">Sélectionnez la bonne réponse avec le bouton radio</p>
            </div>
            <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700">Ajouter la question</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* CREATE MEMORY GAME DIALOG */}
      <Dialog open={showCreateMemory} onOpenChange={setShowCreateMemory}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Créer un nouveau jeu Memory</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateMemory} className="space-y-4">
            <div>
              <Label>Titre *</Label>
              <Input
                value={newMemoryData.title}
                onChange={(e) => setNewMemoryData({ ...newMemoryData, title: e.target.value })}
                required
                placeholder="Ex: Memory - Animaux"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={newMemoryData.description}
                onChange={(e) => setNewMemoryData({ ...newMemoryData, description: e.target.value })}
                placeholder="Description du jeu"
              />
            </div>
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">Créer le jeu Memory</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* ADD MEMORY PAIR DIALOG */}
      <Dialog open={showAddPair} onOpenChange={setShowAddPair}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ajouter une paire</DialogTitle>
            <DialogDescription>{selectedMemory?.title}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddPair} className="space-y-4">
            <div>
              <Label>Mot en français (Carte 1) *</Label>
              <Input
                value={newPair.card1}
                onChange={(e) => setNewPair({ ...newPair, card1: e.target.value })}
                required
                placeholder="Ex: Chien"
              />
            </div>
            <div>
              <Label>Mot en anglais (Carte 2) *</Label>
              <Input
                value={newPair.card2}
                onChange={(e) => setNewPair({ ...newPair, card2: e.target.value })}
                required
                placeholder="Ex: Dog"
              />
            </div>
            <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">Ajouter la paire</Button>
          </form>
        </DialogContent>
      </Dialog>

      {/* ASSIGN GAME DIALOG */}
      <Dialog open={showAssignGame} onOpenChange={setShowAssignGame}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send className="w-5 h-5" />
              Assigner un jeu
            </DialogTitle>
            <DialogDescription>
              {assignData.title || 'Sélectionnez les étudiants'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAssignGame} className="space-y-4">
            {assignData.game_type === 'kahoot' && (
              <>
                <div>
                  <Label>Titre du Kahoot *</Label>
                  <Input
                    value={assignData.title}
                    onChange={(e) => setAssignData({ ...assignData, title: e.target.value })}
                    required
                    placeholder="Titre du Kahoot"
                  />
                </div>
                <div>
                  <Label>Lien Kahoot *</Label>
                  <Input
                    value={assignData.game_url}
                    onChange={(e) => setAssignData({ ...assignData, game_url: e.target.value })}
                    required
                    placeholder="https://kahoot.it/..."
                  />
                </div>
              </>
            )}

            <div>
              <Label className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Sélectionner les étudiants
              </Label>
              
              <div className="mt-2 p-3 border rounded-lg bg-gray-50">
                <label className="flex items-center gap-2 mb-3 cursor-pointer">
                  <Checkbox
                    checked={assignData.selectAll}
                    onCheckedChange={(checked) => setAssignData({ 
                      ...assignData, 
                      selectAll: checked,
                      student_ids: checked ? students.map(s => s.id) : []
                    })}
                  />
                  <span className="font-medium text-green-600">
                    Tous les étudiants ({students.length})
                  </span>
                </label>
                
                <div className="max-h-48 overflow-y-auto space-y-2">
                  {students.map((student) => (
                    <label key={student.id} className="flex items-center gap-2 cursor-pointer hover:bg-white p-1 rounded">
                      <Checkbox
                        checked={assignData.selectAll || assignData.student_ids.includes(student.id)}
                        onCheckedChange={() => {
                          if (!assignData.selectAll) {
                            toggleStudentSelection(student.id);
                          }
                        }}
                        disabled={assignData.selectAll}
                      />
                      <span className="text-sm">
                        {student.first_name} {student.last_name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              
              {!assignData.selectAll && assignData.student_ids.length > 0 && (
                <p className="text-sm text-green-600 mt-2">
                  {assignData.student_ids.length} étudiant(s) sélectionné(s)
                </p>
              )}
            </div>

            <Button 
              type="submit" 
              className="w-full bg-green-600 hover:bg-green-700"
              disabled={!assignData.selectAll && assignData.student_ids.length === 0}
            >
              <Send className="w-4 h-4 mr-2" />
              Assigner à {assignData.selectAll ? 'tous' : assignData.student_ids.length} étudiant(s)
            </Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TeacherGames;
