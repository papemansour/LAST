import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { getFileUrl } from '../utils/fileUrl';
import { 
  BookOpen, Send, Edit3, Trash2, Users, MessageCircle, 
  ChevronDown, ChevronUp, Bold, Italic, Highlighter, 
  Mic, MicOff, Play, Square, CheckCircle2, Clock,
  FileText, X, Volume2
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

const TeacherCourseSummaries = () => {
  const [summaries, setSummaries] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showQuestionsDialog, setShowQuestionsDialog] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [allUnansweredQuestions, setAllUnansweredQuestions] = useState([]);
  const [expandedSummary, setExpandedSummary] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    comments: '',
    student_ids: []
  });
  
  // Rich text editing
  const contentRef = useRef(null);
  
  // Audio recording
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [answeringQuestion, setAnsweringQuestion] = useState(null);
  const [textAnswer, setTextAnswer] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [summariesRes, questionsRes] = await Promise.all([
        apiClient.get('/teacher/my-course-summaries'),
        apiClient.get('/teacher/all-summary-questions')
      ]);
      
      // Fetch teacher's assigned students
      let studentsList = [];
      try {
        const studentsRes = await apiClient.get('/teacher/my-students');
        studentsList = studentsRes.data || [];
      } catch (err) {
        // Fallback: try to get all users if teacher has permission
        try {
          const usersRes = await apiClient.get('/admin/all-users');
          studentsList = usersRes.data.filter(u => u.role === 'student');
        } catch (e) {
          console.log('Could not fetch students list');
        }
      }
      
      setSummaries(summariesRes.data);
      setStudents(studentsList);
      setAllUnansweredQuestions(questionsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSummary = async () => {
    if (!formData.title.trim() || !formData.content.trim()) {
      toast.error('Veuillez remplir le titre et le contenu');
      return;
    }
    
    if (formData.student_ids.length === 0) {
      toast.error('Veuillez sélectionner au moins un étudiant');
      return;
    }
    
    try {
      await apiClient.post('/teacher/create-course-summary', formData);
      toast.success('Résumé de cours créé et envoyé!');
      setShowCreateDialog(false);
      setFormData({ title: '', content: '', comments: '', student_ids: [] });
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la création');
    }
  };

  const handleDeleteSummary = async (summaryId) => {
    if (!window.confirm('Supprimer ce résumé de cours?')) return;
    
    try {
      await apiClient.delete(`/teacher/delete-course-summary/${summaryId}`);
      toast.success('Résumé supprimé');
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const openQuestionsDialog = async (summary) => {
    setSelectedSummary(summary);
    try {
      const res = await apiClient.get(`/teacher/summary-questions/${summary.id}`);
      setQuestions(res.data);
      setShowQuestionsDialog(true);
    } catch (error) {
      toast.error('Erreur de chargement des questions');
    }
  };

  // Rich text formatting
  const applyFormat = (command, value = null) => {
    document.execCommand(command, false, value);
    if (contentRef.current) {
      setFormData(prev => ({ ...prev, content: contentRef.current.innerHTML }));
    }
  };

  const highlightText = (color) => {
    document.execCommand('hiliteColor', false, color);
    if (contentRef.current) {
      setFormData(prev => ({ ...prev, content: contentRef.current.innerHTML }));
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

  const handleAnswerQuestion = async (questionId) => {
    if (!textAnswer.trim() && !audioBlob) {
      toast.error('Veuillez saisir une réponse ou enregistrer un message vocal');
      return;
    }
    
    try {
      let audioFileUrl = null;
      
      // Upload audio if exists
      if (audioBlob) {
        const formData = new FormData();
        formData.append('file', audioBlob, 'answer.webm');
        const uploadRes = await apiClient.post('/teacher/upload-audio-answer', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        audioFileUrl = uploadRes.data.file_url;
      }
      
      await apiClient.post(`/teacher/answer-summary-question/${questionId}`, {
        answer: textAnswer || null,
        answer_audio_url: audioFileUrl
      });
      
      toast.success('Réponse envoyée!');
      setAnsweringQuestion(null);
      setTextAnswer('');
      setAudioBlob(null);
      setAudioUrl(null);
      
      // Refresh questions
      if (selectedSummary) {
        const res = await apiClient.get(`/teacher/summary-questions/${selectedSummary.id}`);
        setQuestions(res.data);
      }
      fetchData();
    } catch (error) {
      toast.error('Erreur lors de l\'envoi de la réponse');
    }
  };

  const toggleStudent = (studentId) => {
    setFormData(prev => ({
      ...prev,
      student_ids: prev.student_ids.includes(studentId)
        ? prev.student_ids.filter(id => id !== studentId)
        : [...prev.student_ids, studentId]
    }));
  };

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
      {/* Header with stats */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-teal-800">📚 Résumés de Cours</h2>
          <p className="text-gray-600">Créez et partagez des résumés avec vos étudiants</p>
        </div>
        <div className="flex gap-3">
          {allUnansweredQuestions.length > 0 && (
            <div className="bg-red-100 text-red-700 px-3 py-2 rounded-lg flex items-center gap-2">
              <MessageCircle className="w-4 h-4" />
              <span className="font-semibold">{allUnansweredQuestions.length} questions en attente</span>
            </div>
          )}
          <Button onClick={() => setShowCreateDialog(true)} className="bg-teal-600 hover:bg-teal-700">
            <Edit3 className="w-4 h-4 mr-2" />
            Nouveau résumé
          </Button>
        </div>
      </div>

      {/* Unanswered questions alert */}
      {allUnansweredQuestions.length > 0 && (
        <Card className="border-amber-200 bg-amber-50">
          <CardHeader className="pb-2">
            <CardTitle className="text-amber-800 flex items-center gap-2">
              <MessageCircle className="w-5 h-5" />
              Questions en attente de réponse
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {allUnansweredQuestions.slice(0, 3).map(q => (
                <div key={q.id} className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-200">
                  <div>
                    <p className="font-medium text-gray-800">{q.student_name}</p>
                    <p className="text-sm text-gray-600 line-clamp-1">{q.question}</p>
                    <p className="text-xs text-amber-600 mt-1">📖 {q.summary_title}</p>
                  </div>
                  <Button 
                    size="sm" 
                    onClick={() => {
                      const summary = summaries.find(s => s.id === q.summary_id);
                      if (summary) openQuestionsDialog(summary);
                    }}
                    className="bg-amber-600 hover:bg-amber-700"
                  >
                    Répondre
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summaries list */}
      <div className="grid gap-4">
        {summaries.length === 0 ? (
          <Card className="border-dashed border-2">
            <CardContent className="py-12 text-center">
              <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">Aucun résumé de cours créé</p>
              <p className="text-sm text-gray-400 mt-2">Créez votre premier résumé pour vos étudiants</p>
            </CardContent>
          </Card>
        ) : (
          summaries.map(summary => (
            <Card key={summary.id} className="hover:shadow-lg transition-shadow">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg text-teal-800 flex items-center gap-2">
                      <FileText className="w-5 h-5" />
                      {summary.title}
                    </CardTitle>
                    <CardDescription className="mt-1">
                      <span className="flex items-center gap-4 flex-wrap">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3" />
                          {summary.student_names?.length || 0} étudiant(s)
                        </span>
                        <span className="flex items-center gap-1">
                          <MessageCircle className="w-3 h-3" />
                          {summary.question_count || 0} question(s)
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
                    {summary.question_count > 0 && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => openQuestionsDialog(summary)}
                        className="text-amber-600 border-amber-300"
                      >
                        <MessageCircle className="w-4 h-4 mr-1" />
                        Questions
                      </Button>
                    )}
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => handleDeleteSummary(summary.id)}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              
              {expandedSummary === summary.id && (
                <CardContent>
                  <div className="border rounded-lg p-4 bg-gray-50">
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
                  <div className="mt-3 flex flex-wrap gap-2">
                    <span className="text-sm text-gray-500">Envoyé à:</span>
                    {summary.student_names?.map((name, idx) => (
                      <span key={idx} className="px-2 py-1 bg-teal-100 text-teal-700 rounded-full text-xs">
                        {name}
                      </span>
                    ))}
                  </div>
                </CardContent>
              )}
            </Card>
          ))
        )}
      </div>

      {/* Create Summary Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>📝 Créer un résumé de cours</DialogTitle>
            <DialogDescription>
              Rédigez un résumé avec mise en forme et envoyez-le à vos étudiants
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">Titre du résumé *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                placeholder="Ex: Leçon 5 - Les temps du passé"
              />
            </div>
            
            {/* Rich text toolbar */}
            <div>
              <Label>Contenu du résumé *</Label>
              <div className="border rounded-t-lg bg-gray-50 p-2 flex flex-wrap gap-2">
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => applyFormat('bold')}
                  title="Gras"
                >
                  <Bold className="w-4 h-4" />
                </Button>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => applyFormat('italic')}
                  title="Italique"
                >
                  <Italic className="w-4 h-4" />
                </Button>
                <div className="border-l mx-1"></div>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => highlightText('#ffff00')}
                  title="Surligner en jaune"
                  className="bg-yellow-200"
                >
                  <Highlighter className="w-4 h-4" />
                </Button>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => highlightText('#90EE90')}
                  title="Surligner en vert"
                  className="bg-green-200"
                >
                  <Highlighter className="w-4 h-4" />
                </Button>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => highlightText('#FFB6C1')}
                  title="Surligner en rose"
                  className="bg-pink-200"
                >
                  <Highlighter className="w-4 h-4" />
                </Button>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => highlightText('#87CEEB')}
                  title="Surligner en bleu"
                  className="bg-blue-200"
                >
                  <Highlighter className="w-4 h-4" />
                </Button>
                <div className="border-l mx-1"></div>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => applyFormat('foreColor', '#dc2626')}
                  title="Texte rouge"
                  className="text-red-600"
                >
                  A
                </Button>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => applyFormat('foreColor', '#2563eb')}
                  title="Texte bleu"
                  className="text-blue-600"
                >
                  A
                </Button>
                <Button 
                  type="button" 
                  variant="ghost" 
                  size="sm"
                  onClick={() => applyFormat('foreColor', '#16a34a')}
                  title="Texte vert"
                  className="text-green-600"
                >
                  A
                </Button>
              </div>
              <div
                ref={contentRef}
                contentEditable
                className="border border-t-0 rounded-b-lg p-4 min-h-[200px] focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                onInput={(e) => setFormData({ ...formData, content: e.currentTarget.innerHTML })}
                placeholder="Tapez votre résumé ici..."
              />
            </div>
            
            <div>
              <Label htmlFor="comments">Notes/Commentaires (optionnel)</Label>
              <Textarea
                id="comments"
                value={formData.comments}
                onChange={(e) => setFormData({ ...formData, comments: e.target.value })}
                placeholder="Ajoutez des commentaires ou instructions pour les étudiants..."
                rows={3}
              />
            </div>
            
            {/* Student selection */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label>Destinataires * ({formData.student_ids.length} sélectionné(s))</Label>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (formData.student_ids.length === students.length) {
                      setFormData(prev => ({ ...prev, student_ids: [] }));
                    } else {
                      setFormData(prev => ({ ...prev, student_ids: students.map(s => s.id) }));
                    }
                  }}
                >
                  {formData.student_ids.length === students.length ? 'Tout désélectionner' : 'Tout sélectionner'}
                </Button>
              </div>
              
              <div className="border rounded-lg p-3 max-h-[200px] overflow-y-auto">
                {students.length === 0 ? (
                  <p className="text-gray-500 text-sm text-center py-4">Aucun étudiant disponible</p>
                ) : (
                  <div className="space-y-2">
                    {students.map((student) => (
                      <div
                        key={student.id}
                        className={`flex items-center gap-2 p-2 rounded cursor-pointer transition ${
                          formData.student_ids.includes(student.id) 
                            ? 'bg-teal-100 border border-teal-300' 
                            : 'hover:bg-gray-50'
                        }`}
                        onClick={() => toggleStudent(student.id)}
                      >
                        <input
                          type="checkbox"
                          checked={formData.student_ids.includes(student.id)}
                          onChange={() => toggleStudent(student.id)}
                          className="h-4 w-4 text-teal-600 rounded"
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{student.first_name} {student.last_name}</p>
                          <p className="text-xs text-gray-500">{student.email}</p>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          student.level === 'kkid' ? 'bg-pink-100 text-pink-700' :
                          student.level === 'beginner' ? 'bg-green-100 text-green-700' :
                          student.level === 'intermediate' ? 'bg-blue-100 text-blue-700' :
                          'bg-purple-100 text-purple-700'
                        }`}>
                          {student.level === 'kkid' ? 'K-Kid' : student.level}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="flex-1">
                Annuler
              </Button>
              <Button onClick={handleCreateSummary} className="flex-1 bg-teal-600 hover:bg-teal-700">
                <Send className="w-4 h-4 mr-2" />
                Envoyer le résumé
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Questions Dialog */}
      <Dialog open={showQuestionsDialog} onOpenChange={setShowQuestionsDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>💬 Questions sur: {selectedSummary?.title}</DialogTitle>
            <DialogDescription>
              Répondez aux questions de vos étudiants par écrit ou message vocal
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            {questions.length === 0 ? (
              <div className="text-center py-8">
                <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Aucune question pour ce résumé</p>
              </div>
            ) : (
              questions.map(question => (
                <Card key={question.id} className={question.answer ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <p className="font-medium text-gray-800">{question.student_name}</p>
                        <p className="text-sm text-gray-600 mt-1">{question.question}</p>
                        <p className="text-xs text-gray-400 mt-2">
                          {new Date(question.created_at).toLocaleString('fr-FR')}
                        </p>
                      </div>
                      {question.answer ? (
                        <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                      ) : (
                        <Clock className="w-5 h-5 text-amber-600 flex-shrink-0" />
                      )}
                    </div>
                    
                    {question.answer && (
                      <div className="mt-3 p-3 bg-white rounded-lg border">
                        <p className="text-sm font-medium text-green-700">Votre réponse:</p>
                        <p className="text-sm text-gray-700 mt-1">{question.answer}</p>
                        {question.answer_audio_url && (
                          <audio controls className="mt-2 w-full h-10">
                            <source src={getFileUrl(question.answer_audio_url)} />
                          </audio>
                        )}
                      </div>
                    )}
                    
                    {!question.answer && answeringQuestion !== question.id && (
                      <Button 
                        size="sm" 
                        onClick={() => setAnsweringQuestion(question.id)}
                        className="mt-3 bg-amber-600 hover:bg-amber-700"
                      >
                        Répondre
                      </Button>
                    )}
                    
                    {answeringQuestion === question.id && (
                      <div className="mt-4 p-4 bg-white rounded-lg border space-y-3">
                        <div>
                          <Label>Réponse écrite</Label>
                          <Textarea
                            value={textAnswer}
                            onChange={(e) => setTextAnswer(e.target.value)}
                            placeholder="Tapez votre réponse..."
                            rows={3}
                          />
                        </div>
                        
                        <div>
                          <Label>Ou réponse vocale</Label>
                          <div className="flex items-center gap-3 mt-2">
                            {!isRecording ? (
                              <Button 
                                type="button"
                                variant="outline"
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
                                onClick={stopRecording}
                                className="flex items-center gap-2 bg-red-100 border-red-300"
                              >
                                <Square className="w-4 h-4 text-red-600" />
                                Arrêter
                              </Button>
                            )}
                            
                            {audioUrl && (
                              <audio controls src={audioUrl} className="h-10 flex-1" />
                            )}
                          </div>
                        </div>
                        
                        <div className="flex gap-2">
                          <Button 
                            variant="outline" 
                            size="sm"
                            onClick={() => {
                              setAnsweringQuestion(null);
                              setTextAnswer('');
                              setAudioBlob(null);
                              setAudioUrl(null);
                            }}
                          >
                            <X className="w-4 h-4 mr-1" />
                            Annuler
                          </Button>
                          <Button 
                            size="sm"
                            onClick={() => handleAnswerQuestion(question.id)}
                            className="bg-teal-600 hover:bg-teal-700"
                          >
                            <Send className="w-4 h-4 mr-1" />
                            Envoyer la réponse
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TeacherCourseSummaries;
