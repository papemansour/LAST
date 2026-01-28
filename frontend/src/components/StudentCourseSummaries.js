import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { getFileUrl } from '../utils/fileUrl';
import { 
  BookOpen, MessageCircle, Send, ChevronDown, ChevronUp, 
  CheckCircle2, Clock, FileText, Volume2, User, Bell,
  Mic, MicOff, Square, Trash2, Check
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
  
  // Audio recording
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

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
      
      // Mark unread answers as read
      const unreadAnswers = res.data.filter(q => q.answer && !q.answer_read);
      for (const q of unreadAnswers) {
        try {
          await apiClient.put(`/student/mark-answer-read/${q.id}`);
        } catch (e) {
          console.error('Error marking answer as read:', e);
        }
      }
      
      // Refresh summaries to update unread count
      if (unreadAnswers.length > 0) {
        fetchSummaries();
      }
    } catch (error) {
      toast.error('Erreur de chargement des questions');
    }
  };

  // Audio recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorderRef.current.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorderRef.current.start();
      setIsRecording(true);
      toast.info('Enregistrement en cours...');
    } catch (error) {
      toast.error('Impossible d\'accéder au microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!newQuestion.trim() && !audioBlob) {
      toast.error('Veuillez saisir une question ou enregistrer un message vocal');
      return;
    }
    
    setSubmittingQuestion(true);
    try {
      let audioFileUrl = null;
      
      // Upload audio if exists
      if (audioBlob) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'question.webm');
        const uploadRes = await apiClient.post('/student/upload-question-audio', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        audioFileUrl = uploadRes.data.file_url;
      }
      
      await apiClient.post('/student/ask-summary-question', {
        summary_id: selectedSummary.id,
        question: newQuestion || 'Message vocal',
        question_audio_url: audioFileUrl
      });
      
      toast.success('Question envoyée au professeur!');
      setNewQuestion('');
      setAudioBlob(null);
      setAudioUrl(null);
      
      // Refresh questions
      const res = await apiClient.get(`/student/my-summary-questions/${selectedSummary.id}`);
      setQuestions(res.data);
    } catch (error) {
      console.error('Error sending question:', error);
      toast.error('Erreur lors de l\'envoi de la question');
    } finally {
      setSubmittingQuestion(false);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm('Supprimer cette question ?')) return;
    
    try {
      await apiClient.delete(`/student/delete-question/${questionId}`);
      toast.success('Question supprimée');
      const res = await apiClient.get(`/student/my-summary-questions/${selectedSummary.id}`);
      setQuestions(res.data);
    } catch (error) {
      toast.error('Erreur lors de la suppression');
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
              Posez vos questions par écrit ou message vocal
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
                  placeholder="Tapez votre question ici..."
                  rows={3}
                  className="bg-white"
                />
                
                {/* Voice recording */}
                <div className="mt-3 flex items-center gap-3">
                  <span className="text-sm text-gray-600">Ou message vocal :</span>
                  {!isRecording ? (
                    <Button 
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={startRecording}
                      className="flex items-center gap-2"
                    >
                      <Mic className="w-4 h-4 text-red-600" />
                      Enregistrer
                    </Button>
                  ) : (
                    <Button 
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={stopRecording}
                      className="flex items-center gap-2 bg-red-100 border-red-300 animate-pulse"
                    >
                      <Square className="w-4 h-4 text-red-600" />
                      Arrêter
                    </Button>
                  )}
                  
                  {audioUrl && (
                    <audio controls src={audioUrl} className="h-8 flex-1" />
                  )}
                </div>
                
                <Button 
                  onClick={handleAskQuestion}
                  disabled={submittingQuestion || (!newQuestion.trim() && !audioBlob)}
                  className="mt-3 bg-teal-600 hover:bg-teal-700"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {submittingQuestion ? 'Envoi...' : 'Envoyer'}
                </Button>
              </CardContent>
            </Card>

            {/* Questions list */}
            <div className="space-y-3">
              <h4 className="font-semibold text-gray-700">💬 Mes questions ({questions.length})</h4>
              
              {questions.length === 0 ? (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <MessageCircle className="w-10 h-10 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">Aucune question posée</p>
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
                          {question.question && question.question !== 'Message vocal' && (
                            <p className="text-sm text-gray-600 mt-1">{question.question}</p>
                          )}
                          {question.question_audio_url && (
                            <div className="mt-2 p-2 bg-teal-50 rounded-lg">
                              <p className="text-xs text-teal-700 mb-1 flex items-center gap-1">
                                <Volume2 className="w-3 h-3" />
                                Message vocal
                              </p>
                              <audio controls className="w-full h-8">
                                <source src={getFileUrl(question.question_audio_url)} />
                              </audio>
                            </div>
                          )}
                          <p className="text-xs text-gray-400 mt-2">
                            {new Date(question.created_at).toLocaleString('fr-FR')}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          {question.answer ? (
                            <div className="flex items-center text-blue-600">
                              <Check className="w-4 h-4" />
                              <Check className="w-4 h-4 -ml-2" />
                            </div>
                          ) : (
                            <Clock className="w-4 h-4 text-amber-600" />
                          )}
                          <Button 
                            variant="ghost" 
                            size="sm"
                            onClick={() => handleDeleteQuestion(question.id)}
                            className="text-red-600 hover:bg-red-50"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                      
                      {/* Answer */}
                      {question.answer && (
                        <div className="mt-4 ml-11 p-4 bg-white rounded-lg border border-green-200">
                          <div className="flex items-start gap-3">
                            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center flex-shrink-0">
                              <span className="text-sm">👨‍🏫</span>
                            </div>
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <p className="font-medium text-green-800">Réponse du professeur</p>
                                <div className="flex items-center text-blue-600">
                                  <Check className="w-3 h-3" />
                                  <Check className="w-3 h-3 -ml-1" />
                                </div>
                              </div>
                              {question.answer && (
                                <p className="text-sm text-gray-700 mt-1">{question.answer}</p>
                              )}
                              
                              {question.answer_audio_url && (
                                <div className="mt-3 p-3 bg-green-50 rounded-lg">
                                  <p className="text-xs text-green-700 mb-2 flex items-center gap-1">
                                    <Volume2 className="w-3 h-3" />
                                    Message vocal
                                  </p>
                                  <audio controls className="w-full h-10">
                                    <source src={getFileUrl(question.answer_audio_url)} />
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
                            En attente de réponse du professeur
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
