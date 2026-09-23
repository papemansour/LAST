import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { 
  CheckCircle, XCircle, Trophy, RotateCcw, Sparkles, 
  ArrowRight, Lightbulb, Target, Star, Loader2 
} from 'lucide-react';
import { toast } from 'sonner';
import apiClient from '../utils/api';

// Kalamai Mascot - Cute green plush with big pink eyes
const KalamaiMascot = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-10 h-10',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
    xxl: 'w-20 h-20'
  };
  
  return (
    <div className={`${sizes[size]} ${className} relative`}>
      <svg viewBox="0 0 100 100" className="w-full h-full">
        <ellipse cx="50" cy="85" rx="35" ry="8" fill="#2d8a5e" opacity="0.3"/>
        <ellipse cx="50" cy="55" rx="38" ry="40" fill="url(#bodyGradientQuiz)"/>
        <ellipse cx="50" cy="55" rx="38" ry="40" fill="url(#fuzzyPatternQuiz)" opacity="0.15"/>
        <ellipse cx="50" cy="62" rx="25" ry="22" fill="#7dd3a8"/>
        <ellipse cx="22" cy="25" rx="12" ry="15" fill="url(#bodyGradientQuiz)" transform="rotate(-15 22 25)"/>
        <ellipse cx="22" cy="25" rx="7" ry="9" fill="#ff9ecd" transform="rotate(-15 22 25)"/>
        <ellipse cx="78" cy="25" rx="12" ry="15" fill="url(#bodyGradientQuiz)" transform="rotate(15 78 25)"/>
        <ellipse cx="78" cy="25" rx="7" ry="9" fill="#ff9ecd" transform="rotate(15 78 25)"/>
        <ellipse cx="35" cy="45" rx="14" ry="16" fill="white"/>
        <ellipse cx="35" cy="45" rx="14" ry="16" fill="none" stroke="#ffb6d9" strokeWidth="2"/>
        <circle cx="37" cy="46" r="9" fill="#ff6eb4"/>
        <circle cx="37" cy="46" r="6" fill="#ff1493"/>
        <circle cx="34" cy="43" r="3" fill="white"/>
        <circle cx="40" cy="49" r="1.5" fill="white" opacity="0.7"/>
        <ellipse cx="65" cy="45" rx="14" ry="16" fill="white"/>
        <ellipse cx="65" cy="45" rx="14" ry="16" fill="none" stroke="#ffb6d9" strokeWidth="2"/>
        <circle cx="67" cy="46" r="9" fill="#ff6eb4"/>
        <circle cx="67" cy="46" r="6" fill="#ff1493"/>
        <circle cx="64" cy="43" r="3" fill="white"/>
        <circle cx="70" cy="49" r="1.5" fill="white" opacity="0.7"/>
        <ellipse cx="20" cy="55" rx="8" ry="5" fill="#ffb6d9" opacity="0.6"/>
        <ellipse cx="80" cy="55" rx="8" ry="5" fill="#ffb6d9" opacity="0.6"/>
        <ellipse cx="50" cy="58" rx="4" ry="3" fill="#3d9970"/>
        <path d="M 40 67 Q 50 75 60 67" fill="none" stroke="#3d9970" strokeWidth="2.5" strokeLinecap="round"/>
        <ellipse cx="15" cy="65" rx="8" ry="12" fill="url(#bodyGradientQuiz)" transform="rotate(-20 15 65)"/>
        <ellipse cx="85" cy="65" rx="8" ry="12" fill="url(#bodyGradientQuiz)" transform="rotate(20 85 65)"/>
        <ellipse cx="35" cy="90" rx="12" ry="7" fill="url(#bodyGradientQuiz)"/>
        <ellipse cx="65" cy="90" rx="12" ry="7" fill="url(#bodyGradientQuiz)"/>
        <defs>
          <linearGradient id="bodyGradientQuiz" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#5dd39e"/>
            <stop offset="50%" stopColor="#3dba7b"/>
            <stop offset="100%" stopColor="#2d9a5e"/>
          </linearGradient>
          <pattern id="fuzzyPatternQuiz" patternUnits="userSpaceOnUse" width="4" height="4">
            <circle cx="2" cy="2" r="0.5" fill="#2d8a5e"/>
          </pattern>
        </defs>
      </svg>
    </div>
  );
};

