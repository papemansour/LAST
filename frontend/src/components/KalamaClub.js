import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { 
  Users, Trophy, Calendar, MessageCircle, ThumbsUp, Send, 
  Sparkles, Award, Clock, UserPlus, Star, Flame 
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import LeaderboardManager from './LeaderboardManager';
import StudentOfMonthBadge from './StudentOfMonthBadge';

const KalamaClub = ({ userRole }) => {
  const [posts, setPosts] = useState([]);
  const [events, setEvents] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [selectedPost, setSelectedPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [showPostDialog, setShowPostDialog] = useState(false);
  const [showEventDialog, setShowEventDialog] = useState(false);
  
  const [newPost, setNewPost] = useState({
    title: '',
    content: '',
    category: 'discussion',
    media_url: '',
    media_type: ''
  });
  
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    event_date: '',
    duration_minutes: 60,
    max_participants: 20,
    event_link: ''
  });

  useEffect(() => {
    loadPosts();
    loadEvents();
    loadLeaderboard();
  }, []);

  const loadPosts = async () => {
    try {
      const res = await apiClient.get('/club/posts');
      setPosts(res.data);
    } catch (error) {
      console.error('Error loading posts:', error);
    }
  };

  const loadEvents = async () => {
    try {
      const res = await apiClient.get('/club/events');
      setEvents(res.data);
    } catch (error) {
      console.error('Error loading events:', error);
    }
  };

  const loadLeaderboard = async () => {
    try {
      const res = await apiClient.get('/club/leaderboard');
      setLeaderboard(res.data);
    } catch (error) {
      console.error('Error loading leaderboard:', error);
    }
  };

  const handleCreatePost = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/club/posts', newPost);
      toast.success('Post publié !');
      setShowPostDialog(false);
      setNewPost({ title: '', content: '', category: 'discussion' });
      loadPosts();
      loadLeaderboard();
    } catch (error) {
      toast.error('Erreur lors de la publication');
    }
  };

  const handleLikePost = async (postId) => {
    try {
      await apiClient.post(`/club/posts/${postId}/like`);
      loadPosts();
      loadLeaderboard();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const handleViewComments = async (post) => {
    setSelectedPost(post);
    try {
      const res = await apiClient.get(`/club/posts/${post.id}/comments`);
      setComments(res.data);
    } catch (error) {
      console.error('Error loading comments:', error);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    
    try {
      await apiClient.post(`/club/posts/${selectedPost.id}/comments`, { content: newComment });
      setNewComment('');
      handleViewComments(selectedPost);
      loadPosts();
    } catch (error) {
      toast.error('Erreur lors de l\'ajout du commentaire');
    }
  };

  const handleRemoveFromLeaderboard = async (userId) => {
    if (!window.confirm('Retirer ce membre du classement ?')) return;
    
    try {
      await apiClient.delete(`/club/leaderboard/${userId}`);
      toast.success('Membre retiré du classement');
      loadLeaderboard();
    } catch (error) {
      toast.error('Erreur lors du retrait');
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce post ?')) return;
    
    try {
      await apiClient.delete(`/club/posts/${postId}`);
      toast.success('Post supprimé');
      loadPosts();
    } catch (error) {
      toast.error('Erreur lors de la suppression du post');
    }
  };

  const handleDeleteEvent = async (eventId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cet événement ?')) return;
    
    try {
      await apiClient.delete(`/club/events/${eventId}`);
      toast.success('Événement supprimé');
      loadEvents();
    } catch (error) {
      toast.error('Erreur lors de la suppression de l\'événement');
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    try {
      await apiClient.post('/club/events', newEvent);
      toast.success('Événement créé !');
      setShowEventDialog(false);
      setNewEvent({ title: '', description: '', event_date: '', duration_minutes: 60, max_participants: 20, event_link: '' });
      loadEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    }
  };

  const handleJoinEvent = async (eventId) => {
    try {
      await apiClient.post(`/club/events/${eventId}/join`);
      toast.success('Inscription confirmée !');
      loadEvents();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur');
    }
  };

  const getCategoryBadge = (category) => {
    const styles = {
      discussion: 'bg-blue-100 text-blue-700',
      challenge: 'bg-purple-100 text-purple-700',
      event: 'bg-orange-100 text-orange-700',
      resource: 'bg-green-100 text-green-700'
    };
    return styles[category] || styles.discussion;
  };

  const getCategoryIcon = (category) => {
    const icons = {
      discussion: <MessageCircle className="w-4 h-4" />,
      challenge: <Trophy className="w-4 h-4" />,
      event: <Calendar className="w-4 h-4" />,
      resource: <Sparkles className="w-4 h-4" />
    };
    return icons[category] || icons.discussion;
  };

  return (
    <div className="space-y-6">
      {/* Student of the Month Badge - Flottant et visible partout */}
      <div className="flex justify-center">
        <StudentOfMonthBadge />
      </div>

      {/* Header */}
      <div className="bg-gradient-to-r from-teal-600 to-cyan-600 rounded-2xl p-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="w-8 h-8" />
              <h1 className="text-3xl font-bold">KALAMA CLUB</h1>
              <Badge className="bg-yellow-400 text-black">Exclusif</Badge>
            </div>
            <p className="text-teal-100">La communauté des membres actifs • Partagez, apprenez, grandissez ensemble</p>
          </div>
          {(userRole === 'teacher' || userRole === 'admin') && (
            <Dialog open={showPostDialog} onOpenChange={setShowPostDialog}>
              <DialogTrigger asChild>
                <Button className="bg-white text-teal-600 hover:bg-teal-50">
                  <Send className="w-4 h-4 mr-2" />
                  Nouveau Post
                </Button>
              </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Créer un post</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreatePost} className="space-y-4">
                <div>
                  <Label>Titre</Label>
                  <Input
                    value={newPost.title}
                    onChange={(e) => setNewPost({ ...newPost, title: e.target.value })}
                    placeholder="Titre de votre post"
                    required
                  />
                </div>
                <div>
                  <Label>Catégorie</Label>
                  <Select
                    value={newPost.category}
                    onValueChange={(value) => setNewPost({ ...newPost, category: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="discussion">💬 Discussion</SelectItem>
                      <SelectItem value="challenge">🏆 Challenge</SelectItem>
                      <SelectItem value="event">📅 Événement</SelectItem>
                      <SelectItem value="resource">✨ Ressource</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Contenu</Label>
                  <Textarea
                    value={newPost.content}
                    onChange={(e) => setNewPost({ ...newPost, content: e.target.value })}
                    placeholder="Partagez vos idées..."
                    rows={5}
                    required
                  />
                </div>
                <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700">Publier</Button>
              </form>
            </DialogContent>
          </Dialog>
          )}
        </div>
      </div>

      <Tabs defaultValue="feed" className="w-full">
        <TabsList className="grid w-full grid-cols-3 bg-teal-50">
          <TabsTrigger value="feed">🏠 Fil d'actualité</TabsTrigger>
          <TabsTrigger value="events">📅 Événements</TabsTrigger>
          <TabsTrigger value="leaderboard">🏆 Classement</TabsTrigger>
        </TabsList>

        {/* Feed Tab */}
        <TabsContent value="feed" className="space-y-4">
          {posts.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <MessageCircle className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">Aucun post pour le moment. Soyez le premier à partager !</p>
              </CardContent>
            </Card>
          ) : (
            posts.map((post) => (
              <Card key={post.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getCategoryBadge(post.category)}>
                          {getCategoryIcon(post.category)}
                          <span className="ml-1 capitalize">{post.category}</span>
                        </Badge>
                        <Badge variant="outline">{post.author_role === 'teacher' ? '👨‍🏫 Prof' : '👨‍🎓 Étudiant'}</Badge>
                      </div>
                      <CardTitle>{post.title}</CardTitle>
                      <CardDescription>
                        Par {post.author_name} • {new Date(post.created_at).toLocaleDateString('fr-FR')}
                      </CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-700 mb-4">{post.content}</p>
                  <div className="flex items-center gap-4">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleLikePost(post.id)}
                      className="text-gray-600 hover:text-teal-600"
                    >
                      <ThumbsUp className="w-4 h-4 mr-1" />
                      {post.likes}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleViewComments(post)}
                      className="text-gray-600 hover:text-teal-600"
                    >
                      <MessageCircle className="w-4 h-4 mr-1" />
                      {post.comments_count}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Événements à venir</h2>
            {(userRole === 'teacher' || userRole === 'admin') && (
              <Dialog open={showEventDialog} onOpenChange={setShowEventDialog}>
                <DialogTrigger asChild>
                  <Button size="sm" className="bg-teal-600 hover:bg-teal-700">
                    <Calendar className="w-4 h-4 mr-2" />
                    Créer un événement
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Nouvel événement</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateEvent} className="space-y-4">
                    <div>
                      <Label>Titre</Label>
                      <Input
                        value={newEvent.title}
                        onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <Label>Description</Label>
                      <Textarea
                        value={newEvent.description}
                        onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                        rows={3}
                        required
                      />
                    </div>
                    <div>
                      <Label>Date et heure</Label>
                      <Input
                        type="datetime-local"
                        value={newEvent.event_date}
                        onChange={(e) => setNewEvent({ ...newEvent, event_date: e.target.value })}
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Durée (minutes)</Label>
                        <Input
                          type="number"
                          value={newEvent.duration_minutes}
                          onChange={(e) => setNewEvent({ ...newEvent, duration_minutes: parseInt(e.target.value) })}
                          required
                        />
                      </div>
                      <div>
                        <Label>Max participants</Label>
                        <Input
                          type="number"
                          value={newEvent.max_participants}
                          onChange={(e) => setNewEvent({ ...newEvent, max_participants: parseInt(e.target.value) })}
                          required
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Lien de l'événement (Zoom, Meet, etc.)</Label>
                      <Input
                        type="url"
                        value={newEvent.event_link}
                        onChange={(e) => setNewEvent({ ...newEvent, event_link: e.target.value })}
                        placeholder="https://zoom.us/j/123456789"
                      />
                    </div>
                    <Button type="submit" className="w-full bg-teal-600 hover:bg-teal-700">Créer</Button>
                  </form>
                </DialogContent>
              </Dialog>
            )}
          </div>

          {events.map((event) => (
            <Card key={event.id} className="border-l-4 border-orange-500">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-orange-500" />
                  {event.title}
                </CardTitle>
                <CardDescription>
                  {new Date(event.event_date).toLocaleString('fr-FR')} • Durée: {event.duration_minutes}min
                </CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-gray-700 mb-4">{event.description}</p>
                {event.event_link && (
                  <div className="mb-4 p-3 bg-blue-50 border-2 border-blue-200 rounded-lg">
                    <p className="text-sm font-semibold text-blue-700 mb-1">🔗 Lien de l'événement :</p>
                    <a 
                      href={event.event_link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm break-all"
                    >
                      {event.event_link}
                    </a>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <UserPlus className="w-4 h-4" />
                    <span>{event.participants.length}/{event.max_participants} inscrits</span>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      onClick={() => handleJoinEvent(event.id)}
                      className="bg-orange-500 hover:bg-orange-600"
                    >
                      S'inscrire
                    </Button>
                    {user?.role === 'admin' && new Date(event.event_date) < new Date() && (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={async () => {
                          if (window.confirm('Supprimer cet événement passé ?')) {
                            try {
                              await apiClient.delete(`/club/events/${event.id}`);
                              toast.success('Événement supprimé');
                              loadEvents();
                            } catch (error) {
                              toast.error('Erreur lors de la suppression');
                            }
                          }
                        }}
                      >
                        🗑️ Supprimer
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard">
          <Card>
            <CardHeader className="bg-gradient-to-r from-yellow-50 via-orange-50 to-yellow-50">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="w-6 h-6 text-yellow-600 animate-pulse" />
                    🏆 Classement Officiel
                  </CardTitle>
                  <CardDescription>Top 10 des meilleurs membres sélectionnés par l'administration</CardDescription>
                </div>
                {userRole === 'admin' && (
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button className="bg-yellow-600 hover:bg-yellow-700">
                        <UserPlus className="w-4 h-4 mr-2" />
                        Gérer le classement
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>Gestion du Classement</DialogTitle>
                        <CardDescription>Ajoutez ou retirez des membres du top 10</CardDescription>
                      </DialogHeader>
                      <LeaderboardManager 
                        onClose={() => setShowPostDialog(false)}
                        onUpdate={loadLeaderboard}
                      />
                    </DialogContent>
                  </Dialog>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              {leaderboard.length === 0 ? (
                <div className="text-center py-12">
                  <Trophy className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500">Le classement sera bientôt disponible !</p>
                  <p className="text-sm text-gray-400 mt-2">Continuez à participer activement au club</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {/* TOP 3 PODIUM */}
                  {leaderboard.filter(m => m.rank <= 3).map((member, index) => {
                    const getMedal = (rank) => {
                      if (rank === 1) return '🥇';
                      if (rank === 2) return '🥈';
                      if (rank === 3) return '🥉';
                      return null;
                    };
                    
                    // Le 1er est mis en TRÈS grande évidence
                    if (member.rank === 1) {
                      return (
                        <div
                          key={member.id}
                          className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-yellow-100 via-yellow-200 to-amber-200 border-4 border-yellow-500 p-8 shadow-2xl transform hover:scale-[1.03] transition-all"
                        >
                          {/* Effet brillant animé */}
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                          
                          <div className="relative z-10 text-center">
                            <div className="relative inline-block mb-4">
                              <div className="w-32 h-32 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-full flex items-center justify-center shadow-2xl animate-pulse">
                                <span className="text-6xl">🥇</span>
                              </div>
                              <Sparkles className="absolute top-0 right-0 w-8 h-8 text-yellow-600 animate-ping" />
                              <Sparkles className="absolute bottom-0 left-0 w-6 h-6 text-yellow-600 animate-pulse" />
                            </div>
                            
                            <div className="bg-white/80 backdrop-blur rounded-xl p-4 mb-4">
                              <p className="text-3xl font-black text-yellow-800 mb-2">{member.user_name}</p>
                              <p className="text-lg text-yellow-700 font-semibold flex items-center justify-center gap-2">
                                {member.user_role === 'teacher' ? '👨‍🏫 Professeur' : '🎓 Étudiant'}
                                <Star className="w-6 h-6 text-yellow-600 fill-yellow-600 animate-pulse" />
                              </p>
                            </div>
                            
                            <div className="flex items-center justify-center gap-2">
                              <Trophy className="w-6 h-6 text-yellow-700" />
                              <p className="text-xl font-bold text-yellow-900">CHAMPION(NE)</p>
                              <Trophy className="w-6 h-6 text-yellow-700" />
                            </div>
                            
                            {userRole === 'admin' && (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="mt-4 text-red-600 hover:text-red-700 hover:bg-red-50"
                                onClick={() => handleRemoveFromLeaderboard(member.user_id)}
                              >
                                Retirer
                              </Button>
                            )}
                          </div>
                        </div>
                      );
                    }
                    
                    // Les 2ème et 3ème places
                    return (
                      <div
                        key={member.id}
                        className={`flex items-center justify-between p-6 rounded-xl transition-all hover:scale-[1.02] ${
                          member.rank === 2 ? 'bg-gradient-to-r from-gray-100 to-gray-200 border-3 border-gray-400 shadow-lg' :
                          'bg-gradient-to-r from-orange-100 to-orange-200 border-3 border-orange-400 shadow-lg'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          <div className={`relative w-20 h-20 rounded-full flex items-center justify-center font-bold text-2xl ${
                            member.rank === 2 ? 'bg-gradient-to-br from-gray-400 to-gray-600 text-white shadow-xl' :
                            'bg-gradient-to-br from-orange-400 to-orange-600 text-white shadow-xl'
                          }`}>
                            {getMedal(member.rank)}
                            <Sparkles className="absolute -top-1 -right-1 w-6 h-6 text-yellow-400 animate-pulse" />
                          </div>
                          <div>
                            <p className="font-bold text-2xl">{member.user_name}</p>
                            <p className="text-base text-gray-700 flex items-center gap-1">
                              {member.user_role === 'teacher' ? '👨‍🏫 Professeur' : '🎓 Étudiant'}
                              <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                            </p>
                          </div>
                        </div>
                        {userRole === 'admin' && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            onClick={() => handleRemoveFromLeaderboard(member.user_id)}
                          >
                            Retirer
                          </Button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Comments Dialog */}
      <Dialog open={!!selectedPost} onOpenChange={() => setSelectedPost(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedPost?.title}</DialogTitle>
            <CardDescription>Par {selectedPost?.author_name}</CardDescription>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-gray-700">{selectedPost?.content}</p>
            <div className="border-t pt-4">
              <h4 className="font-semibold mb-4">Commentaires ({comments.length})</h4>
              <div className="space-y-3 mb-4 max-h-60 overflow-y-auto">
                {comments.map((comment) => (
                  <div key={comment.id} className="bg-gray-50 p-3 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-semibold text-sm">{comment.author_name}</span>
                      <Badge variant="outline" className="text-xs">
                        {comment.author_role === 'teacher' ? 'Prof' : 'Étudiant'}
                      </Badge>
                    </div>
                    <p className="text-sm text-gray-700">{comment.content}</p>
                  </div>
                ))}
              </div>
              <form onSubmit={handleAddComment} className="flex gap-2">
                <Input
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  placeholder="Ajouter un commentaire..."
                  className="flex-1"
                />
                <Button type="submit" size="sm">
                  <Send className="w-4 h-4" />
                </Button>
              </form>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default KalamaClub;
