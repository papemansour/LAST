import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { toast } from 'sonner';
import apiClient from '../utils/api';
import { Play, Video, RefreshCw, ChevronLeft, ChevronRight, Star, User, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';

// Playlist YouTube prédéfinies pour les K-Kids
const youtubePlaylist = {
  alphabet: {
    title: "🔤 L'Alphabet",
    emoji: "🔤",
    color: "from-blue-400 to-cyan-400",
    borderColor: "border-blue-300",
    bgColor: "from-blue-50 to-cyan-50",
    videos: [
      {
        id: 'yt-abc-1',
        title: 'ABC Song - L\'alphabet en anglais',
        description: 'Apprends les 26 lettres de l\'alphabet avec cette chanson amusante!',
        thumbnail: 'https://img.youtube.com/vi/75p-N9YKqNo/mqdefault.jpg',
        videoId: '75p-N9YKqNo'
      },
      {
        id: 'yt-abc-2',
        title: 'Phonics Song - Les sons des lettres',
        description: 'Découvre comment prononcer chaque lettre',
        thumbnail: 'https://img.youtube.com/vi/BELlZKpi1Zs/mqdefault.jpg',
        videoId: 'BELlZKpi1Zs'
      },
      {
        id: 'yt-abc-3',
        title: 'ABC Animals - L\'alphabet avec les animaux',
        description: 'A comme Alligator, B comme Bear...',
        thumbnail: 'https://img.youtube.com/vi/aEXBa0L_7PE/mqdefault.jpg',
        videoId: 'aEXBa0L_7PE'
      }
    ]
  },
  numbers: {
    title: "🔢 Les Chiffres",
    emoji: "🔢",
    color: "from-green-400 to-emerald-400",
    borderColor: "border-green-300",
    bgColor: "from-green-50 to-emerald-50",
    videos: [
      {
        id: 'yt-num-1',
        title: 'Numbers Song 1-20',
        description: 'Compte de 1 à 20 en anglais avec cette chanson',
        thumbnail: 'https://img.youtube.com/vi/0TgLtF3PMOc/mqdefault.jpg',
        videoId: '0TgLtF3PMOc'
      },
      {
        id: 'yt-num-2',
        title: 'Count to 100',
        description: 'Compte de 1 à 100!',
        thumbnail: 'https://img.youtube.com/vi/SxgCA1qOW20/mqdefault.jpg',
        videoId: 'SxgCA1qOW20'
      },
      {
        id: 'yt-num-3',
        title: 'Numbers and Shapes',
        description: 'Les chiffres et les formes ensemble',
        thumbnail: 'https://img.youtube.com/vi/RBvmO1zSXvg/mqdefault.jpg',
        videoId: 'RBvmO1zSXvg'
      }
    ]
  },
  family: {
    title: "👨‍👩‍👧‍👦 La Famille",
    emoji: "👨‍👩‍👧‍👦",
    color: "from-purple-400 to-pink-400",
    borderColor: "border-purple-300",
    bgColor: "from-purple-50 to-pink-50",
    videos: [
      {
        id: 'yt-fam-1',
        title: 'Family Members Song',
        description: 'Apprends les membres de la famille en anglais',
        thumbnail: 'https://img.youtube.com/vi/FHaObkHEkHQ/mqdefault.jpg',
        videoId: 'FHaObkHEkHQ'
      },
      {
        id: 'yt-fam-2',
        title: 'My Family - Kids Song',
        description: 'Mother, Father, Sister, Brother...',
        thumbnail: 'https://img.youtube.com/vi/d_WgPQgEWqk/mqdefault.jpg',
        videoId: 'd_WgPQgEWqk'
      },
      {
        id: 'yt-fam-3',
        title: 'Finger Family Song',
        description: 'Daddy finger, Mommy finger...',
        thumbnail: 'https://img.youtube.com/vi/F4cMibc7xvg/mqdefault.jpg',
        videoId: 'F4cMibc7xvg'
      }
    ]
  },
  colors: {
    title: "🎨 Les Couleurs",
    emoji: "🎨",
    color: "from-pink-400 to-rose-400",
    borderColor: "border-pink-300",
    bgColor: "from-pink-50 to-rose-50",
    videos: [
      {
        id: 'yt-col-1',
        title: 'Colors Song for Kids',
        description: 'Red, Blue, Yellow, Green... toutes les couleurs!',
        thumbnail: 'https://img.youtube.com/vi/tRNy2i75tCc/mqdefault.jpg',
        videoId: 'tRNy2i75tCc'
      },
      {
        id: 'yt-col-2',
        title: 'Rainbow Colors Song',
        description: 'Les couleurs de l\'arc-en-ciel',
        thumbnail: 'https://img.youtube.com/vi/SLZs8qPgzHQ/mqdefault.jpg',
        videoId: 'SLZs8qPgzHQ'
      },
      {
        id: 'yt-col-3',
        title: 'I See Something Blue',
        description: 'Cherche les couleurs autour de toi',
        thumbnail: 'https://img.youtube.com/vi/jYAWf8Y91hA/mqdefault.jpg',
        videoId: 'jYAWf8Y91hA'
      }
    ]
  },
  animals: {
    title: "🦁 Les Animaux",
    emoji: "🦁",
    color: "from-orange-400 to-amber-400",
    borderColor: "border-orange-300",
    bgColor: "from-orange-50 to-amber-50",
    videos: [
      {
        id: 'yt-ani-1',
        title: 'Old MacDonald Had a Farm',
        description: 'Les animaux de la ferme en anglais',
        thumbnail: 'https://img.youtube.com/vi/5oYKonYBujg/mqdefault.jpg',
        videoId: '5oYKonYBujg'
      },
      {
        id: 'yt-ani-2',
        title: 'Zoo Animals Song',
        description: 'Lion, Elephant, Giraffe... animaux du zoo!',
        thumbnail: 'https://img.youtube.com/vi/OwRmivbNgQk/mqdefault.jpg',
        videoId: 'OwRmivbNgQk'
      },
      {
        id: 'yt-ani-3',
        title: 'Animal Sounds Song',
        description: 'Quels sons font les animaux en anglais?',
        thumbnail: 'https://img.youtube.com/vi/t99ULJjCsaM/mqdefault.jpg',
        videoId: 't99ULJjCsaM'
      }
    ]
  }
};

const KidsVideoPlaylist = () => {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [teacherVideos, setTeacherVideos] = useState([]);
  const [loadingTeacherVideos, setLoadingTeacherVideos] = useState(false);
  const [showVideoDialog, setShowVideoDialog] = useState(false);
  const [currentVideo, setCurrentVideo] = useState(null);
  const [watchedVideos, setWatchedVideos] = useState([]);
  const [favoriteVideos, setFavoriteVideos] = useState([]);

  // Load saved progress
  useEffect(() => {
    const saved = localStorage.getItem('kkid_video_progress');
    if (saved) {
      const data = JSON.parse(saved);
      setWatchedVideos(data.watched || []);
      setFavoriteVideos(data.favorites || []);
    }
    fetchTeacherVideos();
  }, []);

  // Save progress
  useEffect(() => {
    if (watchedVideos.length > 0 || favoriteVideos.length > 0) {
      localStorage.setItem('kkid_video_progress', JSON.stringify({
        watched: watchedVideos,
        favorites: favoriteVideos
      }));
    }
  }, [watchedVideos, favoriteVideos]);

  const fetchTeacherVideos = async () => {
    setLoadingTeacherVideos(true);
    try {
      const res = await apiClient.get('/kkid/videos');
      setTeacherVideos(res.data);
    } catch (error) {
      console.log('Could not fetch teacher videos:', error);
    } finally {
      setLoadingTeacherVideos(false);
    }
  };

  const playVideo = (video, isYoutube = false) => {
    setCurrentVideo({ ...video, isYoutube });
    setShowVideoDialog(true);
    
    // Mark as watched
    if (!watchedVideos.includes(video.id)) {
      setWatchedVideos(prev => [...prev, video.id]);
    }
  };

  const toggleFavorite = (videoId) => {
    if (favoriteVideos.includes(videoId)) {
      setFavoriteVideos(prev => prev.filter(id => id !== videoId));
      toast.info('Retiré des favoris');
    } else {
      setFavoriteVideos(prev => [...prev, videoId]);
      toast.success('Ajouté aux favoris ! ⭐');
    }
  };

  const getYoutubeEmbedUrl = (videoId) => {
    return `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1`;
  };

  // Category selection view
  if (!selectedCategory) {
    return (
      <div className="space-y-6">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-pink-700 mb-2">🎥 Mes Vidéos</h2>
          <p className="text-gray-600">Regarde des vidéos amusantes pour apprendre l'anglais !</p>
        </div>

        {/* Teacher Videos Section */}
        {teacherVideos.length > 0 && (
          <Card className="border-2 border-teal-300 bg-gradient-to-br from-teal-50 to-cyan-50 mb-6">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-teal-700">
                <User className="w-5 h-5" />
                📺 Vidéos de mon professeur
              </CardTitle>
              <CardDescription>Vidéos spécialement envoyées par ton professeur</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {teacherVideos.slice(0, 4).map(video => (
                  <Card 
                    key={video.id} 
                    className="border-teal-200 hover:shadow-lg transition-all cursor-pointer"
                    onClick={() => playVideo(video, video.video_url?.includes('youtube') || video.video_url?.includes('youtu.be'))}
                  >
                    <CardContent className="p-3">
                      <div className="flex items-center gap-3">
                        <div className="w-16 h-12 bg-teal-200 rounded flex items-center justify-center flex-shrink-0">
                          {video.thumbnail_url ? (
                            <img src={video.thumbnail_url} alt={video.title} className="w-full h-full object-cover rounded" />
                          ) : (
                            <Video className="w-6 h-6 text-teal-600" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-sm text-teal-800 truncate">{video.title}</h4>
                          <p className="text-xs text-gray-500">De : {video.teacher_name}</p>
                        </div>
                        <Play className="w-5 h-5 text-teal-600 flex-shrink-0" />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
              {teacherVideos.length > 4 && (
                <Button 
                  variant="link" 
                  className="w-full mt-2 text-teal-600"
                  onClick={() => setSelectedCategory('teacher')}
                >
                  Voir toutes les vidéos du professeur ({teacherVideos.length})
                </Button>
              )}
            </CardContent>
          </Card>
        )}

        {/* YouTube Playlists Categories */}
        <h3 className="font-bold text-lg text-pink-700">🎬 Playlists Éducatives</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {Object.entries(youtubePlaylist).map(([key, data]) => {
            const watchedInCategory = data.videos.filter(v => watchedVideos.includes(v.id)).length;
            const progress = (watchedInCategory / data.videos.length) * 100;
            
            return (
              <Card 
                key={key}
                className={`${data.borderColor} bg-gradient-to-br ${data.bgColor} hover:shadow-xl transition-all cursor-pointer transform hover:scale-105 border-2`}
                onClick={() => setSelectedCategory(key)}
              >
                <CardContent className="p-4 text-center">
                  <div className="text-5xl mb-3">{data.emoji}</div>
                  <h3 className="font-bold text-base">{data.title}</h3>
                  <p className="text-sm text-gray-600 mt-1">{data.videos.length} vidéos</p>
                  
                  {/* Progress bar */}
                  <div className="mt-3">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full bg-gradient-to-r ${data.color} transition-all duration-500`}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{watchedInCategory}/{data.videos.length} vues</p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Refresh button */}
        <div className="text-center mt-4">
          <Button 
            variant="outline" 
            size="sm"
            onClick={fetchTeacherVideos}
            disabled={loadingTeacherVideos}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loadingTeacherVideos ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
        </div>

        {/* Video Player Dialog */}
        <Dialog open={showVideoDialog} onOpenChange={setShowVideoDialog}>
          <DialogContent className="max-w-3xl p-0">
            <DialogHeader className="p-4 pb-0">
              <div className="flex items-center justify-between">
                <DialogTitle className="text-lg">{currentVideo?.title}</DialogTitle>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={() => toggleFavorite(currentVideo?.id)}
                  className={favoriteVideos.includes(currentVideo?.id) ? 'text-amber-500' : 'text-gray-400'}
                >
                  <Star className={`w-5 h-5 ${favoriteVideos.includes(currentVideo?.id) ? 'fill-amber-400' : ''}`} />
                </Button>
              </div>
            </DialogHeader>
            <div className="aspect-video w-full bg-black">
              {currentVideo?.isYoutube ? (
                <iframe
                  src={getYoutubeEmbedUrl(currentVideo.videoId || extractYoutubeId(currentVideo.video_url))}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  title={currentVideo?.title}
                />
              ) : currentVideo?.video_url ? (
                <video 
                  src={currentVideo.video_url} 
                  controls 
                  autoPlay 
                  className="w-full h-full"
                >
                  Your browser does not support the video tag.
                </video>
              ) : (
                <div className="w-full h-full flex items-center justify-center text-white">
                  <p>Vidéo non disponible</p>
                </div>
              )}
            </div>
            {currentVideo?.description && (
              <div className="p-4 pt-2">
                <p className="text-sm text-gray-600">{currentVideo.description}</p>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  // Teacher videos list view
  if (selectedCategory === 'teacher') {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2 mb-4">
          <Button variant="ghost" size="sm" onClick={() => setSelectedCategory(null)}>
            <ChevronLeft className="w-4 h-4 mr-1" />
            Retour
          </Button>
          <h2 className="font-bold text-teal-700">📺 Vidéos de mon professeur</h2>
        </div>

        <div className="grid gap-4">
          {teacherVideos.map(video => (
            <Card 
              key={video.id} 
              className="border-teal-200 hover:shadow-lg transition-all cursor-pointer"
              onClick={() => playVideo(video, video.video_url?.includes('youtube') || video.video_url?.includes('youtu.be'))}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <div className="w-32 h-24 bg-teal-200 rounded flex items-center justify-center flex-shrink-0 relative">
                    {video.thumbnail_url ? (
                      <img src={video.thumbnail_url} alt={video.title} className="w-full h-full object-cover rounded" />
                    ) : (
                      <Video className="w-10 h-10 text-teal-600" />
                    )}
                    {watchedVideos.includes(video.id) && (
                      <div className="absolute top-1 right-1 bg-green-500 text-white text-xs px-1 rounded">✓ Vu</div>
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="font-bold text-teal-800">{video.title}</h4>
                    {video.description && (
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">{video.description}</p>
                    )}
                    <p className="text-xs text-gray-500 mt-2">
                      👨‍🏫 {video.teacher_name} • {new Date(video.created_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <div className="flex flex-col gap-2">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleFavorite(video.id);
                      }}
                    >
                      <Star className={`w-5 h-5 ${favoriteVideos.includes(video.id) ? 'fill-amber-400 text-amber-500' : 'text-gray-400'}`} />
                    </Button>
                    <Button size="sm" className="bg-teal-600 hover:bg-teal-700">
                      <Play className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {teacherVideos.length === 0 && (
          <Card className="border-dashed border-2 border-gray-300">
            <CardContent className="p-8 text-center">
              <Video className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500">Ton professeur n'a pas encore envoyé de vidéos</p>
              <p className="text-sm text-gray-400 mt-1">Les vidéos apparaîtront ici quand ton professeur les enverra</p>
            </CardContent>
          </Card>
        )}

        {/* Video Player Dialog */}
        <Dialog open={showVideoDialog} onOpenChange={setShowVideoDialog}>
          <DialogContent className="max-w-3xl p-0">
            <DialogHeader className="p-4 pb-0">
              <DialogTitle>{currentVideo?.title}</DialogTitle>
            </DialogHeader>
            <div className="aspect-video w-full bg-black">
              {currentVideo?.isYoutube ? (
                <iframe
                  src={getYoutubeEmbedUrl(currentVideo.videoId || extractYoutubeId(currentVideo.video_url))}
                  className="w-full h-full"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  title={currentVideo?.title}
                />
              ) : (
                <video src={currentVideo?.video_url} controls autoPlay className="w-full h-full" />
              )}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  // YouTube playlist view
  const playlist = youtubePlaylist[selectedCategory];
  
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Button variant="ghost" size="sm" onClick={() => setSelectedCategory(null)}>
          <ChevronLeft className="w-4 h-4 mr-1" />
          Retour
        </Button>
        <h2 className="font-bold">{playlist.emoji} {playlist.title}</h2>
      </div>

      <div className="grid gap-4">
        {playlist.videos.map((video, index) => (
          <Card 
            key={video.id} 
            className={`${playlist.borderColor} hover:shadow-lg transition-all cursor-pointer`}
            onClick={() => playVideo(video, true)}
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-4">
                <div className="relative flex-shrink-0">
                  <img 
                    src={video.thumbnail} 
                    alt={video.title}
                    className="w-32 h-24 object-cover rounded"
                  />
                  <div className="absolute inset-0 flex items-center justify-center bg-black/30 rounded">
                    <div className="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center">
                      <Play className="w-6 h-6 text-pink-600 ml-1" />
                    </div>
                  </div>
                  {watchedVideos.includes(video.id) && (
                    <div className="absolute top-1 right-1 bg-green-500 text-white text-xs px-1 rounded">✓ Vu</div>
                  )}
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-gray-800">{video.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{video.description}</p>
                  <p className="text-xs text-gray-400 mt-2">Vidéo {index + 1} / {playlist.videos.length}</p>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleFavorite(video.id);
                  }}
                >
                  <Star className={`w-5 h-5 ${favoriteVideos.includes(video.id) ? 'fill-amber-400 text-amber-500' : 'text-gray-400'}`} />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Video Player Dialog */}
      <Dialog open={showVideoDialog} onOpenChange={setShowVideoDialog}>
        <DialogContent className="max-w-3xl p-0">
          <DialogHeader className="p-4 pb-0">
            <div className="flex items-center justify-between">
              <DialogTitle className="text-lg pr-8">{currentVideo?.title}</DialogTitle>
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => toggleFavorite(currentVideo?.id)}
                className={favoriteVideos.includes(currentVideo?.id) ? 'text-amber-500' : 'text-gray-400'}
              >
                <Star className={`w-5 h-5 ${favoriteVideos.includes(currentVideo?.id) ? 'fill-amber-400' : ''}`} />
              </Button>
            </div>
          </DialogHeader>
          <div className="aspect-video w-full bg-black">
            <iframe
              src={getYoutubeEmbedUrl(currentVideo?.videoId)}
              className="w-full h-full"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              title={currentVideo?.title}
            />
          </div>
          {currentVideo?.description && (
            <div className="p-4 pt-2">
              <p className="text-sm text-gray-600">{currentVideo.description}</p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Helper function to extract YouTube video ID from URL
const extractYoutubeId = (url) => {
  if (!url) return null;
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
};

export default KidsVideoPlaylist;