const QUIZ_CATEGORIES = [
  { id: 'grammar', name: 'Grammaire', icon: '📝', color: 'bg-blue-100 text-blue-700' },
  { id: 'vocabulary', name: 'Vocabulaire', icon: '📚', color: 'bg-green-100 text-green-700' },
  { id: 'conjugation', name: 'Conjugaison', icon: '🔄', color: 'bg-purple-100 text-purple-700' },
  { id: 'comprehension', name: 'Compréhension', icon: '🎧', color: 'bg-orange-100 text-orange-700' },
  { id: 'expressions', name: 'Expressions', icon: '💬', color: 'bg-pink-100 text-pink-700' }
];

const KalamaiQuiz = ({ userLevel = 'intermediate' }) => {
  const [quizState, setQuizState] = useState('menu'); // menu, loading, playing, results
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [score, setScore] = useState(0);
  const [mistakes, setMistakes] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [quizHistory, setQuizHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchQuizHistory();
  }, []);

  const fetchQuizHistory = async () => {
    try {
      const response = await apiClient.get('/kalamai/quiz-history');
      setQuizHistory(response.data || []);
    } catch (error) {
      console.error('Error fetching quiz history:', error);
    }
  };

  const generateQuiz = async (category) => {
    setSelectedCategory(category);
    setLoading(true);
    setQuizState('loading');
    
    try {
      const response = await apiClient.post('/kalamai/generate-quiz', {
        category: category.id,
        level: userLevel,
        previous_mistakes: mistakes.slice(-5) // Send last 5 mistakes for adaptation
      });
      
      if (response.data && response.data.questions) {
        setCurrentQuiz(response.data);
        setCurrentQuestion(0);
        setScore(0);
        setSelectedAnswer(null);
        setShowExplanation(false);
        setQuizState('playing');
      } else {
        throw new Error('Invalid quiz data');
      }
    } catch (error) {
      console.error('Error generating quiz:', error);
      toast.error('Erreur lors de la génération du quiz');
      setQuizState('menu');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (answerIndex) => {
    if (selectedAnswer !== null) return; // Already answered
    
    setSelectedAnswer(answerIndex);
    const question = currentQuiz.questions[currentQuestion];
    const isCorrect = answerIndex === question.correct_answer;
    
    if (isCorrect) {
      setScore(prev => prev + 1);
    } else {
      setMistakes(prev => [...prev, {
        question: question.question,
        category: selectedCategory.id,
        correct_answer: question.options[question.correct_answer],
        user_answer: question.options[answerIndex]
      }]);
    }
    
    setShowExplanation(true);
  };

  const nextQuestion = () => {
    if (currentQuestion < currentQuiz.questions.length - 1) {
      setCurrentQuestion(prev => prev + 1);
      setSelectedAnswer(null);
      setShowExplanation(false);
    } else {
      // Quiz finished - save results
      saveQuizResults();
      setQuizState('results');
    }
  };

  const saveQuizResults = async () => {
    try {
      await apiClient.post('/kalamai/save-quiz-result', {
        category: selectedCategory.id,
        score: score,
        total: currentQuiz.questions.length,
        mistakes: mistakes.slice(-currentQuiz.questions.length),
        level: userLevel
      });
      fetchQuizHistory();
    } catch (error) {
      console.error('Error saving quiz results:', error);
    }
  };

  const restartQuiz = () => {
    setQuizState('menu');
    setCurrentQuiz(null);
    setSelectedCategory(null);
    setSelectedAnswer(null);
    setShowExplanation(false);
  };

  const getScoreMessage = () => {
    const percentage = (score / currentQuiz.questions.length) * 100;
    if (percentage === 100) return { text: 'Parfait ! 🎉', color: 'text-green-600' };
    if (percentage >= 80) return { text: 'Excellent ! 🌟', color: 'text-green-500' };
    if (percentage >= 60) return { text: 'Bien joué ! 👍', color: 'text-blue-500' };
    if (percentage >= 40) return { text: 'Continuez ! 💪', color: 'text-orange-500' };
    return { text: 'À améliorer 📚', color: 'text-red-500' };
  };

  // Menu State
  if (quizState === 'menu') {
    return (
      <Card className="bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200" data-testid="kalamai-quiz">
        <CardHeader>
          <div className="flex items-center gap-3">
            <KalamaiMascot size="lg" className="shadow-lg" />
            <div>
              <CardTitle className="text-teal-700 flex items-center gap-2">
                Quiz Adaptatif Kalamai
                <Sparkles className="h-4 w-4 text-yellow-500" />
              </CardTitle>
              <CardDescription>Testez vos connaissances avec des quiz personnalisés</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-gray-600">
            Choisissez une catégorie pour commencer un quiz adapté à votre niveau ({userLevel}).
          </p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {QUIZ_CATEGORIES.map((cat) => (
              <Button
                key={cat.id}
                variant="outline"
                className="h-auto py-4 flex flex-col items-center gap-2 hover:bg-teal-50 hover:border-teal-300 transition-all"
                onClick={() => generateQuiz(cat)}
                data-testid={`quiz-category-${cat.id}`}
              >
                <span className="text-2xl">{cat.icon}</span>
                <span className="text-sm font-medium">{cat.name}</span>
              </Button>
            ))}
          </div>

          {/* Recent Quiz History */}
          {quizHistory.length > 0 && (
            <div className="mt-6 pt-4 border-t border-teal-100">
              <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Target className="h-4 w-4 text-teal-600" />
                Derniers résultats
              </h4>
              <div className="space-y-2">
                {quizHistory.slice(0, 3).map((result, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-white p-2 rounded-lg border border-teal-50">
                    <div className="flex items-center gap-2">
                      <span>{QUIZ_CATEGORIES.find(c => c.id === result.category)?.icon || '📝'}</span>
                      <span className="text-sm">{QUIZ_CATEGORIES.find(c => c.id === result.category)?.name}</span>
                    </div>
                    <Badge variant={result.score / result.total >= 0.7 ? 'default' : 'secondary'}>
                      {result.score}/{result.total}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Loading State
  if (quizState === 'loading') {
    return (
      <Card className="bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200">
        <CardContent className="py-16 flex flex-col items-center justify-center">
          <KalamaiMascot size="xl" className="animate-bounce mb-4" />
          <p className="text-teal-700 font-medium">Kalamai prépare votre quiz...</p>
          <p className="text-sm text-gray-500 mt-2">Génération de questions personnalisées</p>
        </CardContent>
      </Card>
    );
  }

  // Playing State
  if (quizState === 'playing' && currentQuiz) {
    const question = currentQuiz.questions[currentQuestion];
    const progress = ((currentQuestion + 1) / currentQuiz.questions.length) * 100;

    return (
      <Card className="bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <Badge className={selectedCategory?.color || 'bg-teal-100 text-teal-700'}>
              {selectedCategory?.icon} {selectedCategory?.name}
            </Badge>
            <span className="text-sm text-gray-500">
              Question {currentQuestion + 1}/{currentQuiz.questions.length}
            </span>
          </div>
          <Progress value={progress} className="h-2 mt-2" />
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Question */}
          <div className="bg-white p-4 rounded-lg border border-teal-100">
            <p className="text-lg font-medium text-gray-800">{question.question}</p>
          </div>

          {/* Options */}
          <div className="space-y-2">
            {question.options.map((option, idx) => {
              const isSelected = selectedAnswer === idx;
              const isCorrect = idx === question.correct_answer;
              const showResult = selectedAnswer !== null;
              
              let buttonClass = 'w-full justify-start text-left h-auto py-3 px-4 ';
              if (showResult) {
                if (isCorrect) {
                  buttonClass += 'bg-green-100 border-green-500 text-green-800';
                } else if (isSelected && !isCorrect) {
                  buttonClass += 'bg-red-100 border-red-500 text-red-800';
                } else {
                  buttonClass += 'bg-gray-50 border-gray-200 text-gray-500';
                }
              } else {
                buttonClass += 'hover:bg-teal-50 hover:border-teal-300';
              }

              return (
                <Button
                  key={idx}
                  variant="outline"
                  className={buttonClass}
                  onClick={() => handleAnswerSelect(idx)}
                  disabled={selectedAnswer !== null}
                  data-testid={`quiz-option-${idx}`}
                >
                  <span className="flex items-center gap-3 w-full">
                    <span className="w-6 h-6 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-sm font-bold">
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span className="flex-1">{option}</span>
                    {showResult && isCorrect && <CheckCircle className="h-5 w-5 text-green-600" />}
                    {showResult && isSelected && !isCorrect && <XCircle className="h-5 w-5 text-red-600" />}
                  </span>
                </Button>
              );
            })}
          </div>

          {/* Explanation */}
          {showExplanation && question.explanation && (
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-start gap-2">
                <Lightbulb className="h-5 w-5 text-blue-500 mt-0.5" />
                <div>
                  <p className="font-medium text-blue-800">Explication :</p>
                  <p className="text-sm text-blue-700 mt-1">{question.explanation}</p>
                </div>
              </div>
            </div>
          )}

          {/* Next Button */}
          {selectedAnswer !== null && (
            <Button 
              className="w-full bg-teal-600 hover:bg-teal-700"
              onClick={nextQuestion}
              data-testid="quiz-next"
            >
              {currentQuestion < currentQuiz.questions.length - 1 ? (
                <>Question suivante <ArrowRight className="h-4 w-4 ml-2" /></>
              ) : (
                <>Voir les résultats <Trophy className="h-4 w-4 ml-2" /></>
              )}
            </Button>
          )}
        </CardContent>
      </Card>
    );
  }

  // Results State
  if (quizState === 'results' && currentQuiz) {
    const scoreMessage = getScoreMessage();
    const percentage = Math.round((score / currentQuiz.questions.length) * 100);

    return (
      <Card className="bg-gradient-to-br from-teal-50 to-emerald-50 border-teal-200">
        <CardContent className="py-8 text-center space-y-6">
          <KalamaiMascot size="xxl" className="mx-auto shadow-lg" />
          
          <div>
            <h3 className={`text-2xl font-bold ${scoreMessage.color}`}>{scoreMessage.text}</h3>
            <p className="text-gray-600 mt-2">Quiz {selectedCategory?.name} terminé !</p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-teal-100">
            <div className="text-5xl font-bold text-teal-600">{score}/{currentQuiz.questions.length}</div>
            <Progress value={percentage} className="h-3 mt-4" />
            <p className="text-sm text-gray-500 mt-2">{percentage}% de bonnes réponses</p>
          </div>

          {/* Stars */}
          <div className="flex justify-center gap-2">
            {[...Array(5)].map((_, i) => (
              <Star 
                key={i} 
                className={`h-8 w-8 ${i < Math.ceil(percentage / 20) ? 'text-yellow-400 fill-yellow-400' : 'text-gray-300'}`}
              />
            ))}
          </div>

          {/* Mistakes summary */}
          {mistakes.length > 0 && (
            <div className="bg-orange-50 p-4 rounded-lg border border-orange-200 text-left">
              <p className="font-medium text-orange-800 mb-2">Points à revoir :</p>
              <ul className="text-sm text-orange-700 space-y-1">
                {mistakes.slice(-3).map((m, i) => (
                  <li key={i}>• {m.question.substring(0, 50)}...</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button 
              variant="outline" 
              className="flex-1 border-teal-300 text-teal-600 hover:bg-teal-50"
              onClick={restartQuiz}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Autre quiz
            </Button>
            <Button 
              className="flex-1 bg-teal-600 hover:bg-teal-700"
              onClick={() => generateQuiz(selectedCategory)}
            >
              <Brain className="h-4 w-4 mr-2" />
              Rejouer
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return null;
};

export default KalamaiQuiz;
