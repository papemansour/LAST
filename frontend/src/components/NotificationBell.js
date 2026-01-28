import React, { useState, useEffect, useCallback } from 'react';
import { Bell, MessageCircle, Newspaper, Trophy, BookOpen, X, Sparkles, Wifi, WifiOff } from 'lucide-react';
import { Button } from './ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from './ui/popover';
import { Badge } from './ui/badge';
import { toast } from 'sonner';
import apiClient from '../utils/api';

const NotificationBell = ({ userId }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);

  // WebSocket connection for real-time notifications
  useEffect(() => {
    if (!userId) return;
    
    let ws = null;
    let reconnectTimeout = null;
    let pingInterval = null;
    
    const connect = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      const wsUrl = `${protocol}//${host}/ws/notifications/${userId}`;
      
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log('🔔 Notifications WebSocket connected');
          setWsConnected(true);
          
          // Ping to keep alive
          pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send('ping');
            }
          }, 30000);
        };
        
        ws.onmessage = (event) => {
          if (event.data === 'pong') return;
          
          try {
            const notification = JSON.parse(event.data);
            
            // Show toast for real-time notification
            if (notification.type === 'new_question') {
              toast.info(notification.message, {
                description: notification.title,
                duration: 6000,
              });
            } else if (notification.type === 'new_answer') {
              toast.success(notification.message, {
                description: notification.title,
                duration: 6000,
              });
            }
            
            // Refresh notifications list
            fetchNotifications();
          } catch (e) {
            console.error('Error parsing WebSocket message:', e);
          }
        };
        
        ws.onclose = () => {
          console.log('🔔 Notifications WebSocket disconnected');
          setWsConnected(false);
          clearInterval(pingInterval);
          
          // Reconnect after 5 seconds
          reconnectTimeout = setTimeout(connect, 5000);
        };
        
        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          ws.close();
        };
      } catch (error) {
        console.error('Failed to create WebSocket:', error);
        reconnectTimeout = setTimeout(connect, 5000);
      }
    };
    
    connect();
    
    return () => {
      if (ws) ws.close();
      clearTimeout(reconnectTimeout);
      clearInterval(pingInterval);
    };
  }, [userId]);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await apiClient.get('/notifications/my-notifications');
      setNotifications(res.data || []);
      const unread = (res.data || []).filter(n => !n.is_read).length;
      setUnreadCount(unread);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 60000); // Reduced to 60s since we have WebSocket
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = async (notificationId) => {
    try {
      await apiClient.put(`/notifications/${notificationId}/read`);
      setNotifications(notifications.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(Math.max(0, unreadCount - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    setLoading(true);
    try {
      await apiClient.put('/notifications/mark-all-read');
      // Mettre à jour immédiatement l'état local
      const updatedNotifications = notifications.map(n => ({ ...n, is_read: true }));
      setNotifications(updatedNotifications);
      setUnreadCount(0);
      toast.success('✅ Toutes les notifications sont lues');
      // Fermer le popover et rafraîchir après un court délai
      setTimeout(() => {
        setIsOpen(false);
        fetchNotifications(); // Rafraîchir depuis le serveur
      }, 500);
    } catch (error) {
      toast.error('Erreur lors du marquage');
    } finally {
      setLoading(false);
    }
  };

  const deleteNotification = async (notificationId) => {
    try {
      await apiClient.delete(`/notifications/${notificationId}`);
      const notif = notifications.find(n => n.id === notificationId);
      setNotifications(notifications.filter(n => n.id !== notificationId));
      if (notif && !notif.is_read) {
        setUnreadCount(Math.max(0, unreadCount - 1));
      }
      toast.success('🗑️ Notification supprimée');
    } catch (error) {
      toast.error('Erreur lors de la suppression');
    }
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'message':
        return <MessageCircle className="w-5 h-5 text-blue-600" />;
      case 'news':
        return <Newspaper className="w-5 h-5 text-purple-600" />;
      case 'club':
        return <Trophy className="w-5 h-5 text-yellow-600" />;
      case 'book':
        return <BookOpen className="w-5 h-5 text-teal-600" />;
      default:
        return <Sparkles className="w-5 h-5 text-gray-600" />;
    }
  };

  const getNotificationBgColor = (type) => {
    switch (type) {
      case 'message':
        return 'bg-blue-50 border-l-4 border-blue-400';
      case 'news':
        return 'bg-purple-50 border-l-4 border-purple-400';
      case 'club':
        return 'bg-yellow-50 border-l-4 border-yellow-400';
      case 'book':
        return 'bg-teal-50 border-l-4 border-teal-400';
      default:
        return 'bg-gray-50 border-l-4 border-gray-400';
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInMs = now - date;
    const diffInMinutes = Math.floor(diffInMs / 60000);
    const diffInHours = Math.floor(diffInMs / 3600000);
    const diffInDays = Math.floor(diffInMs / 86400000);

    if (diffInMinutes < 1) return '🔥 À l\'instant';
    if (diffInMinutes < 60) return `Il y a ${diffInMinutes} min`;
    if (diffInHours < 24) return `Il y a ${diffInHours}h`;
    if (diffInDays < 7) return `Il y a ${diffInDays}j`;
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative hover:bg-teal-50 transition-all group"
        >
          <Bell className={`w-6 h-6 text-teal-600 transition-all ${unreadCount > 0 ? 'animate-wiggle' : 'group-hover:scale-110'}`} />
          {unreadCount > 0 ? (
            <span className="absolute -top-1 -right-1 bg-gradient-to-r from-red-500 to-pink-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center animate-pulse shadow-lg">
              {unreadCount > 9 ? '9+' : unreadCount}
            </span>
          ) : (
            <span className="absolute -top-1 -right-1 bg-gray-400 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
              0
            </span>
          )}
          {/* WebSocket status indicator */}
          <span
            className={`absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border border-white ${
              wsConnected ? 'bg-green-500' : 'bg-red-500 animate-pulse'
            }`}
            title={wsConnected ? 'Notifications en temps réel actives' : 'Reconnexion...'}
          />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[420px] p-0 shadow-2xl border-2 border-teal-100" align="end">
        <div className="bg-gradient-to-r from-teal-600 via-teal-500 to-teal-600 p-5 text-white relative overflow-hidden">
          <div className="absolute inset-0 bg-white/10 animate-pulse"></div>
          <div className="relative z-10 flex items-center justify-between">
            <div>
              <h3 className="font-bold text-xl flex items-center gap-2">
                <Bell className="w-5 h-5" />
                Notifications
              </h3>
              <p className="text-sm text-teal-100 mt-1">
                {unreadCount > 0 ? `✨ ${unreadCount} nouvelle(s) notification(s)` : '✅ Tout est à jour !'}
              </p>
            </div>
            {unreadCount > 0 && (
              <Button
                size="sm"
                variant="ghost"
                className="text-white hover:bg-teal-700 transition-all"
                onClick={markAllAsRead}
                disabled={loading}
              >
                ✓ Tout lire
              </Button>
            )}
          </div>
        </div>

        <div className="max-h-[550px] overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="p-12 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-teal-100 to-teal-200 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce">
                <Bell className="w-10 h-10 text-teal-600" />
              </div>
              <p className="text-gray-600 font-semibold">Aucune notification</p>
              <p className="text-sm text-gray-400 mt-2">Vous êtes à jour ! 🎉</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 hover:bg-gray-50 transition-all cursor-pointer group ${
                    !notification.is_read ? 'bg-blue-50/30' : ''
                  }`}
                  onClick={() => !notification.is_read && markAsRead(notification.id)}
                >
                  <div className="flex gap-3">
                    <div className={`p-2.5 rounded-xl ${getNotificationBgColor(notification.type)} flex-shrink-0 h-fit shadow-sm`}>
                      {getNotificationIcon(notification.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <h4 className={`text-sm font-bold ${!notification.is_read ? 'text-teal-900' : 'text-gray-800'}`}>
                          {notification.title}
                        </h4>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteNotification(notification.id);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 transition-all transform hover:scale-110"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                      <p className="text-sm text-gray-600 mt-1.5 line-clamp-2 leading-relaxed">
                        {notification.message}
                      </p>
                      <div className="flex items-center gap-2 mt-2.5">
                        <span className="text-xs text-gray-500 font-medium">
                          {formatTime(notification.created_at)}
                        </span>
                        {!notification.is_read && (
                          <Badge className="bg-gradient-to-r from-teal-500 to-teal-600 text-white text-xs px-2 py-0.5 shadow-sm animate-pulse">
                            ✨ Nouveau
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {notifications.length > 0 && (
          <div className="p-3 border-t bg-gradient-to-r from-gray-50 to-gray-100 text-center">
            <button
              className="text-sm text-teal-600 hover:text-teal-700 font-semibold transition-colors"
              onClick={() => setIsOpen(false)}
            >
              Fermer ✓
            </button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
};

export default NotificationBell;
