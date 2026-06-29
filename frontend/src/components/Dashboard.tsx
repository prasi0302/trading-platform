/** Dashboard page - Portfolio overview, P&L, holdings allocation, account summary. */

import { useEffect, useState } from 'react';
import { useAppState } from '../contexts/AppContext';
import { useSessionId } from '../hooks/useSessionId';
import { getPortfolio, getOrders } from '../services/api';
import type { Portfolio } from '../types';

export function Dashboard() {
  const { state, dispatch } = useAppState();
  const sessionId = useSessionId();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);

  useEffect(() => {
    getPortfolio(sessionId)
      .then((p) => setPortfolio(p))
      .catch(() => {});
    getOrders(sessionId)
      .then((orders) => dispatch({ type: 'SET_ORDERS', payload: orders }))
      .catch(() => {});
  }, [sessionId, dispatch]);

  const totalTrades = state.orders.filter((o) => o.status === 'filled').length;
  const totalAssets = portfolio?.total_value || 100000;
  const startingCash = 100000;
  const pnl = totalAssets - startingCash;

  // Calculate sector allocation from holdings
  const sectorMap: Record<string, string> = {
    AAPL: 'Technology', GOOGL: 'Technology', MSFT: 'Technology',
    NVDA: 'Technology', META: 'Technology', AMZN: 'Consumer',
    TSLA: 'Automotive', JPM: 'Finance',
  };

  const holdingsValue: Record<string, number> = {};
  if (portfolio?.holdings) {
    for (const h of portfolio.holdings) {
      const sector = sectorMap[h.symbol] || 'Other';
      const price = state.prices[h.symbol]?.price || h.avg_cost;
      holdingsValue[sector] = (holdingsValue[sector] || 0) + h.quantity * price;
    }
  }

  const totalHoldingsValue = Object.values(holdingsValue).reduce((a, b) => a + b, 0);
  const sectorColors: Record<string, string> = {
    Technology: '#2563eb', Finance: '#10b981', Consumer: '#f59e0b', Automotive: '#8b5cf6', Other: '#6b7280',
  };

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Good Morning</h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: 4, fontSize: '0.9rem' }}>
            Here's your financial overview
          </p>
        </div>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-label">Total Assets</div>
          <div className="stat-value">${totalAssets.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Portfolio P&L</div>
          <div className="stat-value" style={{ color: pnl >= 0 ? 'var(--green)' : 'var(--red)' }}>
            ${pnl >= 0 ? '+' : ''}{pnl.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Trades Today</div>
          <div className="stat-value">{totalTrades}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Cash Available</div>
          <div className="stat-value">${(portfolio?.cash || startingCash).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}</div>
        </div>
      </div>

      {/* Two column: Allocation + Market Overview */}
      <div className="two-col">
        {/* Portfolio Allocation */}
        <div className="card">
          <div className="card-title">Portfolio Allocation</div>
          {totalHoldingsValue > 0 ? (
            <div>
              {/* Simple bar chart */}
              <div style={{ display: 'flex', height: 12, borderRadius: 6, overflow: 'hidden', marginBottom: 16 }}>
                {Object.entries(holdingsValue).map(([sector, value]) => (
                  <div
                    key={sector}
                    style={{
                      width: `${(value / totalHoldingsValue) * 100}%`,
                      background: sectorColors[sector] || '#6b7280',
                    }}
                  />
                ))}
              </div>
              {/* Legend */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16 }}>
                {Object.entries(holdingsValue).map(([sector, value]) => (
                  <div key={sector} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 10, height: 10, borderRadius: 3, background: sectorColors[sector] || '#6b7280' }} />
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      {sector} {((value / totalHoldingsValue) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="empty-state">No holdings yet — start trading to see allocation</div>
          )}
        </div>

        {/* Market Overview */}
        <div className="card">
          <div className="card-title">Market Overview</div>
          <ul className="market-list">
            {['AAPL', 'JPM', 'AMZN', 'MSFT', 'NVDA'].map((ticker) => {
              const tick = state.prices[ticker];
              const initialPrices: Record<string, number> = {
                AAPL: 175, GOOGL: 140, MSFT: 380, AMZN: 180,
                TSLA: 250, JPM: 190, NVDA: 800, META: 500,
              };
              const initial = initialPrices[ticker] || 100;
              const change = tick ? ((tick.price - initial) / initial) * 100 : 0;
              const isUp = change >= 0;
              return (
                <li key={ticker} className="market-item">
                  <span className="market-item-symbol">{ticker}</span>
                  <div className="market-item-right">
                    <span className="market-item-price">{tick ? `$${tick.price.toFixed(2)}` : '—'}</span>
                    {tick && (
                      <div className={`market-item-change ${isUp ? 'up' : 'down'}`}>
                        {isUp ? '▲' : '▼'} {Math.abs(change).toFixed(2)}%
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="card">
        <div className="card-title">Holdings</div>
        {portfolio?.holdings && portfolio.holdings.length > 0 ? (
          <table className="trades-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Qty</th>
                <th>Avg Cost</th>
                <th>Current</th>
                <th>Value</th>
                <th>P&L</th>
                <th>% Change</th>
              </tr>
            </thead>
            <tbody>
              {portfolio.holdings.map((pos) => {
                const currentPrice = state.prices[pos.symbol]?.price || pos.avg_cost;
                const value = currentPrice * pos.quantity;
                const positionPnl = (currentPrice - pos.avg_cost) * pos.quantity;
                const pctChange = ((currentPrice - pos.avg_cost) / pos.avg_cost) * 100;
                const isUp = positionPnl >= 0;
                return (
                  <tr key={pos.symbol}>
                    <td><strong>{pos.symbol}</strong></td>
                    <td>{pos.quantity}</td>
                    <td>${pos.avg_cost.toFixed(2)}</td>
                    <td>${currentPrice.toFixed(2)}</td>
                    <td><strong>${value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</strong></td>
                    <td style={{ color: isUp ? 'var(--green)' : 'var(--red)' }}>
                      {isUp ? '+' : ''}${positionPnl.toFixed(2)}
                    </td>
                    <td style={{ color: isUp ? 'var(--green)' : 'var(--red)' }}>
                      {isUp ? '+' : ''}{pctChange.toFixed(2)}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="empty-state">No holdings yet — place your first trade on the Trading page</div>
        )}
      </div>
    </div>
  );
}
