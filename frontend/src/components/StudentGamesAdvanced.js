import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Trophy, ExternalLink, Star, X, Check, Sparkles, Brain, HelpCircle, Layers, RefreshCw } from 'lucide-react';

const StudentGamesAdvanced = () => {
  const [games, setGames] = useState([]);
  const [activeGame, setActiveGame] = useState(null);
  const [gameType, setGameType] = useState(null);
  
  // Flashcard state
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [knownCards, setKnownCards] = useState(0);
  const [unknownCards, setUnknownCards] = useState(0);
  const [favorites, setFavorites] = useState([]);
  const [gameFinished, setGameFinished] = useState(false);
  const [surpriseMode, setSurpriseMode] = useState(false);

  // Quiz state
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [quizScore, setQuizScore] = useState(0);
  const [quizAnswered, setQuizAnswered] = useState(false);
  const [timeLeft, setTimeLeft] = useState(0);

  // Memory state
  const [memoryCards, setMemoryCards] = useState([]);
  const [flippedCards, setFlippedCards] = useState([]);
  const [matchedPairs, setMatchedPairs] = useState([]);
  const [memoryMoves, setMemoryMoves] = useState(0);

  useEffect(() => {
    fetchGames();
  }, []);

  // Timer for quiz
  useEffect(() => {
    let timer;
    if (gameType === 'quiz' && activeGame && timeLeft > 0 && !quizAnswered) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            handleQuizTimeout();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [gameType, activeGame, timeLeft, quizAnswered]);

  const fetchGames = async () => {
    try {
      const response = await apiClient.get('/student/my-games');
      setGames(response.data);
    } catch (error) {
      toast.error('Erreur lors du chargement des jeux');
    }
  };

  const shuffleArray = (array) => {
    const arr = [...array];
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  };

  // ============ FLASHCARD GAME ============
  const startFlashcardGame = (game) => {
    const cards = surpriseMode ? shuffleArray([...game.flashcards]) : game.flashcards;
    setActiveGame({ ...game, flashcards: cards });
    setGameType('flashcard');
    setCurrentCardIndex(0);
    setIsFlipped(false);
    setKnownCards(0);
    setUnknownCards(0);
    setFavorites([]);
    setGameFinished(false);
  };

  const handleSwipeLeft = () => {
    setUnknownCards(unknownCards + 1);
    nextFlashcard();
  };

  const handleSwipeRight = () => {
    setKnownCards(knownCards + 1);
    nextFlashcard();
  };

  const handleFavorite = () => {
    const currentCard = activeGame.flashcards[currentCardIndex];
    setFavorites([...favorites, currentCard]);
    toast.success('⭐ Favori ajouté!');
  };

  const nextFlashcard = () => {
    if (currentCardIndex < activeGame.flashcards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setIsFlipped(false);
    } else {
      finishGame(knownCards + 1, activeGame.flashcards.length);
    }
  };

  // ============ QUIZ GAME ============
  const startQuizGame = (game) => {
    setActiveGame(game);
    setGameType('quiz');
    setCurrentQuestionIndex(0);
    setSelectedAnswer(null);
    setQuizScore(0);
    setQuizAnswered(false);
    setGameFinished(false);
    if (game.time_limit > 0) {
      setTimeLeft(game.time_limit);
    }
  };

  const handleQuizAnswer = (answerIndex) => {
    if (quizAnswered) return;
    
    setSelectedAnswer(answerIndex);
    setQuizAnswered(true);
    
    const currentQuestion = activeGame.questions[currentQuestionIndex];
    if (answerIndex === currentQuestion.correct_answer) {
      setQuizScore(quizScore + 1);
      toast.success('✅ Bonne réponse!');
    } else {
      toast.error('❌ Mauvaise réponse');
    }
  };

  const handleQuizTimeout = () => {
    if (!quizAnswered) {
      setQuizAnswered(true);
      toast.error('⏰ Temps écoulé!');
    }
  };

  const nextQuizQuestion = () => {
    if (currentQuestionIndex < activeGame.questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setSelectedAnswer(null);
      setQuizAnswered(false);
      if (activeGame.time_limit > 0) {
        setTimeLeft(activeGame.time_limit);
      }
    } else {
      finishGame(quizScore + (selectedAnswer === activeGame.questions[currentQuestionIndex].correct_answer ? 1 : 0), activeGame.questions.length);
    }
  };

  // ============ MEMORY GAME ============
  const startMemoryGame = (game) => {
    // Create pairs of cards and shuffle them
    const cards = [];
    game.pairs.forEach((pair, idx) => {
      cards.push({ id: `${idx}-a`, content: pair.card1, pairId: idx, type: 'french' });
      cards.push({ id: `${idx}-b`, content: pair.card2, pairId: idx, type: 'english' });
    });
    
    setActiveGame(game);
    setGameType('memory');
    setMemoryCards(shuffleArray(cards));
    setFlippedCards([]);
    setMatchedPairs([]);
    setMemoryMoves(0);
    setGameFinished(false);
  };

  const handleMemoryCardClick = (cardId) => {
    if (flippedCards.length >= 2) return;
    if (flippedCards.includes(cardId)) return;
    if (matchedPairs.some(p => memoryCards.find(c => c.id === cardId)?.pairId === p)) return;
    
    const newFlipped = [...flippedCards, cardId];
    setFlippedCards(newFlipped);
    
    if (newFlipped.length === 2) {
      setMemoryMoves(memoryMoves + 1);
      const card1 = memoryCards.find(c => c.id === newFlipped[0]);
      const card2 = memoryCards.find(c => c.id === newFlipped[1]);
      
      if (card1.pairId === card2.pairId) {
        // Match found!
        setMatchedPairs([...matchedPairs, card1.pairId]);
        setFlippedCards([]);
        toast.success('🎉 Paire trouvée!');
        
        // Check if game is finished
        if (matchedPairs.length + 1 === activeGame.pairs.length) {
          setTimeout(() => {
            finishGame(activeGame.pairs.length, activeGame.pairs.length);
          }, 500);
        }
      } else {
        // No match, flip back after delay
        setTimeout(() => {
          setFlippedCards([]);
        }, 1000);
      }
    }
  };

  // ============ COMMON ============
  const finishGame = async (score, total) => {
    setGameFinished(true);
    try {
      await apiClient.post('/student/submit-game-score', {
        assignment_id: activeGame.id,
        score: score,
        total: total
      });
      toast.success(`🎉 Score: ${score}/${total}`);
    } catch (error) {
      console.error('Error submitting score:', error);
    }
  };

  const exitGame = () => {
    setActiveGame(null);
    setGameType(null);
    setGameFinished(false);
    setSurpriseMode(false);
    fetchGames();
  };

  // ============ RENDER FLASHCARD GAME ============
  const renderFlashcardGame = () => {
    if (gameFinished) {
      return (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-2xl font-bold mb-4">Bravo!</h2>
          <div className="grid grid-cols-2 gap-4 max-w-xs mx-auto mb-6">
            <div className="bg-green-100 p-4 rounded-lg">
              <p className="text-3xl font-bold text-green-600">{knownCards}</p>
              <p className="text-sm text-green-700">Je sais</p>
            </div>
            <div className="bg-red-100 p-4 rounded-lg">
              <p className="text-3xl font-bold text-red-600">{unknownCards}</p>
              <p className="text-sm text-red-700">À réviser</p>
            </div>
          </div>
          <p className="text-gray-600 mb-6">
            {Math.round((knownCards / (knownCards + unknownCards)) * 100)}% de réussite
          </p>
          <Button onClick={exitGame}>Retour aux jeux</Button>
        </div>
      );
    }

    const card = activeGame.flashcards[currentCardIndex];
    return (
      <div className="max-w-md mx-auto">
        <div className="flex justify-between items-center mb-4">
          <Button variant="ghost" onClick={exitGame}>← Quitter</Button>
          <span className="text-sm text-gray-500">
            {currentCardIndex + 1} / {activeGame.flashcards.length}
          </span>
        </div>
        
        <div 
          className={`relative h-64 cursor-pointer transition-transform duration-500 ${isFlipped ? 'scale-x-[-1]' : ''}`}
          onClick={() => setIsFlipped(!isFlipped)}
        >
          <Card className="h-full flex items-center justify-center bg-gradient-to-br from-yellow-100 to-orange-100">
            <CardContent className={`text-center ${isFlipped ? 'scale-x-[-1]' : ''}`}>
              <p className="text-2xl font-bold">
                {isFlipped ? card.answer : card.question}
              </p>
              <p className="text-sm text-gray-500 mt-2">
                {isFlipped ? '🇬🇧 Anglais' : '🇫🇷 Français'}
              </p>
            </CardContent>
          </Card>
        </div>
        
        <p className="text-center text-gray-500 text-sm my-4">Touche la carte pour la retourner</p>
        
        <div className="flex justify-center gap-4">
          <Button 
            variant="outline" 
            className="border-red-300 text-red-600 hover:bg-red-50"
            onClick={handleSwipeLeft}
          >
            <X className="w-5 h-5 mr-1" /> Je ne sais pas
          </Button>
          <Button 
            variant="outline"
            className="border-yellow-300 text-yellow-600 hover:bg-yellow-50"
            onClick={handleFavorite}
          >
            <Star className="w-5 h-5" />
          </Button>
          <Button 
            variant="outline"
            className="border-green-300 text-green-600 hover:bg-green-50"
            onClick={handleSwipeRight}
          >
            <Check className="w-5 h-5 mr-1" /> Je sais
          </Button>
        </div>
      </div>
    );
  };

  // ============ RENDER QUIZ GAME ============
  const renderQuizGame = () => {
    if (gameFinished) {
      const percentage = Math.round((quizScore / activeGame.questions.length) * 100);
      return (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">
            {percentage >= 80 ? '🏆' : percentage >= 50 ? '👍' : '📚'}
          </div>
          <h2 className="text-2xl font-bold mb-4">Quiz terminé!</h2>
          <div className="bg-purple-100 p-6 rounded-lg max-w-xs mx-auto mb-6">
            <p className="text-4xl font-bold text-purple-600">{quizScore}/{activeGame.questions.length}</p>
            <p className="text-purple-700">{percentage}%</p>
          </div>
          <Button onClick={exitGame}>Retour aux jeux</Button>
        </div>
      );
    }

    const question = activeGame.questions[currentQuestionIndex];
    return (
      <div className="max-w-lg mx-auto">
        <div className="flex justify-between items-center mb-4">
          <Button variant="ghost" onClick={exitGame}>← Quitter</Button>
          <div className="flex items-center gap-4">
            {activeGame.time_limit > 0 && (
              <span className={`font-bold ${timeLeft <= 5 ? 'text-red-500 animate-pulse' : 'text-gray-600'}`}>
                ⏱️ {timeLeft}s
              </span>
            )}
            <span className="text-sm text-gray-500">
              {currentQuestionIndex + 1} / {activeGame.questions.length}
            </span>
          </div>
        </div>
        
        <Card className="mb-4">
          <CardContent className="pt-6">
            <h3 className="text-xl font-semibold mb-6">{question.question}</h3>
            
            <div className="space-y-3">
              {question.options.map((option, idx) => {
                let bgColor = 'bg-white hover:bg-gray-50';
                if (quizAnswered) {
                  if (idx === question.correct_answer) {
                    bgColor = 'bg-green-100 border-green-500';
                  } else if (idx === selectedAnswer && idx !== question.correct_answer) {
                    bgColor = 'bg-red-100 border-red-500';
                  }
                } else if (selectedAnswer === idx) {
                  bgColor = 'bg-purple-100 border-purple-500';
                }
                
                return (
                  <button
                    key={idx}
                    className={`w-full p-4 text-left rounded-lg border-2 transition-colors ${bgColor}`}
                    onClick={() => handleQuizAnswer(idx)}
                    disabled={quizAnswered}
                  >
                    <span className="font-medium mr-2">{String.fromCharCode(65 + idx)}.</span>
                    {option}
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>
        
        {quizAnswered && (
          <div className="text-center">
            <Button onClick={nextQuizQuestion} className="bg-purple-600 hover:bg-purple-700">
              {currentQuestionIndex < activeGame.questions.length - 1 ? 'Question suivante →' : 'Voir le résultat'}
            </Button>
          </div>
        )}
      </div>
    );
  };

  // ============ RENDER MEMORY GAME ============
  const renderMemoryGame = () => {
    if (gameFinished) {
      return (
        <div className="text-center py-8">
          <div className="text-6xl mb-4">🧠</div>
          <h2 className="text-2xl font-bold mb-4">Memory terminé!</h2>
          <div className="bg-blue-100 p-6 rounded-lg max-w-xs mx-auto mb-6">
            <p className="text-4xl font-bold text-blue-600">{matchedPairs.length} paires</p>
            <p className="text-blue-700">en {memoryMoves} coups</p>
          </div>
          <Button onClick={exitGame}>Retour aux jeux</Button>
        </div>
      );
    }

    const gridCols = memoryCards.length <= 8 ? 'grid-cols-4' : 'grid-cols-6';
    
    return (
      <div className="max-w-2xl mx-auto">
        <div className="flex justify-between items-center mb-4">
          <Button variant="ghost" onClick={exitGame}>← Quitter</Button>
          <span className="text-sm text-gray-500">
            {matchedPairs.length} / {activeGame.pairs.length} paires • {memoryMoves} coups
          </span>
        </div>
        
        <div className={`grid ${gridCols} gap-3`}>
          {memoryCards.map((card) => {
            const isFlipped = flippedCards.includes(card.id);
            const isMatched = matchedPairs.includes(card.pairId);
            
            return (
              <button
                key={card.id}
                className={`
                  aspect-square rounded-lg text-center flex items-center justify-center p-2
                  transition-all duration-300 transform
                  ${isMatched ? 'bg-green-200 border-green-400' : isFlipped ? 'bg-blue-100 border-blue-400' : 'bg-blue-600 hover:bg-blue-500'}
                  border-2 ${isFlipped || isMatched ? 'scale-100' : 'scale-95 hover:scale-100'}
                `}
                onClick={() => !isMatched && handleMemoryCardClick(card.id)}
                disabled={isMatched}
              >
                {(isFlipped || isMatched) ? (
                  <span className={`text-sm font-medium ${isMatched ? 'text-green-700' : 'text-blue-700'}`}>
                    {card.content}
                  </span>
                ) : (
                  <span className="text-2xl">❓</span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  // ============ MAIN RENDER ============
  if (activeGame) {
    if (gameType === 'flashcard') return renderFlashcardGame();
    if (gameType === 'quiz') return renderQuizGame();
    if (gameType === 'memory') return renderMemoryGame();
  }

  // Games list
  const flashcardGames = games.filter(g => g.game_type === 'flashcard' && g.flashcards?.length > 0);
  const quizGames = games.filter(g => g.game_type === 'quiz' && g.questions?.length > 0);
  const memoryGamesFiltered = games.filter(g => g.game_type === 'memory' && g.pairs?.length > 0);
  const kahootGames = games.filter(g => g.game_type === 'kahoot');
  const pendingGames = games.filter(g => !g.completed);

  return (
    <div className="space-y-6">
      {/* Pending Games Banner */}
      {pendingGames.length > 0 && (
        <Card className="bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
          <CardContent className="py-4">
            <p className="text-center text-yellow-800">
              <span className="font-bold">🎮 {pendingGames.length}</span> jeu(x) à compléter!
            </p>
          </CardContent>
        </Card>
      )}

      {/* Surprise Mode Toggle */}
      <div className="flex justify-center">
        <Button
          variant={surpriseMode ? "default" : "outline"}
          onClick={() => setSurpriseMode(!surpriseMode)}
          className={surpriseMode ? "bg-purple-600" : ""}
        >
          <Sparkles className="w-4 h-4 mr-2" />
          Mode Surprise {surpriseMode ? 'ON' : 'OFF'}
        </Button>
      </div>

      {/* Flashcards */}
      {flashcardGames.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-yellow-500" />
              Flashcards
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {flashcardGames.map((game) => (
                <Card key={game.id} className={`border-2 ${game.completed ? 'border-green-200 bg-green-50' : 'border-yellow-200'}`}>
                  <CardContent className="p-4">
                    <h3 className="font-bold">{game.title}</h3>
                    <p className="text-sm text-gray-500 mb-3">{game.flashcards.length} cartes</p>
                    {game.completed ? (
                      <div className="flex items-center gap-2 text-green-600">
                        <Trophy className="w-4 h-4" />
                        <span>Score: {game.score}/{game.total}</span>
                      </div>
                    ) : (
                      <Button size="sm" onClick={() => startFlashcardGame(game)}>
                        Jouer
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quizzes */}
      {quizGames.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HelpCircle className="w-5 h-5 text-purple-500" />
              Quiz
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {quizGames.map((game) => (
                <Card key={game.id} className={`border-2 ${game.completed ? 'border-green-200 bg-green-50' : 'border-purple-200'}`}>
                  <CardContent className="p-4">
                    <h3 className="font-bold">{game.title}</h3>
                    <p className="text-sm text-gray-500 mb-3">
                      {game.questions.length} questions
                      {game.time_limit > 0 && ` • ${game.time_limit}s/question`}
                    </p>
                    {game.completed ? (
                      <div className="flex items-center gap-2 text-green-600">
                        <Trophy className="w-4 h-4" />
                        <span>Score: {game.score}/{game.total}</span>
                      </div>
                    ) : (
                      <Button size="sm" className="bg-purple-600 hover:bg-purple-700" onClick={() => startQuizGame(game)}>
                        Jouer
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Memory Games */}
      {memoryGamesFiltered.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5 text-blue-500" />
              Memory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              {memoryGamesFiltered.map((game) => (
                <Card key={game.id} className={`border-2 ${game.completed ? 'border-green-200 bg-green-50' : 'border-blue-200'}`}>
                  <CardContent className="p-4">
                    <h3 className="font-bold">{game.title}</h3>
                    <p className="text-sm text-gray-500 mb-3">{game.pairs.length} paires</p>
                    {game.completed ? (
                      <div className="flex items-center gap-2 text-green-600">
                        <Trophy className="w-4 h-4" />
                        <span>Complété!</span>
                      </div>
                    ) : (
                      <Button size="sm" className="bg-blue-600 hover:bg-blue-700" onClick={() => startMemoryGame(game)}>
                        Jouer
                      </Button>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Kahoot Links */}
      {kahootGames.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-xl">🎯</span>
              Kahoot
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {kahootGames.map((game) => (
                <div key={game.id} className="flex justify-between items-center p-3 border rounded-lg">
                  <span className="font-medium">{game.title}</span>
                  <Button size="sm" variant="outline" asChild>
                    <a href={game.game_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-4 h-4 mr-1" /> Ouvrir
                    </a>
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* No games */}
      {games.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="text-5xl mb-4">🎮</div>
            <h3 className="text-xl font-semibold mb-2">Pas de jeux pour le moment</h3>
            <p className="text-gray-500">Ton professeur t'assignera bientôt des jeux !</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default StudentGamesAdvanced;
