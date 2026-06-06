/** Shared TypeScript types matching backend Pydantic models. */

export interface Symbol {
  ticker: string;
  name: string;
  sector: string;
  initial_price: number;
  volatility: number;
  drift: number;
}

export interface PriceTick {
  symbol: string;
  price: number;
  bid: number;
  ask: number;
  volume: number;
  timestamp: string;
}

export interface OHLCV {
  symbol: string;
  timeframe: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  timestamp: string;
}

export interface Order {
  id: string;
  session_id: string;
  symbol: string;
  type: 'market' | 'limit' | 'stop_loss';
  side: 'buy' | 'sell';
  quantity: number;
  price: number | null;
  status: 'pending' | 'filled' | 'cancelled';
  filled_price: number | null;
  created_at: string;
  filled_at: string | null;
}

export interface OrderRequest {
  symbol: string;
  type: 'market' | 'limit' | 'stop_loss';
  side: 'buy' | 'sell';
  quantity: number;
  price?: number;
  session_id: string;
}

export interface Portfolio {
  session_id: string;
  cash: number;
  holdings: Position[];
  total_value: number;
}

export interface Position {
  symbol: string;
  quantity: number;
  avg_cost: number;
  current_price: number;
  pnl: number;
}

export interface Alert {
  id: string;
  session_id: string;
  symbol: string;
  condition: 'above' | 'below';
  threshold: number;
  active: boolean;
  created_at: string;
}

export interface AlertRequest {
  session_id: string;
  symbol: string;
  condition: 'above' | 'below';
  threshold: number;
}

export interface MarketStatus {
  is_open: boolean;
  next_open: string | null;
  next_close: string | null;
  current_time_et: string;
}

export interface WebSocketMessage {
  type: 'price' | 'order' | 'alert' | 'subscribed' | 'unsubscribed';
  data: unknown;
}
