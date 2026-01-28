import { useState, useEffect, useCallback, useRef } from 'react';
import { toast } from 'sonner';

/**
 * Custom hook for WebSocket notifications
 * Provides real-time push notifications for Q/R messages
 */
const useNotifications = (userId, onNotification) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastNotification, setLastNotification] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const pingIntervalRef = useRef(null);

  const connect = useCallback(() => {
    if (!userId) return;
    
    // Determine WebSocket URL based on current location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/notifications/${userId}`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        
        // Start ping interval to keep connection alive
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000); // Ping every 30 seconds
      };
      
      ws.onmessage = (event) => {
        if (event.data === 'pong') return; // Ignore ping responses
        
        try {
          const notification = JSON.parse(event.data);
          setLastNotification(notification);
          
          // Show toast notification
          if (notification.type === 'new_question') {
            toast.info(notification.message, {
              description: notification.title,
              duration: 5000,
              action: {
                label: 'Voir',
                onClick: () => onNotification?.(notification)
              }
            });
          } else if (notification.type === 'new_answer') {
            toast.success(notification.message, {
              description: notification.title,
              duration: 5000,
              action: {
                label: 'Voir',
                onClick: () => onNotification?.(notification)
              }
            });
          }
          
          // Call custom callback if provided
          onNotification?.(notification);
        } catch (e) {
          console.error('Error parsing notification:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        clearInterval(pingIntervalRef.current);
        
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };
      
      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      // Retry connection after 5 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 5000);
    }
  }, [userId, onNotification]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(pingIntervalRef.current);
    setIsConnected(false);
  }, []);

  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastNotification,
    reconnect: connect,
    disconnect
  };
};

export default useNotifications;
