/** API client functions for backend REST endpoints. */

import type { Alert, AlertRequest, MarketStatus, OHLCV, Order, OrderRequest, Portfolio, Symbol } from '../types';

const API_BASE = '/api';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

// Market Data
export const getSymbols = () => fetchJSON<Symbol[]>(`${API_BASE}/symbols`);

export const getPrice = (symbol: string) =>
  fetchJSON<import('../types').PriceTick>(`${API_BASE}/symbols/${symbol}/price`);

export const getHistory = (symbol: string, timeframe: string, start: string, end: string) =>
  fetchJSON<OHLCV[]>(
    `${API_BASE}/symbols/${symbol}/history?timeframe=${timeframe}&start=${start}&end=${end}`
  );

export const getMarketStatus = () => fetchJSON<MarketStatus>(`${API_BASE}/market/status`);

// Orders
export const submitOrder = (order: OrderRequest) =>
  fetchJSON<Order>(`${API_BASE}/orders`, {
    method: 'POST',
    body: JSON.stringify(order),
  });

export const cancelOrder = (orderId: string, sessionId: string) =>
  fetchJSON<Order>(`${API_BASE}/orders/${orderId}?session_id=${sessionId}`, {
    method: 'DELETE',
  });

export const getOrders = (sessionId: string, status?: string) => {
  const params = new URLSearchParams({ session_id: sessionId });
  if (status) params.set('status', status);
  return fetchJSON<Order[]>(`${API_BASE}/orders?${params}`);
};

// Portfolio
export const getPortfolio = (sessionId: string) =>
  fetchJSON<Portfolio>(`${API_BASE}/portfolio?session_id=${sessionId}`);

export const resetPortfolio = (sessionId: string) =>
  fetchJSON<Portfolio>(`${API_BASE}/portfolio/reset?session_id=${sessionId}`, {
    method: 'POST',
  });

// Alerts
export const createAlert = (alert: AlertRequest) =>
  fetchJSON<Alert>(`${API_BASE}/alerts`, {
    method: 'POST',
    body: JSON.stringify(alert),
  });

export const getAlerts = (sessionId: string) =>
  fetchJSON<Alert[]>(`${API_BASE}/alerts?session_id=${sessionId}`);

export const deleteAlert = (alertId: string) =>
  fetch(`${API_BASE}/alerts/${alertId}`, { method: 'DELETE' });
