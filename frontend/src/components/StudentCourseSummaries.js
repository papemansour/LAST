import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { getFileUrl } from '../utils/fileUrl';
import { 
  BookOpen, MessageCircle, Send, ChevronDown, ChevronUp, 
  CheckCircle2, Clock, FileText, Volume2, User, Bell
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';

const StudentCourseSummaries = () => {
  const [summaries, setSummaries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedSummary, setExpandedSummary] = useState(null);
  const [showQuestionsDialog, setShowQuestionsDialog] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState('');
  const [submittingQuestion, setSubmittingQuestion] = useState(false);

  useEffect(() => {
    fetchSummaries();
  }, []);

  const fetchSummaries = async () => {
    try {
      const res = await apiClient.get('/student/my-course-summaries');
      setSummaries(res.data);
    } catch (error) {
      console.error('Error fetching summaries:', error);
    } finally {
      setLoading(false);
    }
  };

  const openQuestionsDialog = async (summary) => {
    setSelectedSummary(summary);
    try {
      const res = await apiClient.get(`/student/my-summary-questions/${summary.id}`);
      setQuestions(res.data);
      setShowQuestionsDialog(true);
    } catch (error) {
      toast.error('Erreur de chargement des questions');
    }
  };

  const handleAskQuestion = async () => {
    if (!newQuestion.trim()) {
      toast.error('Veuillez saisir votre question');
      return;
    }
    
    setSubmittingQuestion(true);
    try {
      await apiClient.post('/student/ask-summary-question', {
        summary_id: selectedSummary.id,
        question: newQuestion
      });
      
      toast.success('Question envoyée au professeur!');
      setNewQuestion('');
      
      // Refresh questions
      const res = await apiClient.get(`/student/my-summary-questions/${selectedSummary.id}`);
      setQuestions(res.data);
    } catch (error) {
      toast.error('Erreur lors de l\'envoi de la question');
    } finally {
      setSubmittingQuestion(false);
    }
  };

  const totalUnreadAnswers = summaries.reduce((acc, s) => acc + (s.unread_answers || 0), 0);

  if (loading) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Chargement...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-teal-800 flex items-center gap-2">
            📚 Résumés de Cours
            {totalUnreadAnswers > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                {totalUnreadAnswers} nouvelle(s) réponse(s)
              </span>
            )}
          </h2>
          <p className="text-gray-600">Révisez les résumés envoyés par vos professeurs</p>
        </div>
      </div>

      {/* Summaries list */}
      <div className="space-y-4">
        {summaries.length === 0 ? (
          <Card className="border-dashed border-2">
            <CardContent className="py-12 text-center">
              <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucun résumé de cours reçu</p>
              <p className="text-sm text-gray-400 mt-2">Les résumés envoyés par vos professeurs apparaîtront ici</p>
            </CardContent>
          </Card>
        ) : (
          summaries.map(summary => (
            <Card 
              key={summary.id} 
              className={`hover:shadow-lg transition-shadow ${
                summary.unread_answers > 0 ? 'border-amber-300 bg-amber-50/50' : ''
              }`}
            >
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg text-teal-800 flex items-center gap-2">
                      <FileText className="w-5 h-5" />
                      {summary.title}
                      {summary.unread_answers > 0 && (
                        <span className="bg-amber-500 text-white text-xs px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Bell className="w-3 h-3" />
                          {summary.unread_answers} réponse(s)
                        </span>
                      )}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      <span className="flex items-center gap-4 flex-wrap">
                        <span className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {summary.teacher_name}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(summary.created_at).toLocaleDateString('fr-FR')}
                        </span>
                      </span>
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => setExpandedSummary(expandedSummary === summary.id ? null : summary.id)}
                    >
                      {expandedSummary === summary.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => openQuestionsDialog(summary)}
                      className={summary.unread_answers > 0 ? 'text-amber-600 border-amber-300 bg-amber-50' : 'text-teal-600 border-teal-300'}
                    >
                      <MessageCircle className="w-4 h-4 mr-1" />
                      Questions
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              {expandedSummary === summary.id && (
                <CardContent>
                  <div className="border rounded-lg p-4 bg-white">
                    <div 
                      className="prose prose-sm max-w-none"
                      dangerouslySetInnerHTML={{ __html: summary.content }}
                    />
                    {summary.comments && (
                      <div className="mt-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                        <p className="text-sm font-medium text-yellow-800">📝 Notes du professeur:</p>
                        <p className="text-sm text-yellow-700 mt-1">{summary.comments}</p>
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-4 flex justify-end">
                    <Button 
                      onClick={() => openQuestionsDialog(summary)}
                      className="bg-teal-600 hover:bg-teal-700"
                    >
                      <MessageCircle className="w-4 h-4 mr-2" />
                      Poser une question
                    </Button>
                  </div>
                </CardContent>
              )}
            </Card>
          ))
        )}
      </div>

      {/* Questions Dialog */}
      <Dialog open={showQuestionsDialog} onOpenChange={setShowQuestionsDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-teal-600" />
              Questions sur: {selectedSummary?.title}
            </DialogTitle>
            <DialogDescription>
              Posez vos questions et consultez les réponses de votre professeur
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {/* Ask new question */}
            <Card className="border-teal-200 bg-teal-50">
              <CardContent className="p-4">
                <h4 className="font-semibold text-teal-800 mb-3">❓ Poser une nouvelle question</h4>
                <Textarea
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  placeholder="Tapez votre question ici... (ex: Je ne comprends pas la différence entre...)"
                  rows={3}
                  className="bg-white"
                />
                <Button 
                  onClick={handleAskQuestion}
                  disabled={submittingQuestion || !newQuestion.trim()}
                  className="mt-3 bg-teal-600 hover:bg-teal-700"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {submittingQuestion ? 'Envoi...' : 'Envoyer la question'}
                </Button>
              </CardContent>
            </Card>

            {/* Questions list */}
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-700">💬 Mes questions ({questions.length})</h4>
              
              {questions.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <MessageCircle className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">Vous n&apos;avez pas encore posé de questions</p>
                  <p className="text-sm text-gray-400">Utilisez le formulaire ci-dessus pour poser une question</p>
                </div>
              ) : (
                questions.map(question => (
                  <Card 
                    key={question.id} 
                    className={question.answer ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}
                  >
                    <CardContent className="p-4">
                      {/* Question */}
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-teal-100 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-sm">👤</span>
                        </div>
                        <div className="flex-1">
                          <p className="font-medium text-gray-800">Votre question</p>
                          <p className="text-sm text-gray-600 mt-1">{question.question}</p>
                          <p className="text-xs text-gray-400 mt-2">
                            {new Date(question.created_at).toLocaleString('fr-FR')}
                          </p>
                        </div>
                        {question.answer ? (
                          <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                        ) : (
                          <div className="flex items-center gap-1 text-amber-600 text-xs">
                            <Clock className="w-4 h-4" />
                            En attente
                          </div>
                        )}
                      </div>
                      
                      {/* Answer */}
                      {question.answer && (
                        <div className="mt-4 ml-11 p-4 bg-white rounded-lg border border-green-200">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <span className="text-sm">👨‍🏫</span>
                            </div>
                            <div className="flex-1">
                              <p className="font-medium text-green-800">Réponse du professeur</p>
                              <p className="text-sm text-gray-700 mt-1">{question.answer}</p>
                              
                              {question.answer_audio_url && (
                                <div className="mt-3 p-3 bg-green-50 rounded-lg">
                                  <p className="text-xs text-green-700 mb-2 flex items-center gap-1">
                                    <Volume2 className="w-3 h-3" />
                                    Message vocal
                                  </p>
                                  <audio controls className="w-full h-10">
                                    <source src={getFileUrl(question.answer_audio_url)} />
                                    Votre navigateur ne supporte pas l&apos;audio.
                                  </audio>
                                </div>
                              )}
                              
                              {question.answered_at && (
                                <p className="text-xs text-gray-400 mt-2">
                                  Répondu le {new Date(question.answered_at).toLocaleString('fr-FR')}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {!question.answer && (
                        <div className="mt-3 ml-11 p-3 bg-amber-50 rounded-lg border border-amber-200">
                          <p className="text-sm text-amber-700 flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            Votre professeur répondra bientôt à cette question
                          </p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StudentCourseSummaries;
