import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { RadioGroup, RadioGroupItem } from '../components/ui/radio-group';
import { Label } from '../components/ui/label';
import { Progress } from '../components/ui/progress';
import { toast } from 'sonner';
import axios from 'axios';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle, Lock, UserPlus, LogIn, Home, Sparkles } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const GATE_QUESTION = 5; // Block at question 5 (0-indexed = after 5 answers)

// Packs data for display in gate screen
const PACKS = [
  { id: 'kkid', name: 'Pack K-Kid', desc: 'Enfants 3-9 ans', price: '30€', color: 'pink' },
  { id: 'beginner', name: 'Pack K-Débutant', desc: 'Parfait pour commencer', price: '60€', color: 'teal' },
  { id: 'intermediate', name: 'Pack K-Intermédiaire', desc: 'Le plus populaire', price: '90€', color: 'teal', popular: true },
  { id: 'advanced', name: 'Pack K-Avancé', desc: 'Professionnel', price: '120€', color: 'emerald' },
];

const TestPage = () => {
  const { level } = useParams();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState([]);
  const [selectedOption, setSelectedOption] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gated, setGated] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [lastAnswerCorrect, setLastAnswerCorrect] = useState(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [correctOption, setCorrectOption] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isLoggedIn = !!localStorage.getItem('token');

  useEffect(() => {
    fetchTest();
  }, [level]);

  const fetchTest = async () => {
    try {
      const response = await axios.get(`${API}/tests/${level}`);
      setQuestions(response.data.questions);
      setLoading(false);
    } catch (error) {
      toast.error('Erreur lors du chargement du test');
      navigate('/');
    }
  };

  const handleNext = async () => {
    if (selectedOption === null) {
      toast.error('Veuillez selectionner une reponse');
      return;
    }

    // Prevent double submission
    if (isSubmitting) return;
    setIsSubmitting(true);

    try {
      // Check if answer is correct via API
      const response = await axios.post(`${API}/tests/check-answer`, {
        level,
        question_id: questions[currentQuestion].id,
        selected_option: selectedOption
      });

      const { is_correct, correct_option } = response.data;
      setLastAnswerCorrect(is_correct);
      setCorrectOption(correct_option);
      setShowFeedback(true);
      
      if (is_correct) {
        setCorrectCount(prev => prev + 1);
      }

      const newAnswers = [
        ...answers,
        {
          question_id: questions[currentQuestion].id,
          selected_option: selectedOption,
          is_correct: is_correct
        }
      ];
      setAnswers(newAnswers);
    } catch (error) {
      toast.error('Erreur lors de la verification');
      setIsSubmitting(false);
    }
  };

  const handleContinueAfterFeedback = () => {
    setShowFeedback(false);
    setSelectedOption(null);
    setIsSubmitting(false);

    // Gate check: after 5 answers, block if not logged in
    if (answers.length >= GATE_QUESTION && !isLoggedIn) {
      setGated(true);
      return;
    }

    if (currentQuestion < questions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitTest(answers);
    }
  };

  const submitTest = async (finalAnswers) => {
    try {
      const response = await axios.post(`${API}/tests/submit`, {
        level,
        answers: finalAnswers
      });
      setResult(response.data);
      toast.success('Test termine !');
    } catch (error) {
      toast.error('Erreur lors de la soumission du test');
    }
  };

  const handleRestart = () => {
    setCurrentQuestion(0);
    setAnswers([]);
    setSelectedOption(null);
    setResult(null);
    setGated(false);
    setShowFeedback(false);
    setLastAnswerCorrect(null);
    setCorrectCount(0);
    setCorrectOption('');
    setIsSubmitting(false);
  };

  const levelLabel = level === 'beginner' ? 'Debutant' : level === 'intermediate' ? 'Intermediaire' : 'Professionnel';

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-600"></div>
      </div>
    );
  }

  // GATE: User must register or login to continue
  if (gated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 flex items-center justify-center px-4 py-8">
        <Card className="w-full max-w-2xl shadow-2xl border-teal-100" data-testid="test-gate-card">
          <CardHeader className="text-center pb-2">
            <div className="w-16 h-16 bg-teal-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-teal-600" />
            </div>
            <CardTitle className="text-2xl text-gray-900">Continuez votre test</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center">
              <p className="text-gray-600 mb-2">
                Vous avez repondu a <strong className="text-teal-700">{answers.length} questions</strong> sur {questions.length}.
              </p>
              <p className="text-lg font-semibold text-teal-700">
                Score actuel: {correctCount}/{answers.length} bonnes reponses
              </p>
              <p className="text-gray-500 text-sm mt-2">
                Pour voir les questions restantes et votre score final, inscrivez-vous ou connectez-vous.
              </p>
            </div>

            <div className="bg-teal-50 rounded-xl p-4 text-center">
              <p className="text-sm text-teal-700 font-medium">Test {levelLabel}</p>
              <Progress value={(answers.length / questions.length) * 100} className="h-2 mt-2" />
              <p className="text-xs text-teal-600 mt-1">{answers.length}/{questions.length} questions</p>
            </div>

            {/* Packs Section */}
            <div className="border-t pt-4">
              <h3 className="text-center font-semibold text-gray-800 mb-4 flex items-center justify-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                Nos formules d&apos;apprentissage
              </h3>
              <div className="grid grid-cols-2 gap-3">
                {PACKS.map((pack) => (
                  <div 
                    key={pack.id}
                    className={`relative p-3 rounded-xl border-2 transition-all hover:shadow-md cursor-pointer ${
                      pack.popular 
                        ? 'border-teal-400 bg-teal-50' 
                        : pack.color === 'pink' 
                          ? 'border-pink-200 bg-pink-50/50 hover:border-pink-300' 
                          : 'border-gray-200 bg-white hover:border-teal-300'
                    }`}
                    onClick={() => navigate('/?openRegister=true#pricing')}
                  >
                    {pack.popular && (
                      <span className="absolute -top-2 right-2 bg-teal-600 text-white text-xs px-2 py-0.5 rounded-full">
                        Populaire
                      </span>
                    )}
                    <h4 className={`font-bold text-sm ${pack.color === 'pink' ? 'text-pink-700' : 'text-teal-700'}`}>
                      {pack.name}
                    </h4>
                    <p className="text-xs text-gray-500">{pack.desc}</p>
                    <p className={`font-bold mt-1 ${pack.color === 'pink' ? 'text-pink-600' : 'text-teal-600'}`}>
                      {pack.price}<span className="text-xs font-normal text-gray-500">/mois</span>
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <Link to="/?openRegister=true#pricing" className="block">
                <Button
                  className="w-full bg-teal-600 hover:bg-teal-700 text-white py-6 text-base font-semibold"
                  data-testid="gate-register-btn"
                >
                  <UserPlus className="w-5 h-5 mr-2" />
                  S&apos;inscrire gratuitement
                </Button>
              </Link>

              <Link to="/login" className="block">
                <Button
                  variant="outline"
                  className="w-full border-teal-300 text-teal-700 hover:bg-teal-50 py-6 text-base font-semibold"
                  data-testid="gate-login-btn"
                >
                  <LogIn className="w-5 h-5 mr-2" />
                  Se connecter
                </Button>
              </Link>

              <Link to="/" className="block">
                <Button
                  variant="ghost"
                  className="w-full text-gray-500 hover:text-gray-700 py-4"
                  data-testid="gate-home-btn"
                >
                  <Home className="w-4 h-4 mr-2" />
                  Retour au site
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // RESULT: Test completed
  if (result) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 flex items-center justify-center px-4">
        <Card className="w-full max-w-2xl shadow-2xl">
          <CardHeader className="text-center">
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <CardTitle className="text-3xl">Test Termine !</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center">
              <div className="text-6xl font-bold text-teal-600 mb-2">
                {result.percentage}%
              </div>
              <p className="text-xl text-gray-600">
                {result.score} / {result.total} reponses correctes
              </p>
              <p className="text-lg text-gray-500 mt-2">
                Niveau: <span className="font-semibold">{levelLabel}</span>
              </p>
            </div>

            <div className="space-y-3">
              <Button
                onClick={handleRestart}
                className="w-full bg-teal-600 hover:bg-teal-700"
                data-testid="test-restart-button"
              >
                Refaire le test
              </Button>
              <Link to="/" className="block">
                <Button variant="outline" className="w-full" data-testid="test-home-button">
                  Retour a l&apos;accueil
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // QUESTIONS
  const progress = ((currentQuestion + 1) / questions.length) * 100;

  // FEEDBACK SCREEN - Show after answering each question
  if (showFeedback) {
    const currentQ = questions[currentQuestion];
    const selectedOptionText = currentQ.options[selectedOption];

    return (
      <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 py-12 px-4">
        <div className="container mx-auto max-w-3xl">
          <Card className="shadow-2xl overflow-hidden">
            <div className={`p-6 ${lastAnswerCorrect ? 'bg-gradient-to-r from-green-500 to-emerald-500' : 'bg-gradient-to-r from-red-500 to-rose-500'}`}>
              <div className="flex items-center justify-center gap-3 text-white">
                {lastAnswerCorrect ? (
                  <>
                    <CheckCircle className="w-10 h-10" />
                    <span className="text-2xl font-bold">Bonne reponse !</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-10 h-10" />
                    <span className="text-2xl font-bold">Mauvaise reponse</span>
                  </>
                )}
              </div>
            </div>

            <CardContent className="p-6 space-y-6">
              <div className="text-center">
                <p className="text-gray-600 mb-4">Question {currentQuestion + 1} sur {questions.length}</p>
                <h3 className="text-lg font-semibold text-gray-800 mb-4">{currentQ.question}</h3>
              </div>

              {!lastAnswerCorrect && (
                <div className="space-y-3">
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600 font-medium">Votre reponse:</p>
                    <p className="text-red-800">{selectedOptionText}</p>
                  </div>
                  <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-600 font-medium">Bonne reponse:</p>
                    <p className="text-green-800 font-semibold">{correctOption}</p>
                  </div>
                </div>
              )}

              {lastAnswerCorrect && (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center">
                  <p className="text-green-800 font-semibold">{correctOption}</p>
                </div>
              )}

              <div className="bg-gray-50 rounded-lg p-4 text-center">
                <p className="text-sm text-gray-600">Score actuel</p>
                <p className="text-2xl font-bold text-teal-600">{correctCount} / {answers.length}</p>
              </div>

              <Button
                onClick={handleContinueAfterFeedback}
                className="w-full bg-teal-600 hover:bg-teal-700 py-6 text-lg"
                data-testid="test-continue-btn"
              >
                {currentQuestion < questions.length - 1 ? (
                  <>
                    Question suivante <ArrowRight className="ml-2 w-5 h-5" />
                  </>
                ) : (
                  'Voir mes resultats'
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 via-white to-emerald-50 py-12 px-4">
      <div className="container mx-auto max-w-3xl">
        <Link to="/" className="inline-flex items-center text-teal-600 hover:text-teal-700 mb-6">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Quitter le test
        </Link>

        <Card className="shadow-2xl">
          <CardHeader>
            <div className="flex justify-between items-center mb-4">
              <CardTitle className="text-2xl">
                Test {levelLabel}
              </CardTitle>
              <span className="text-sm font-semibold text-gray-600">
                Question {currentQuestion + 1} / {questions.length}
              </span>
            </div>
            <Progress value={progress} className="h-2" />
          </CardHeader>

          <CardContent className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold mb-6">
                {questions[currentQuestion]?.question}
              </h3>

              <RadioGroup value={selectedOption?.toString()} onValueChange={(val) => setSelectedOption(parseInt(val))}>
                <div className="space-y-3">
                  {questions[currentQuestion]?.options.map((option, index) => (
                    <div
                      key={index}
                      className="flex items-center space-x-3 p-4 border rounded-lg hover:bg-teal-50 transition-colors cursor-pointer"
                      onClick={() => setSelectedOption(index)}
                    >
                      <RadioGroupItem value={index.toString()} id={`option-${index}`} />
                      <Label htmlFor={`option-${index}`} className="flex-1 cursor-pointer">
                        {option}
                      </Label>
                    </div>
                  ))}
                </div>
              </RadioGroup>
            </div>

            <div className="flex justify-between">
              <Button
                variant="outline"
                onClick={() => navigate('/')}
                data-testid="test-quit-button"
              >
                Quitter
              </Button>
              <Button
                onClick={handleNext}
                className="bg-teal-600 hover:bg-teal-700"
                data-testid="test-next-button"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Verification...' : 'Valider ma reponse'}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default TestPage;
