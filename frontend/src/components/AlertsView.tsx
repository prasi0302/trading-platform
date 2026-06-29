/** Alerts view - create, view, and delete price alerts. */

import { useEffect, useState } from 'react';
import { useAppState } from '../contexts/AppContext';
import { useSessionId } from '../hooks/useSessionId';
import { createAlert, deleteAlert, getAlerts } from '../services/api';

const ALL_SYMBOLS = ['AAPL', 'NVDA', 'JPM', 'MSFT', 'TSLA', 'AMZN', 'GOOGL', 'META'];

export function AlertsView() {
  const { state, dispatch } = useAppState();
  const sessionId = useSessionId();
  const [symbol, setSymbol] = useState('AAPL');
  const [condition, setCondition] = useState<'above' | 'below'>('above');
  const [threshold, setThreshold] = useState<number | ''>('');

  useEffect(() => {
    getAlerts(sessionId)
      .then((alerts) => dispatch({ type: 'SET_ALERTS', payload: alerts }))
      .catch(() => {});
  }, [sessionId, dispatch]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!threshold) return;

    try {
      const alert = await createAlert({
        session_id: sessionId,
        symbol,
        condition,
        threshold: Number(threshold),
      });
      dispatch({ type: 'ADD_ALERT', payload: alert });
      setThreshold('');
    } catch {
      // Ignore
    }
  };

  const handleDelete = async (alertId: string) => {
    await deleteAlert(alertId);
    dispatch({ type: 'REMOVE_ALERT', payload: alertId });
  };

  const activeAlerts = state.alerts.filter((a) => a.active);

  return (
    <div>
      {/* Create Alert */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div className="card-title">Create Alert</div>
        <form onSubmit={handleCreate} style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
          <select
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            style={{
              padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)',
              fontSize: '0.85rem', background: 'var(--bg-white)',
            }}
          >
            {ALL_SYMBOLS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          <select
            value={condition}
            onChange={(e) => setCondition(e.target.value as 'above' | 'below')}
            style={{
              padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)',
              fontSize: '0.85rem', background: 'var(--bg-white)',
            }}
          >
            <option value="above">Price Above</option>
            <option value="below">Price Below</option>
          </select>
          <input
            type="number"
            step="0.01"
            min={0.01}
            value={threshold}
            onChange={(e) => setThreshold(e.target.value ? Number(e.target.value) : '')}
            placeholder="$0.00"
            required
            style={{
              padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)',
              fontSize: '0.85rem', width: 120,
            }}
          />
          <button
            type="submit"
            style={{
              padding: '10px 20px', borderRadius: 8, border: 'none',
              background: 'var(--accent)', color: 'white', fontWeight: 600,
              fontSize: '0.85rem', cursor: 'pointer',
            }}
          >
            Set Alert
          </button>
        </form>
      </div>

      {/* Active Alerts */}
      <div className="card">
        <div className="card-title">Active Alerts ({activeAlerts.length})</div>
        {activeAlerts.length === 0 ? (
          <div className="empty-state">No active alerts — create one above</div>
        ) : (
          <table className="trades-table">
            <thead>
              <tr>
                <th>Symbol</th>
                <th>Condition</th>
                <th>Threshold</th>
                <th>Current Price</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {activeAlerts.map((alert) => {
                const currentPrice = state.prices[alert.symbol]?.price;
                return (
                  <tr key={alert.id}>
                    <td><strong>{alert.symbol}</strong></td>
                    <td>
                      <span style={{ color: alert.condition === 'above' ? 'var(--green)' : 'var(--red)', fontWeight: 600 }}>
                        {alert.condition === 'above' ? '▲ Above' : '▼ Below'}
                      </span>
                    </td>
                    <td><strong>${alert.threshold.toFixed(2)}</strong></td>
                    <td>{currentPrice ? `$${currentPrice.toFixed(2)}` : '—'}</td>
                    <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {new Date(alert.created_at).toLocaleTimeString('en-US', { hour12: false })}
                    </td>
                    <td>
                      <button
                        onClick={() => handleDelete(alert.id)}
                        style={{
                          padding: '4px 12px', borderRadius: 4,
                          border: '1px solid var(--red)', background: 'var(--red-light)',
                          color: 'var(--red)', fontSize: '0.75rem', fontWeight: 600, cursor: 'pointer',
                        }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
