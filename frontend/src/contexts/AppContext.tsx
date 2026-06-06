/** Global application state using React Context + useReducer. */

import React, { createContext, useContext, useReducer, type Dispatch } from 'react';
import type { Alert, Order, Portfolio, PriceTick } from '../types';

interface AppState {
  prices: Record<string, PriceTick>;
  portfolio: Portfolio | null;
  orders: Order[];
  alerts: Alert[];
  watchlist: string[];
  selectedSymbol: string;
  notifications: string[];
}

type AppAction =
  | { type: 'SET_PRICE'; payload: PriceTick }
  | { type: 'SET_PORTFOLIO'; payload: Portfolio }
  | { type: 'SET_ORDERS'; payload: Order[] }
  | { type: 'ADD_ORDER'; payload: Order }
  | { type: 'SET_ALERTS'; payload: Alert[] }
  | { type: 'ADD_ALERT'; payload: Alert }
  | { type: 'REMOVE_ALERT'; payload: string }
  | { type: 'SET_WATCHLIST'; payload: string[] }
  | { type: 'ADD_TO_WATCHLIST'; payload: string }
  | { type: 'REMOVE_FROM_WATCHLIST'; payload: string }
  | { type: 'SET_SELECTED_SYMBOL'; payload: string }
  | { type: 'ADD_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_NOTIFICATIONS' };

const initialState: AppState = {
  prices: {},
  portfolio: null,
  orders: [],
  alerts: [],
  watchlist: JSON.parse(localStorage.getItem('watchlist') || '["AAPL","MSFT","GOOGL"]'),
  selectedSymbol: 'AAPL',
  notifications: [],
};

function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_PRICE':
      return { ...state, prices: { ...state.prices, [action.payload.symbol]: action.payload } };
    case 'SET_PORTFOLIO':
      return { ...state, portfolio: action.payload };
    case 'SET_ORDERS':
      return { ...state, orders: action.payload };
    case 'ADD_ORDER':
      return { ...state, orders: [action.payload, ...state.orders] };
    case 'SET_ALERTS':
      return { ...state, alerts: action.payload };
    case 'ADD_ALERT':
      return { ...state, alerts: [...state.alerts, action.payload] };
    case 'REMOVE_ALERT':
      return { ...state, alerts: state.alerts.filter((a) => a.id !== action.payload) };
    case 'SET_WATCHLIST': {
      localStorage.setItem('watchlist', JSON.stringify(action.payload));
      return { ...state, watchlist: action.payload };
    }
    case 'ADD_TO_WATCHLIST': {
      const newList = [...new Set([...state.watchlist, action.payload])];
      localStorage.setItem('watchlist', JSON.stringify(newList));
      return { ...state, watchlist: newList };
    }
    case 'REMOVE_FROM_WATCHLIST': {
      const filtered = state.watchlist.filter((s) => s !== action.payload);
      localStorage.setItem('watchlist', JSON.stringify(filtered));
      return { ...state, watchlist: filtered };
    }
    case 'SET_SELECTED_SYMBOL':
      return { ...state, selectedSymbol: action.payload };
    case 'ADD_NOTIFICATION':
      return { ...state, notifications: [...state.notifications, action.payload] };
    case 'CLEAR_NOTIFICATIONS':
      return { ...state, notifications: [] };
    default:
      return state;
  }
}

const AppContext = createContext<{ state: AppState; dispatch: Dispatch<AppAction> } | null>(null);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);
  return <AppContext.Provider value={{ state, dispatch }}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useAppState must be used within AppProvider');
  return context;
}
