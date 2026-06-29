/** Hook for managing anonymous session ID in localStorage. */

import { useMemo } from 'react';

const SESSION_KEY = 'trading_session_id';

function generateSessionId(): string {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

export function useSessionId(): string {
  return useMemo(() => {
    let sessionId = localStorage.getItem(SESSION_KEY);
    if (!sessionId) {
      sessionId = generateSessionId();
      localStorage.setItem(SESSION_KEY, sessionId);
    }
    return sessionId;
  }, []);
}
