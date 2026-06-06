/** WebSocket hook for real-time data streaming. */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { PriceTick, WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  sessionId: string;
  onPrice?: (tick: PriceTick) => void;
  onOrder?: (data: unknown) => void;
  onAlert?: (data: unknown) => void;
}

export function useWebSocket({ sessionId, onPrice, onOrder, onAlert }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const reconnectTimeoutRef = useRef<number>();

  // Use refs for callbacks to avoid reconnection on callback changes
  const onPriceRef = useRef(onPrice);
  const onOrderRef = useRef(onOrder);
  const onAlertRef = useRef(onAlert);
  onPriceRef.current = onPrice;
  onOrderRef.current = onOrder;
  onAlertRef.current = onAlert;

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws?session_id=${sessionId}`;

    function connect() {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          switch (message.type) {
            case 'price':
              onPriceRef.current?.(message.data as PriceTick);
              break;
            case 'order':
              onOrderRef.current?.(message.data);
              break;
            case 'alert':
              onAlertRef.current?.(message.data);
              break;
          }
        } catch {
          // Ignore malformed messages
        }
      };

      ws.onclose = () => {
        setConnected(false);
        reconnectTimeoutRef.current = window.setTimeout(connect, 3000);
      };

      ws.onerror = () => {
        ws.close();
      };
    }

    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      wsRef.current?.close();
    };
  }, [sessionId]);

  const subscribe = useCallback((symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'subscribe', symbols }));
    }
  }, []);

  const unsubscribe = useCallback((symbols: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'unsubscribe', symbols }));
    }
  }, []);

  return { connected, subscribe, unsubscribe };
}
